"""Anthropic translation provider implementation.

Uses Anthropic's Claude models for Birkenbihl translations.
API key provided via ProviderConfig.
"""

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.providers.base_translator import BaseTranslator


class AnthropicTranslator:
    """Translation provider using Anthropic Claude models.

    Implements ITranslationProvider protocol using PydanticAI with Anthropic models.
    Uses tool-based structured outputs (Anthropic doesn't support native structured outputs).

    Example:
        config = ProviderConfig(
            name="Claude Sonnet",
            provider_type="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="sk-ant-..."
        )
        translator = AnthropicTranslator(config)
        result = translator.translate("Hola mundo", "es", "de")
    """

    def __init__(self, provider_config: ProviderConfig):
        """Initialize Anthropic translator.

        Args:
            provider_config: Provider configuration with model and API key
        """
        provider = AnthropicProvider(api_key=provider_config.api_key)
        model = AnthropicModel(provider_config.model, provider=provider)
        self._translator = BaseTranslator(model)

    def translate(self, text: str, source_lang: str, target_lang: str) -> Translation:
        """Translate text using Birkenbihl method.

        Args:
            text: Text to translate
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Returns:
            Translation with natural and word-by-word translations

        Raises:
            Exception: If API call fails or ANTHROPIC_API_KEY not set
        """
        return self._translator.translate(text, source_lang, target_lang)

    def detect_language(self, text: str) -> str:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language code (en, es, de)
        """
        return self._translator.detect_language(text)
