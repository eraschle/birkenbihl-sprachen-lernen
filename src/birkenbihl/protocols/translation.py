"""Translation provider protocol."""

from typing import Protocol

from birkenbihl.models.languages import Language
from birkenbihl.models.translation import Translation, WordAlignment


class ITranslationProvider(Protocol):
    """Protocol for translation providers."""

    def translate(
        self, text: str, source_lang: Language, target_lang: Language, title: str | None = None
    ) -> Translation:
        """Translate text using Birkenbihl method.

        Args:
            text: Text to translate
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Returns:
            Translation with natural and word-by-word translations
        """
        ...

    def detect_language(self, text: str) -> Language:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language code (en, es, de)
        """
        ...

    def generate_alternatives(
        self,
        source_text: str,
        source_lang: Language,
        target_lang: Language,
        count: int = 3,
    ) -> list[str]:
        """Generate alternative natural translations for a sentence.

        Args:
            source_text: Original sentence to translate
            source_lang: Source language
            target_lang: Target language
            count: Number of alternative translations to generate (default: 3)

        Returns:
            List of natural translation alternatives
        """
        ...

    def regenerate_alignment(
        self,
        source_text: str,
        natural_translation: str,
        source_lang: Language,
        target_lang: Language,
    ) -> list[WordAlignment]:
        """Generate word-by-word alignment based on given natural translation.

        Args:
            source_text: Original sentence
            natural_translation: Natural translation
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of WordAlignment objects mapping source words to target words
        """
        ...
