"""Translation service for orchestrating translation and storage operations."""

from uuid import UUID

from birkenbihl.models import dateutils
from birkenbihl.models.languages import Language
from birkenbihl.models.requests import SentenceUpdateRequest, TranslationRequest
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.protocols import IStorageProvider, ITranslationProvider
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.storage.exceptions import NotFoundError


class TranslationService:
    """Service orchestrating translation and storage operations.

    Coordinates between TranslationProvider (AI translation) and
    StorageProvider (persistence) to provide high-level translation workflows.

    Follows SOLID principles with dependency injection via protocols.
    """

    def __init__(self, translator: ITranslationProvider | None, storage: IStorageProvider):
        """Initialize service with providers.

        Args:
            translator: Provider for AI-based translations (optional, only needed for translate_and_save)
            storage: Provider for persistence operations
        """
        self._translator = translator
        self._storage = storage

    def translate(self, request: TranslationRequest) -> Translation:
        """Translate text using Birkenbihl method (returns unsaved Translation).

        Args:
            request: Translation request with text, languages, and title

        Returns:
            Translation object with natural and word-by-word translations (unsaved)

        Raises:
            TranslationError: If translation fails
            ValueError: If translator not configured
        """
        if not self._translator:
            raise ValueError("Translator required for translate operation")

        return self._translator.translate(
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

    def update_translation(self, translation: Translation) -> Translation:
        """Update existing translation.

        Args:
            translation: Translation with updated data

        Returns:
            Updated translation

        Raises:
            NotFoundError: If translation doesn't exist
        """
        return self._storage.update(translation)

    def auto_detect_and_translate(self, text: str, target_lang: Language, title: str) -> Translation:
        """Auto-detect source language and translate (returns unsaved Translation).

        Args:
            text: Text to translate
            target_lang: Target language
            title: Document title

        Returns:
            Translation object (unsaved)

        Raises:
            TranslationError: If detection or translation fails
            ValueError: If translator not configured
        """
        if not self._translator:
            raise ValueError("Translator required for auto_detect_and_translate operation")

        source_lang = self._translator.detect_language(text)
        request = TranslationRequest(
            text=text, source_lang=source_lang, target_lang=target_lang, title=title
        )
        return self.translate(request)

    def get_sentence_suggestions(
        self,
        translation_id: UUID,
        sentence_uuid: UUID,
        provider: ProviderConfig,
        count: int = 3,
    ) -> list[str]:
        """Get alternative natural translation suggestions for a sentence.

        Args:
            translation_id: UUID of the translation containing the sentence
            sentence_uuid: UUID of the sentence to generate suggestions for
            provider: Provider configuration to use for generation
            count: Number of suggestions to generate

        Returns:
            List of alternative natural translations

        Raises:
            NotFoundError: If translation or sentence not found
            Exception: If suggestion generation fails
        """
        translation = self._storage.get(translation_id)
        if not translation:
            raise NotFoundError(f"Translation {translation_id} not found")

        sentence = next((s for s in translation.sentences if s.uuid == sentence_uuid), None)
        if not sentence:
            raise NotFoundError(f"Sentence {sentence_uuid} not found in translation {translation_id}")

        translator = PydanticAITranslator(provider)
        alternatives = translator.generate_alternatives(
            sentence.source_text, translation.source_language, translation.target_language, count
        )

        return alternatives

    def update_sentence_natural(self, request: SentenceUpdateRequest) -> Translation:
        """Update natural translation of a sentence and regenerate word-by-word.

        Workflow:
        1. Load translation and find sentence by UUID
        2. Update sentence.natural_translation with new_natural
        3. Call provider.regenerate_alignment() to create new word-by-word
        4. Update sentence.word_alignments with new alignment
        5. Update translation.updated_at timestamp
        6. Save translation via storage

        Args:
            request: Update request with translation_id, sentence_idx, new_text, provider

        Returns:
            Updated Translation object

        Raises:
            NotFoundError: If translation or sentence not found
            Exception: If alignment regeneration fails
        """
        translation = self._storage.get(request.translation_id)
        if not translation:
            raise NotFoundError(f"Translation {request.translation_id} not found")

        if request.sentence_idx < 0 or request.sentence_idx >= len(translation.sentences):
            raise NotFoundError(
                f"Sentence index {request.sentence_idx} out of range for translation {request.translation_id}"
            )

        sentence = translation.sentences[request.sentence_idx]

        translator = PydanticAITranslator(request.provider)
        new_alignments = translator.regenerate_alignment(
            sentence.source_text, request.new_text, translation.source_language, translation.target_language
        )

        sentence.natural_translation = request.new_text
        sentence.word_alignments = new_alignments
        translation.updated_at = dateutils.create_now()

        return self._storage.update(translation)

    def update_sentence_alignment(
        self,
        translation_id: UUID,
        sentence_uuid: UUID,
        alignments: list[WordAlignment],
    ) -> Translation:
        """Update word-by-word alignment of a sentence manually.

        Workflow:
        1. Load translation and find sentence by UUID
        2. Validate alignments using validation.validate_alignment_complete()
        3. If valid: Update sentence.word_alignments
        4. Update translation.updated_at timestamp
        5. Save translation via storage

        Args:
            translation_id: UUID of the translation
            sentence_uuid: UUID of the sentence to update
            alignments: New word-by-word alignments

        Returns:
            Updated Translation object

        Raises:
            NotFoundError: If translation or sentence not found
            ValueError: If alignment validation fails
        """
        translation = self._storage.get(translation_id)
        if not translation:
            raise NotFoundError(f"Translation {translation_id} not found")

        sentence = next((s for s in translation.sentences if s.uuid == sentence_uuid), None)
        if not sentence:
            raise NotFoundError(f"Sentence {sentence_uuid} not found in translation {translation_id}")

        is_valid, error_message = validate_alignment_complete(sentence.natural_translation, alignments)
        if not is_valid:
            raise ValueError(f"Invalid alignment: {error_message}")

        sentence.word_alignments = alignments
        translation.updated_at = dateutils.create_now()

        return self._storage.update(translation)
