"""UI service layer interfaces.

Defines protocols for UI-specific service operations.
"""

from typing import Protocol
from uuid import UUID

from birkenbihl.models.translation import Translation
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


class TranslationUIService(Protocol):
    """Service layer for UI operations.

    Encapsulates storage/service initialization and provides
    high-level operations for the UI.
    """

    @property
    def service(self) -> TranslationService:
        """Get translation service instance.

        Returns:
            Initialized TranslationService
        """
        ...

    @property
    def storage(self) -> JsonStorageProvider:
        """Get storage provider instance.

        Returns:
            Initialized JsonStorageProvider
        """
        ...

    def get_translation(self, translation_id: UUID) -> Translation | None:
        """Get translation by ID.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation object or None if not found
        """
        ...

    def list_translations(self) -> list[Translation]:
        """List all translations.

        Returns:
            List of all translations, sorted by most recent first
        """
        ...
