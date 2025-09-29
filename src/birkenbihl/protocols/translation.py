"""Translation provider protocol for AI translation services."""

from typing import Protocol, runtime_checkable

from ..models.translation import TranslationResult


@runtime_checkable
class TranslationProviderProtocol(Protocol):
    """Protocol defining the interface for AI translation providers.

    This protocol ensures that any AI translation provider (OpenAI, Anthropic, etc.)
    implements the required methods for natural and word-for-word translations
    following the Birkenbihl method.

    The Birkenbihl method requires:
    1. Natural translation for comprehension
    2. Word-for-word "dekodierung" (decoding) for language structure learning
    3. Formatted alignment showing original text structure
    """

    async def translate_natural(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str | None = None,
    ) -> str:
        """Translate text naturally with proper grammar and meaning.

        Parameters
        ----------
        text : str
            The source text to translate
        source_language : str
            Source language code (e.g., 'en', 'de', 'fr')
        target_language : str
            Target language code (e.g., 'en', 'de', 'fr')
        context : str | None, optional
            Additional context to improve translation quality

        Returns
        -------
        str
            Natural translation that sounds fluent in the target language

        Raises
        ------
        ValueError
            If language codes are not supported
        RuntimeError
            If translation service is unavailable
        """
        ...

    async def translate_word_for_word(
        self,
        text: str,
        source_language: str,
        target_language: str,
        preserve_structure: bool = True,
    ) -> str:
        """Translate text word-for-word for dekodierung (decoding).

        This is the core of the Birkenbihl method - creating a literal translation
        that preserves the original language structure to help learners understand
        how the source language works.

        Parameters
        ----------
        text : str
            The source text to translate word-for-word
        source_language : str
            Source language code (e.g., 'en', 'de', 'fr')
        target_language : str
            Target language code (e.g., 'en', 'de', 'fr')
        preserve_structure : bool, default=True
            Whether to preserve the original word order and structure

        Returns
        -------
        str
            Word-for-word translation preserving source language structure

        Raises
        ------
        ValueError
            If language codes are not supported
        RuntimeError
            If translation service is unavailable
        """
        ...

    async def translate_birkenbihl(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str | None = None,
    ) -> TranslationResult:
        """Perform complete Birkenbihl translation with both natural and word-for-word.

        This method combines both translation types and formats them according to
        the Birkenbihl method with proper alignment and structure preservation.

        Parameters
        ----------
        text : str
            The source text to translate
        source_language : str
            Source language code (e.g., 'en', 'de', 'fr')
        target_language : str
            Target language code (e.g., 'en', 'de', 'fr')
        context : str | None, optional
            Additional context to improve translation quality

        Returns
        -------
        TranslationResult
            Complete translation result with natural, word-for-word, and formatted versions

        Raises
        ------
        ValueError
            If language codes are not supported
        RuntimeError
            If translation service is unavailable
        """
        ...

    @property
    def provider_name(self) -> str:
        """Get the name of the translation provider.

        Returns
        -------
        str
            Provider name (e.g., "OpenAI", "Anthropic", "Google")
        """
        ...

    @property
    def supported_languages(self) -> list[str]:
        """Get list of supported language codes.

        Returns
        -------
        list[str]
            List of supported language codes (e.g., ['en', 'de', 'fr', 'es'])
        """
        ...

    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported by this provider.

        Parameters
        ----------
        language_code : str
            Language code to check (e.g., 'en', 'de', 'fr')

        Returns
        -------
        bool
            True if language is supported, False otherwise
        """
        ...
