"""Birkenbihl App - Shared application logic for CLI and GUI.

This module contains the core application logic that is independent of
the presentation layer (CLI or GUI). It provides factory functions for
creating services and handles configuration.
"""

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers import PydanticAITranslator, translator_factory
from birkenbihl.services import path_service as ps
from birkenbihl.services.settings_service import SettingsService


def get_translator(
    provider: ProviderConfig | None = None, settings_service: SettingsService | None = None
) -> PydanticAITranslator:
    """Create translator based on provider configuration and the word aligner chosen in the settings.

    Uses SettingsService to get default provider if not specified.

    Args:
        provider: Provider configuration (defaults to default provider from settings)
        settings_service: Optional SettingsService instance (creates new if not provided)

    Returns:
        Configured translator instance

    Raises:
        ValueError: If no provider configured
        ProviderError: If a provider or the word aligner cannot be built (e.g. Jev without API key)
    """
    if settings_service is None:
        settings_service = SettingsService(ps.get_setting_path())
        settings_service.load_settings()
    provider = provider or settings_service.get_default_provider()

    if provider is None:
        raise ValueError("No provider configured in settings.yaml")

    return translator_factory(settings_service.get_settings())(provider)
