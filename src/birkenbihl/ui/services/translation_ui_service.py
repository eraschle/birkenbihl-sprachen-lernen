"""UI service implementation for translation operations.

Provides a facade over TranslationService and StorageProvider,
eliminating duplicate initialization code across UI modules.
"""

import logging
from uuid import UUID

from birkenbihl.models.translation import Translation
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider

logger = logging.getLogger(__name__)


class TranslationUIServiceImpl:
    """Implementation of TranslationUIService.

    Provides lazy initialization of storage and service instances,
    following the Singleton pattern per session.
    """

    _storage: JsonStorageProvider | None = None
    _service: TranslationService | None = None

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure storage and service are initialized."""
        if cls._storage is None:
            cls._storage = JsonStorageProvider()
        if cls._service is None:
            cls._service = TranslationService(translator=None, storage=cls._storage)

    @classmethod
    def get_storage(cls) -> JsonStorageProvider:
        """Get storage provider instance.

        Returns:
            Initialized JsonStorageProvider
        """
        cls._ensure_initialized()
        assert cls._storage is not None  # For type checker
        return cls._storage

    @classmethod
    def get_service(cls) -> TranslationService:
        """Get translation service instance.

        Returns:
            Initialized TranslationService
        """
        cls._ensure_initialized()
        assert cls._service is not None  # For type checker
        return cls._service

    # Convenience properties for backwards compatibility
    storage = property(lambda self: self.get_storage())
    service = property(lambda self: self.get_service())

    @classmethod
    def get_translation(cls, translation_id: UUID) -> Translation | None:
        """Get translation by ID with error handling.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation object or None if not found

        Raises:
            Exception: If there's an error loading the translation
        """
        service = cls.get_service()
        try:
            translation = service.get_translation(translation_id)
            if translation:
                logger.debug("Loaded translation %s", translation_id)
            else:
                logger.warning("Translation %s not found", translation_id)
            return translation
        except Exception as e:
            logger.error("Failed to load translation %s: %s", translation_id, str(e), exc_info=True)
            raise

    @classmethod
    def list_translations(cls) -> list[Translation]:
        """List all translations, sorted by most recent first.

        Returns:
            List of all translations

        Raises:
            Exception: If there's an error listing translations
        """
        service = cls.get_service()
        try:
            translations = service.list_all_translations()
            # Sort by updated_at (most recent first)
            translations.sort(key=lambda t: t.updated_at, reverse=True)
            logger.debug("Listed %d translations", len(translations))
            return translations
        except Exception as e:
            logger.error("Failed to list translations: %s", str(e), exc_info=True)
            raise

    @classmethod
    def reset(cls) -> None:
        """Reset service instances.

        Useful for testing or when storage configuration changes.
        """
        cls._storage = None
        cls._service = None
        logger.debug("UI service instances reset")
