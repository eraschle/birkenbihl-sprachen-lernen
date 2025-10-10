"""Translation service for orchestrating translation and storage operations."""

from uuid import UUID

from birkenbihl.models.translation import Translation
from birkenbihl.protocols import IStorageProvider, ITranslationProvider


class TranslationService:
    """Service orchestrating translation and storage operations.

    Coordinates between TranslationProvider (AI translation) and
    StorageProvider (persistence) to provide high-level translation workflows.

    Follows SOLID principles with dependency injection via protocols.
    """

    def __init__(self, translator: ITranslationProvider, storage: IStorageProvider):
        """Initialize service with providers.

        Args:
            transaltor: Provider for AI-based translations
            storage: Provider for persistence operations
        """
        super().__init__()
        self._translator = translator
        self._storage = storage

    def translate_and_save(
        self, text: str, source_lang: str, target_lang: str, title: str
    ) -> Translation:
        """Translate text using Birkenbihl method and save to storage.

        Args:
            text: Text to translate (can contain multiple sentences)
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)
            title: Document title

        Returns:
            Saved Translation with natural and word-by-word translations

        Raises:
            TranslationError: If translation fails
            StorageError: If save fails
        """
        # Get translation from AI provider
        result = self._translator.translate(text, source_lang, target_lang)

        # Create Translation domain model
        translation = Translation(
            title=title,
            source_language=source_lang,
            target_language=target_lang,
            sentences=result.sentences,  # Assuming provider returns compatible format
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

    def auto_detect_and_translate(
        self, text: str, target_lang: str, title: str
    ) -> Translation:
        """Auto-detect source language and translate.

        Args:
            text: Text to translate
            target_lang: Target language code
            title: Document title

        Returns:
            Saved Translation

        Raises:
            TranslationError: If detection or translation fails
        """
        source_lang = self._translator.detect_language(text)
        return self.translate_and_save(text, source_lang, target_lang, title)
