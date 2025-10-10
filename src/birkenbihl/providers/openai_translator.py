"""OpenAI translation provider implementation.

Uses OpenAI's GPT models (GPT-4, GPT-4o, etc.) for Birkenbihl translations.
API key provided via ProviderConfig.
"""

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.providers.base_translator import BaseTranslator


class OpenAITranslator:
    """Translation provider using OpenAI GPT models.

    Implements ITranslationProvider protocol using PydanticAI with OpenAI models.
    Uses structured outputs for reliable Birkenbihl method translations.

    Example:
        config = ProviderConfig(
            name="OpenAI GPT-4",
            provider_type="openai",
            model="gpt-4o",
            api_key="sk-..."
        )
        translator = OpenAITranslator(config)
        result = translator.translate("Hello world", "en", "de")
    """

    def __init__(self, provider_config: ProviderConfig):
        """Initialize OpenAI translator.

        Args:
            provider_config: Provider configuration with model and API key
        """
        provider = OpenAIProvider(api_key=provider_config.api_key)
        model = OpenAIChatModel(provider_config.model, provider=provider)
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
            Exception: If API call fails or OPENAI_API_KEY not set
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
