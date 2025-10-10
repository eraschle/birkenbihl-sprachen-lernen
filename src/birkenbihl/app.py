"""Birkenbihl App - Shared application logic for CLI and GUI.

This module contains the core application logic that is independent of
the presentation layer (CLI or GUI). It provides factory functions for
creating services and handles configuration.
"""

from pathlib import Path

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers import AnthropicTranslator, OpenAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage import JsonStorageProvider


def get_translator(provider: ProviderConfig | None = None):
    """Create translator based on provider configuration.

    Uses SettingsService to get current provider if not specified.

    Args:
        provider: Provider configuration (defaults to current provider from settings)

    Returns:
        Configured translator instance

    Raises:
        ValueError: If no provider configured or provider type is unknown
    """
    if provider is None:
        provider = SettingsService.get_current_provider()

    if provider is None:
        raise ValueError("No provider configured in settings.yaml")

    if provider.provider_type == "openai":
        return OpenAITranslator(provider)
    elif provider.provider_type == "anthropic":
        return AnthropicTranslator(provider)
    else:
        raise ValueError(f"Unknown provider type: {provider.provider_type}")


def get_service(storage_path: Path | None = None) -> TranslationService:
    """Create translation service with configured providers.

    Uses SettingsService for provider configuration.

    Args:
        storage_path: Optional storage path (defaults to ~/.birkenbihl)

    Returns:
        Configured TranslationService instance
    """
    translator = get_translator()
    storage = JsonStorageProvider(storage_path)
    return TranslationService(translator, storage)
