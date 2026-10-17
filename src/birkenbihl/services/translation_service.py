"""Translation service for orchestrating translation and storage operations."""

from collections.abc import Callable
from uuid import UUID

from birkenbihl.models import dateutils
from birkenbihl.models.requests import AlignmentRequest, AlignmentUpdateRequest, AutoDetectRequest, TranslationRequest
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.protocols import IStorageProvider, ITranslationProvider
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.language_service import detect_language
from birkenbihl.storage.exceptions import NotFoundError

TranslatorFactory = Callable[[ProviderConfig], ITranslationProvider]


class TranslationService:
    """Service orchestrating translation and storage operations.

    Coordinates between TranslationProvider (AI translation) and
    StorageProvider (persistence) to provide high-level translation workflows.
    All AI calls of the application go through this service; views never build translators themselves.

    Follows SOLID principles with dependency injection via protocols.
    """

    def __init__(
        self,
        translator: ITranslationProvider | None,
        storage: IStorageProvider,
        translator_factory: TranslatorFactory = PydanticAITranslator,
    ):
        """Initialize service with providers.

        Args:
            translator: Default translator, used when a request names no provider (optional)
            storage: Provider for persistence operations
            translator_factory: Builds a translator for a provider chosen per request
        """
        self._translator = translator
        self._storage = storage
        self._translator_factory = translator_factory

    def translate(self, request: TranslationRequest) -> Translation:
        """Translate text using Birkenbihl method (returns unsaved Translation).

        Args:
            request: Translation request with text, languages, title and optionally the provider to use

        Returns:
            Translation object with natural and word-by-word translations (unsaved);
            sentences with uncertain or incomplete alignments are flagged (Sentence.needs_review())

        Raises:
            ValueError: If no provider is given and no default translator is configured
            ProviderError: If provider configuration fails
        """
        return self._translator_for(request.provider).translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            title=request.title,
        )

    def save_translation(self, translation: Translation) -> Translation:
        """Save new translation or update existing one.

        Automatically decides whether to create new or update existing
        translation based on whether it exists in storage.

        Args:
            translation: Translation object to save

        Returns:
            Saved/updated Translation

        Raises:
            StorageError: If save/update fails
        """
        existing = self._storage.get(translation.uuid)

        if existing is None:
            return self._storage.save(translation)
        else:
            return self._storage.update(translation)

    def get_translation(self, translation_id: UUID) -> Translation | None:
        """Retrieve translation by ID.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation if found, None otherwise
        """
        return self._storage.get(translation_id)

    def list_all_translations(self) -> list[Translation]:
        """List all stored translations.

        Returns:
            List of all translations, ordered by newest first
        """
        return self._storage.list_all()

    def delete_translation(self, translation_id: UUID) -> bool:
        """Delete translation by ID.

        Args:
            translation_id: UUID of the translation to delete

        Returns:
            True if deleted, False if not found
        """
        return self._storage.delete(translation_id)

    def auto_detect_and_translate(self, request: AutoDetectRequest) -> Translation:
        """Auto-detect source language and translate (returns unsaved Translation).

        Args:
            request: Auto-detect translation request

        Returns:
            Translation object (unsaved)

        Raises:
            ValueError: If translator not configured
            ProviderError: If provider configuration fails
        """
        source_lang = detect_language(request.text)
        trans_request = TranslationRequest(
            text=request.text, source_lang=source_lang, target_lang=request.target_lang, title=request.title
        )
        return self.translate(trans_request)

    def generate_alignment(self, request: AlignmentRequest) -> list[WordAlignment]:
        """Let the AI propose a word-by-word alignment for a sentence (nothing is saved).

        Used by the editor after the user changed the natural translation; the result is a preview the
        user can still edit, save or cancel.

        Returns:
            Alignments referencing token positions of the request's texts; problems are FLAGGED

        Raises:
            ProviderError: If provider configuration fails
        """
        return self._translator_factory(request.provider).regenerate_alignment(
            request.source_text, request.natural_translation, request.source_lang, request.target_lang
        )

    def update_sentence_alignment(self, request: AlignmentUpdateRequest) -> Translation:
        """Update word-by-word alignment of a sentence manually.

        Args:
            request: Alignment update request

        Returns:
            Updated Translation object

        Raises:
            NotFoundError: If translation or sentence not found
            ValueError: If alignment validation fails
        """
        translation, sentence = self._find_translation_and_sentence(request.translation_id, request.sentence_uuid)

        self._validate_alignments(sentence, request.alignments)

        sentence.word_alignments = request.alignments
        translation.updated_at = dateutils.create_now()

        return self._storage.update(translation)

    def _find_translation_by_id(self, translation_id: UUID) -> Translation:
        """Find translation by ID or raise error.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation object

        Raises:
            NotFoundError: If translation not found
        """
        translation = self._storage.get(translation_id)
        if not translation:
            raise NotFoundError(f"Translation {translation_id} not found")
        return translation

    def _find_translation_and_sentence(self, translation_id: UUID, sentence_uuid: UUID) -> tuple[Translation, Sentence]:
        """Find translation and sentence by UUIDs or raise error.

        Args:
            translation_id: UUID of the translation
            sentence_uuid: UUID of the sentence

        Returns:
            Tuple of (Translation, Sentence)

        Raises:
            NotFoundError: If translation or sentence not found
        """
        translation = self._find_translation_by_id(translation_id)

        sentence = next((s for s in translation.sentences if s.uuid == sentence_uuid), None)
        if not sentence:
            raise NotFoundError(f"Sentence {sentence_uuid} not found in translation {translation_id}")

        return translation, sentence

    def _translator_for(self, provider: ProviderConfig | None) -> ITranslationProvider:
        if provider is not None:
            return self._translator_factory(provider)
        if self._translator is None:
            raise ValueError("No provider given and no default translator configured")
        return self._translator

    def _validate_alignments(self, sentence: Sentence, alignments: list[WordAlignment]) -> None:
        """Validate word alignments for completeness.

        Args:
            sentence: Sentence object
            alignments: Word alignments to validate

        Raises:
            ValueError: If alignment validation fails
        """
        candidate = sentence.model_copy(update={"word_alignments": alignments})
        is_valid, error_message = validate_alignment_complete(candidate)
        if not is_valid:
            raise ValueError(f"Invalid alignment: {error_message}")
