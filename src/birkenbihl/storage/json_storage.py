"""JSON file-based storage provider implementation."""

import json
from pathlib import Path
from uuid import UUID

from birkenbihl.models import dateutils
from birkenbihl.models.translation import Translation


class JsonStorageProvider:
    """Storage provider using JSON files for persistence.

    Stores translations in a single JSON file with array of translation objects.
    Each translation is serialized using Pydantic's model_dump().

    Args:
        file_path: Path to JSON storage file (default: ~/.birkenbihl/translations.json)

    Example:
        storage = JsonStorageProvider()
        storage.save(translation)
    """

    def __init__(self, file_path: Path | str | None = None):
        """Initialize JSON storage provider.

        Args:
            file_path: Path to storage file. If None, uses ~/.birkenbihl/translations.json
        """
        if file_path is None:
            file_path = Path.home() / ".birkenbihl" / "translations.json"
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._write_translations([])

    def save(self, translation: Translation) -> Translation:
        """Save a new translation or update existing one.

        Args:
            translation: Translation to save

        Returns:
            Saved translation with updated metadata
        """
        translations = self._read_translations()

        # Check if translation exists (update case)
        existing_idx = next(
            (i for i, t in enumerate(translations) if t.uuid == translation.uuid),
            None,
        )

        # Update timestamp
        translation.updated_at = dateutils.create_now()

        if existing_idx is not None:
            translations[existing_idx] = translation
        else:
            translations.append(translation)

        self._write_translations(translations)
        return translation

    def get(self, translation_id: UUID) -> Translation | None:
        """Retrieve translation by ID.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation if found, None otherwise
        """
        translations = self._read_translations()
        return next((t for t in translations if t.uuid == translation_id), None)

    def list_all(self) -> list[Translation]:
        """List all stored translations.

        Returns:
            List of all translations, ordered by updated_at (newest first)
        """
        translations = self._read_translations()
        return sorted(translations, key=lambda t: t.updated_at, reverse=True)

    def delete(self, translation_id: UUID) -> bool:
        """Delete translation by ID.

        Args:
            translation_id: UUID of the translation to delete

        Returns:
            True if deleted, False if not found
        """
        translations = self._read_translations()
        initial_count = len(translations)
        translations = [t for t in translations if t.uuid != translation_id]

        if len(translations) < initial_count:
            self._write_translations(translations)
            return True
        return False

    def update(self, translation: Translation) -> Translation:
        """Update existing translation.

        Args:
            translation: Translation with updated data

        Returns:
            Updated translation with new updated_at timestamp

        Raises:
            ValueError: If translation doesn't exist
        """
        translations = self._read_translations()
        existing_idx = next(
            (i for i, t in enumerate(translations) if t.uuid == translation.uuid),
            None,
        )

        if existing_idx is None:
            raise ValueError(f"Translation with id {translation.uuid} not found")

        translation.updated_at = dateutils.create_now()
        translations[existing_idx] = translation
        self._write_translations(translations)
        return translation

    def _read_translations(self) -> list[Translation]:
        """Read all translations from JSON file."""
        with self._file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return [Translation.model_validate(t) for t in data]

    def _write_translations(self, translations: list[Translation]) -> None:
        """Write all translations to JSON file."""
        data = [t.model_dump(mode="json") for t in translations]
        with self._file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
