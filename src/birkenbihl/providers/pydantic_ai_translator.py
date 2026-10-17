"""Translator for a provider configured in the settings."""

import logging
from collections.abc import Callable

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.protocols import IWordAligner
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.catalog import create_jev_model, create_model
from birkenbihl.providers.jev_aligner import JevAligner

logger = logging.getLogger(__name__)


class PydanticAITranslator(BaseTranslator):
    """BaseTranslator whose model is built from a ProviderConfig (provider type, model name, API key).

    Example:
        translator = PydanticAITranslator(
            ProviderConfig(name="Claude", provider_type="anthropic", model="claude-sonnet-4-5", api_key="sk-ant-...")
        )
    """

    def __init__(self, provider_config: ProviderConfig, aligner: IWordAligner | None = None):
        """Raises ProviderError if the provider type is not supported or its configuration is incomplete.

        Args:
            provider_config: Provider for the natural translation
            aligner: Word-by-word step; defaults to the same provider (LLMAligner)
        """
        logger.info(
            "Initializing translator: provider=%s, model=%s, base_url=%s, aligner=%s",
            provider_config.provider_type,
            provider_config.model,
            provider_config.api_url or "default",
            type(aligner).__name__ if aligner else "LLMAligner",
        )
        super().__init__(create_model(provider_config), aligner)


def translator_factory(settings: Settings) -> Callable[[ProviderConfig], PydanticAITranslator]:
    """Builds translators for any provider, with the word aligner chosen in the settings.

    Raises:
        ProviderError: If Jev is chosen but has no API key
    """
    if settings.word_aligner == "jev":
        aligner = JevAligner(create_jev_model(settings.jev_api_key))
        return lambda provider_config: PydanticAITranslator(provider_config, aligner)
    return PydanticAITranslator
