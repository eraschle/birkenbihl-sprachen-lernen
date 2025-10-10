"""Anthropic translation provider implementation.

Uses Anthropic's Claude models for Birkenbihl translations.
Requires ANTHROPIC_API_KEY environment variable.
"""

from birkenbihl.models.translation import Translation
from birkenbihl.providers.base_translator import BaseTranslator


class AnthropicTranslator:
    """Translation provider using Anthropic Claude models.

    Implements ITranslationProvider protocol using PydanticAI with Anthropic models.
    Uses tool-based structured outputs (Anthropic doesn't support native structured outputs).

    Environment Requirements:
        ANTHROPIC_API_KEY: Anthropic API key

    Example:
        translator = AnthropicTranslator()
        result = translator.translate("Hola mundo", "es", "de")
    """

    def __init__(self, model: str = "anthropic:claude-3-5-sonnet-20241022"):
        """Initialize Anthropic translator.

        Args:
            model: Anthropic model to use (default: claude-3-5-sonnet-20241022)
                   Options: claude-3-5-sonnet-20241022, claude-3-opus-20240229,
                           claude-3-sonnet-20240229, claude-3-haiku-20240307
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
