"""Service for managing application settings and provider configurations."""

from pathlib import Path
from threading import Lock

import yaml

from birkenbihl.models.settings import ProviderConfig, Settings


class SettingsService:
    """Service for managing application settings and provider configurations.

    Implements singleton pattern with lazy loading for centralized settings management.
    Orchestrates Settings model operations while maintaining separation of concerns.
    Thread-safe singleton ensures consistent configuration across application.
    Tracks currently active provider for translation operations.
    """

    _instance: "SettingsService | None" = None
    _settings: Settings | None = None
    _current_provider: ProviderConfig | None = None
    _lock: Lock = Lock()

    def __init__(self):
        """Private constructor for singleton pattern.

        Use get_instance() to obtain the service instance.
        """
        if SettingsService._instance is not None:
            raise RuntimeError("Use get_instance() to get singleton instance")

    @staticmethod
    def _load_settings_from_file(settings_file: str | Path) -> Settings:
        """Load settings from specified YAML file.

        Reads YAML configuration file and constructs Settings instance.
        Returns default Settings if file does not exist.

        Args:
            settings_file: Path to YAML settings file

        Returns:
            Settings instance populated from YAML or defaults
        """
        config_path = Path(settings_file)
        if not config_path.exists():
            return Settings()

        with config_path.open("r") as file:
            data = yaml.safe_load(file) or {}

        providers_data = data.get("providers", [])
        providers = [ProviderConfig(**provider) for provider in providers_data]
        target_language = data.get("target_language", "de")

        return Settings(providers=providers, target_language=target_language)

    @staticmethod
    def _save_settings_to_file(settings: Settings, settings_file: str | Path) -> None:
        """Save settings to specified YAML file.

        Converts Settings instance to dictionary and writes to YAML file.
        Creates parent directories if they do not exist.

        Args:
            settings: Settings instance to persist
            settings_file: Path to YAML settings file
        """
        config_path = Path(settings_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = settings.model_dump()

        with config_path.open("w") as file:
            yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)

    @classmethod
    def get_instance(cls) -> "SettingsService":
        """Get or create singleton instance of SettingsService.

        Thread-safe singleton creation. Returns existing instance if available.

        Returns:
            Singleton SettingsService instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = cls.__new__(cls)
                    cls._instance = instance
        return cls._instance

    @classmethod
    def get_settings(cls) -> Settings:
        """Get current settings, loading from settings.yaml if not already loaded.

        Lazy loading: Settings are loaded on first access using default settings.yaml path.
        Automatically initializes current provider to default provider.

        Returns:
            Current Settings instance
        """
        if cls._settings is None:
            with cls._lock:
                if cls._settings is None:
                    cls._settings = cls._load_settings_from_file("settings.yaml")
                    if cls._current_provider is None:
                        cls._current_provider = cls._settings.get_default_provider()
        return cls._settings

    @classmethod
    def load_settings(cls, settings_file: str | Path = "settings.yaml") -> Settings:
        """Load settings from specified settings file.

        Replaces current settings with newly loaded configuration.
        Updates current provider to new default provider.
        Thread-safe operation ensures consistency during concurrent access.

        Args:
            settings_file: Path to settings file (defaults to settings.yaml in current directory)

        Returns:
            Loaded Settings instance
        """
        with cls._lock:
            cls._settings = cls._load_settings_from_file(settings_file)
            cls._current_provider = cls._settings.get_default_provider()
        return cls._settings

    @classmethod
    def save_settings(cls, settings: Settings, settings_file: str | Path = "settings.yaml") -> None:
        """Save settings to specified settings file.

        Updates current settings and persists to file.
        Thread-safe operation prevents race conditions during save.

        Args:
            settings: Settings instance to save
            settings_file: Path to settings file (defaults to settings.yaml in current directory)
        """
        with cls._lock:
            cls._save_settings_to_file(settings, settings_file)
            cls._settings = settings

    @classmethod
    def get_default_provider(cls) -> ProviderConfig | None:
        """Get default provider configuration.

        Delegates to Settings.get_default_provider() for business logic.
        Returns first provider marked as default, or first available provider,
        or None if no providers configured.

        Returns:
            Default ProviderConfig or None if no providers exist
        """
        return cls.get_settings().get_default_provider()

    @classmethod
    def get_current_provider(cls) -> ProviderConfig | None:
        """Get currently active provider configuration.

        Returns the provider currently selected for translation operations.
        If not set, initializes to default provider from settings.

        Returns:
            Current ProviderConfig or None if no providers exist
        """
        with cls._lock:
            if cls._current_provider is None:
                cls._current_provider = cls.get_settings().get_default_provider()
            return cls._current_provider

    @classmethod
    def set_current_provider(cls, provider: ProviderConfig) -> None:
        """Set currently active provider for translation operations.

        Updates the active provider without modifying persisted settings.
        Thread-safe operation ensures consistency during concurrent access.

        Args:
            provider: ProviderConfig to set as current active provider
        """
        with cls._lock:
            cls._current_provider = provider

    @classmethod
    def reset_current_provider(cls) -> None:
        """Reset current provider to default provider from settings.

        Reverts active provider selection to the configured default.
        Thread-safe operation ensures consistency during concurrent access.
        """
        with cls._lock:
            cls._current_provider = cls.get_settings().get_default_provider()
