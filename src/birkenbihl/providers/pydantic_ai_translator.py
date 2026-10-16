"""Translator for a provider configured in the settings."""

import logging

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.catalog import create_model

logger = logging.getLogger(__name__)


class PydanticAITranslator(BaseTranslator):
    """BaseTranslator whose model is built from a ProviderConfig (provider type, model name, API key).

    Example:
        translator = PydanticAITranslator(
            ProviderConfig(name="Claude", provider_type="anthropic", model="claude-sonnet-4-5", api_key="sk-ant-...")
        )
    """

    def __init__(self, provider_config: ProviderConfig):
        """Raises ProviderError if the provider type is not supported or its configuration is incomplete."""
        logger.info(
            "Initializing translator: provider=%s, model=%s, base_url=%s",
            provider_config.provider_type,
            provider_config.model,
            provider_config.api_url or "default",
        )
        super().__init__(create_model(provider_config))
