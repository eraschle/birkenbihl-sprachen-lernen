"""Service for managing application settings and provider configurations."""

from pathlib import Path
from threading import Lock

import yaml

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services import path_service as ps
from birkenbihl.storage.settings_storage import SettingsStorageProvider


class SettingsService:
    """Service for managing application settings and provider configurations.

    Instance-based service for settings management with internal state.
    Orchestrates Settings model operations while maintaining separation of concerns.
    Thread-safe operations ensure consistent configuration access.
    """

    def __init__(self, file_path: Path):
        """Initialize SettingsService with empty state.

        Call load_settings() to load configuration from file or database.

        Args:
            db_path: Optional custom database path (defaults to ~/.birkenbihl/birkenbihl.db)
        """
        self._settings: Settings | None = None
        self._storage: SettingsStorageProvider | None = None
        self._lock = Lock()
        self._file_path = file_path if file_path else ps.get_setting_path()

    def get_settings(self) -> Settings:
        """Get current settings.

        Returns:
            Current Settings instance

        Raises:
            RuntimeError: If settings not loaded yet
        """
        if self._settings is None:
            raise RuntimeError("Settings not loaded. Call load_settings() first.")
        return self._settings

    def load_settings(self, use_database: bool = False) -> Settings:
        """Load settings from specified settings file or database.

        Replaces current settings with newly loaded configuration.
        Thread-safe operation ensures consistency during concurrent access.

        Args:
            use_database: If True, load from database instead of YAML file

        Returns:
            Loaded Settings instance
        """
        with self._lock:
            if use_database:
                if self._storage is None:
                    self._storage = SettingsStorageProvider(self._file_path)
                self._settings = self._storage.load()
            else:
                self._settings = self._load_settings_from_file()
        return self._settings

    @staticmethod
    def validate_provider_config(provider: ProviderConfig) -> str | None:
        """Validate provider configuration.

        Checks if provider settings are valid, especially streaming support.

        Args:
            provider: Provider configuration to validate

        Returns:
            Error message if validation fails, None if valid
        """
        from birkenbihl.providers.registry import ProviderRegistry

        # Check if provider type is supported
        if not ProviderRegistry.is_supported(provider.provider_type):
            return f"Provider '{provider.provider_type}' wird nicht unterstützt"

        # Check if streaming is enabled but not supported
        if provider.supports_streaming and not ProviderRegistry.supports_streaming(provider):
            return (
                f"Provider '{provider.provider_type}' mit Modell '{provider.model}' unterstützt kein Streaming. "
                f"Bitte deaktivieren Sie die Streaming-Option für diese Kombination."
            )

        return None

    def add_provider(self, provider: ProviderConfig) -> None:
        """Add a provider to settings with automatic default management.

        Applies business rules:
        - If no providers exist or no default exists, mark new provider as default
        - If new provider is marked as default, clear other defaults

        Args:
            provider: Provider configuration to add

        Raises:
            RuntimeError: If settings not loaded yet
        """
        if self._settings is None:
            raise RuntimeError("Settings not loaded. Call load_settings() first.")

        # Check if any provider is already marked as default
        has_default = any(p.is_default for p in self._settings.providers)

        # Auto-set as default if no providers exist or no default exists
        if not self._settings.providers or not has_default:
            provider.is_default = True

        # If new provider is default, clear other defaults
        if provider.is_default:
            for prov in self._settings.providers:
                prov.is_default = False

        self._settings.providers.append(provider)

    def update_provider(self, index: int, provider: ProviderConfig) -> None:
        """Update a provider with automatic default management.

        Applies business rules:
        - If updated provider is marked as default, clear other defaults

        Args:
            index: Index of provider to update
            provider: New provider configuration

        Raises:
            RuntimeError: If settings not loaded yet
            IndexError: If index is out of range
        """
        if self._settings is None:
            raise RuntimeError("Settings not loaded. Call load_settings() first.")

        if index < 0 or index >= len(self._settings.providers):
            raise IndexError(f"Provider index {index} out of range")

        # If updated provider is set as default, clear other defaults
        if provider.is_default:
            for idx, prov in enumerate(self._settings.providers):
                if idx != index:
                    prov.is_default = False

        self._settings.providers[index] = provider

    def delete_provider(self, index: int) -> None:
        """Delete a provider with automatic default management.

        Applies business rules:
        - If deleted provider was default and providers remain, set first as default

        Args:
            index: Index of provider to delete

        Raises:
            RuntimeError: If settings not loaded yet
            IndexError: If index is out of range
        """
        if self._settings is None:
            raise RuntimeError("Settings not loaded. Call load_settings() first.")

        if index < 0 or index >= len(self._settings.providers):
            raise IndexError(f"Provider index {index} out of range")

        # Check if deleted provider was default
        was_default = self._settings.providers[index].is_default

        del self._settings.providers[index]

        # If default was deleted and providers remain, set first as default
        if was_default and self._settings.providers:
            self._settings.providers[0].is_default = True

    def save_settings(self, use_database: bool = False) -> None:
        """Save settings to specified settings file or database.

        Persists current settings to file or database.
        Thread-safe operation prevents race conditions during save.

        Args:
            use_database: If True, save to database instead of YAML file

        Raises:
            RuntimeError: If settings not loaded yet
            ValueError: If any provider configuration is invalid
        """
        if self._settings is None:
            raise RuntimeError("Settings not loaded. Call load_settings() first.")

        # Validate all providers before saving
        for provider in self._settings.providers:
            error = self.validate_provider_config(provider)
            if error:
                raise ValueError(error)

        with self._lock:
            if use_database:
                if self._storage is None:
                    self._storage = SettingsStorageProvider(self._file_path)
                self._storage.save(self._settings)
            else:
                self._save_settings_to_file()

    def get_default_provider(self) -> ProviderConfig | None:
        """Get default provider configuration.

        Delegates to Settings.get_default_provider() for business logic.
        Returns first provider marked as default, or first available provider,
        or None if no providers configured.

        Returns:
            Default ProviderConfig or None if no providers exist

        Raises:
            RuntimeError: If settings not loaded yet
        """
        return self.get_settings().get_default_provider()

    def _load_settings_from_file(self) -> Settings:
        """Load settings from specified YAML file.

        Reads YAML configuration file and constructs Settings instance.
        Returns default Settings if file does not exist.

        Args:
            settings_file: Path to YAML settings file

        Returns:
            Settings instance populated from YAML or defaults
        """
        if not self._file_path.exists():
            return Settings()

        with self._file_path.open("r") as file:
            data = yaml.safe_load(file) or {}

        providers_data = data.get("providers", [])
        providers = [ProviderConfig(**provider) for provider in providers_data]
        target_language = data.get("target_language", "de")

        return Settings(providers=providers, target_language=target_language)

    def _save_settings_to_file(self) -> None:
        """Save settings to specified YAML file.

        Converts Settings instance to dictionary and writes to YAML file.
        Creates parent directories if they do not exist.

        Args:
            settings: Settings instance to persist
            settings_file: Path to YAML settings file

        Raises:
            RuntimeError: If settings not loaded yet
        """
        if self._settings is None:
            raise RuntimeError("No settings are available")

        if not self._file_path.parent.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._settings.model_dump()
        with self._file_path.open("w") as file:
            yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)
