"""Birkenbihl App - Shared application logic for CLI and GUI.

This module contains the core application logic that is independent of
the presentation layer (CLI or GUI). It provides factory functions for
creating services and handles configuration.
"""

from pathlib import Path

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage import JsonStorageProvider


def get_translator(provider: ProviderConfig | None = None, settings_service: SettingsService | None = None):
    """Create translator based on provider configuration.

    Uses SettingsService to get default provider if not specified.

    Args:
        provider: Provider configuration (defaults to default provider from settings)
        settings_service: Optional SettingsService instance (creates new if not provided)

    Returns:
        Configured translator instance

    Raises:
        ValueError: If no provider configured
    """
    if provider is None:
        if settings_service is None:
            settings_service = SettingsService()
            settings_service.load_settings()
        provider = settings_service.get_default_provider()

    if provider is None:
        raise ValueError("No provider configured in settings.yaml")

    return PydanticAITranslator(provider)


def get_service(storage_path: Path | None = None, settings_service: SettingsService | None = None) -> TranslationService:
    """Create translation service with configured providers.

    Uses SettingsService for provider configuration.

    Args:
        storage_path: Optional storage path (defaults to ~/.birkenbihl)
        settings_service: Optional SettingsService instance (creates new if not provided)

    Returns:
        Configured TranslationService instance
    """
    if settings_service is None:
        settings_service = SettingsService()
        settings_service.load_settings()
    translator = get_translator(settings_service=settings_service)
    storage = JsonStorageProvider(storage_path)
    return TranslationService(translator, storage)
