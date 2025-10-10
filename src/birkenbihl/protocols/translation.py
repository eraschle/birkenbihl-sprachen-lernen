"""Translation provider protocol."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from birkenbihl.models.translation import Translation


class ITranslationProvider(Protocol):
    """Protocol for translation providers."""

    def translate(self, text: str, source_lang: str, target_lang: str) -> "Translation":
        """Translate text using Birkenbihl method.

        Args:
            text: Text to translate
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Returns:
            Translation with natural and word-by-word translations
        """
        ...

    def detect_language(self, text: str) -> str:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language code (en, es, de)
        """
        ...
