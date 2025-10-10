"""Storage provider protocol for translation persistence."""

from typing import Protocol
from uuid import UUID

from birkenbihl.models.translation import Translation


class IStorageProvider(Protocol):
    """Protocol for storage providers.

    Defines interface for persisting and retrieving translations across
    different storage backends (JSON, SQLite, Excel, etc.).

    All implementations must use UUIDs for cross-storage compatibility.
    """

    def save(self, translation: Translation) -> Translation:
        """Save a new translation or update existing one.

        Args:
            translation: Translation to save

        Returns:
            Saved translation with updated metadata (e.g., updated_at)

        Raises:
            StorageError: If save operation fails
        """
        ...

    def get(self, translation_id: UUID) -> Translation | None:
        """Retrieve translation by ID.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation if found, None otherwise
        """
        ...

    def list_all(self) -> list[Translation]:
        """List all stored translations.

        Returns:
            List of all translations, ordered by updated_at (newest first)
        """
        ...

    def delete(self, translation_id: UUID) -> bool:
        """Delete translation by ID.

        Args:
            translation_id: UUID of the translation to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def update(self, translation: Translation) -> Translation:
        """Update existing translation.

        Args:
            translation: Translation with updated data

        Returns:
            Updated translation with new updated_at timestamp

        Raises:
            NotFoundError: If translation doesn't exist
            StorageError: If update operation fails
        """
        ...
