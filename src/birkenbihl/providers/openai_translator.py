"""OpenAI translation provider implementation.

Uses OpenAI's GPT models (GPT-4, GPT-4o, etc.) for Birkenbihl translations.
Requires OPENAI_API_KEY environment variable.
"""

from birkenbihl.models.translation import Translation
from birkenbihl.providers.base_translator import BaseTranslator


class OpenAITranslator:
    """Translation provider using OpenAI GPT models.

    Implements ITranslationProvider protocol using PydanticAI with OpenAI models.
    Uses structured outputs for reliable Birkenbihl method translations.

    Environment Requirements:
        OPENAI_API_KEY: OpenAI API key

    Example:
        translator = OpenAITranslator()
        result = translator.translate("Hello world", "en", "de")
    """

    def __init__(self, model: str = "openai:gpt-4o"):
        """Initialize OpenAI translator.

        Args:
            model: OpenAI model to use (default: gpt-4o)
                   Options: gpt-4o, gpt-4o-mini, gpt-4-turbo
        """
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
