"""Translation service for orchestrating translation and storage operations."""

from uuid import UUID

from birkenbihl.models import dateutils
from birkenbihl.models.languages import Language
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

    def translate_and_save(self, text: str, source_lang: Language, target_lang: Language, title: str) -> Translation:
        """Translate text using Birkenbihl method and save to storage.

        Args:
            text: Text to translate (can contain multiple sentences)
            source_lang_code: Source language object
            target_lang_code: Target language object
            title: Document title

        Returns:
            Saved Translation with natural and word-by-word translations

        Raises:
            TranslationError: If translation fails
            StorageError: If save fails
            ValueError: If translator not configured
        """
        if not self._translator:
            raise ValueError("Translator required for translate_and_save operation")

        # Get translation from AI provider
        translation = self._translator.translate(
            text=text, source_lang=source_lang, target_lang=target_lang, title=title
        )

        # Persist to storage
        return self._storage.save(translation)

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
        """Auto-detect source language and translate.

        Args:
            text: Text to translate
            target_lang_code: Target language
            title: Document title

        Returns:
            Saved Translation

        Raises:
            TranslationError: If detection or translation fails
            ValueError: If translator not configured
        """
        if not self._translator:
            raise ValueError("Translator required for auto_detect_and_translate operation")

        source_lang = self._translator.detect_language(text)
        return self.translate_and_save(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            title=title,
        )

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

    def update_sentence_natural(
        self,
        translation_id: UUID,
        sentence_uuid: UUID,
        new_natural: str,
        provider: ProviderConfig,
    ) -> Translation:
        """Update natural translation of a sentence and regenerate word-by-word.

        Workflow:
        1. Load translation and find sentence by UUID
        2. Update sentence.natural_translation with new_natural
        3. Call provider.regenerate_alignment() to create new word-by-word
        4. Update sentence.word_alignments with new alignment
        5. Update translation.updated_at timestamp
        6. Save translation via storage

        Args:
            translation_id: UUID of the translation
            sentence_uuid: UUID of the sentence to update
            new_natural: New natural translation text
            provider: Provider to use for alignment generation

        Returns:
            Updated Translation object

        Raises:
            NotFoundError: If translation or sentence not found
            Exception: If alignment regeneration fails
        """
        translation = self._storage.get(translation_id)
        if not translation:
            raise NotFoundError(f"Translation {translation_id} not found")

        sentence = next((s for s in translation.sentences if s.uuid == sentence_uuid), None)
        if not sentence:
            raise NotFoundError(f"Sentence {sentence_uuid} not found in translation {translation_id}")

        translator = PydanticAITranslator(provider)
        new_alignments = translator.regenerate_alignment(
            sentence.source_text, new_natural, translation.source_language, translation.target_language
        )

        sentence.natural_translation = new_natural
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
