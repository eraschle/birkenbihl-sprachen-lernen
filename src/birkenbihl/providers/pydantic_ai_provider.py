"""Pydantic AI Provider für Translation Services."""

import os

from pydantic_ai import Agent

from ..models.translation import TranslationResult


class PydanticAITranslationProvider:
    """Pydantic AI Provider für Übersetzungen nach der Birkenbihl-Methode."""

    def __init__(self, model: str = "openai:gpt-4o", api_key: str | None = None) -> None:
        """Initialize the Pydantic AI Translation Provider.

        Args:
            model: Model identifier (e.g., "openai:gpt-4o", "anthropic:claude-3-5-sonnet-20241022")
            api_key: Optional API key. If not provided, will use environment variables
        """
        self._model = model
        self._api_key = api_key
        self._provider_name = self._extract_provider_name(model)

        # Set up API key environment variable if provided
        if api_key:
            if "openai" in model.lower():
                os.environ["OPENAI_API_KEY"] = api_key
            elif "anthropic" in model.lower():
                os.environ["ANTHROPIC_API_KEY"] = api_key

        # Create agents for different translation types
        self._natural_agent = Agent(
            model,
            system_prompt=(
                "Du bist ein Experte für natürliche Übersetzungen. "
                "Übersetze den gegebenen Text flüssig und natürlich in die Zielsprache. "
                "Achte auf Kontext, Idiome und kulturelle Nuancen. "
                "Gib nur die Übersetzung zurück, keine Erklärungen."
            ),
        )

        self._word_for_word_agent = Agent(
            model,
            system_prompt=(
                "Du bist ein Experte für Wort-für-Wort Übersetzungen nach der Birkenbihl-Methode. "
                "Übersetze jeden Begriff direkt und wörtlich, ohne die Satzstruktur zu verändern. "
                "Bewahre die ursprüngliche Wortstellung bei. "
                "Verwende Klammern () für notwendige Erklärungen oder Kontextinformationen. "
                "Beispiel: 'How are you?' -> 'Wie sind du?' oder 'Wie bist du?'"
                "Gib nur die wörtliche Übersetzung zurück, keine Erklärungen."
            ),
        )

        self._birkenbihl_agent = Agent(
            model,
            system_prompt=(
                "Du bist ein Experte für die Birkenbihl-Sprachlernmethode. "
                "Erstelle sowohl eine natürliche als auch eine Wort-für-Wort Übersetzung. "
                "Formatiere das Ergebnis als strukturiertes Alignment mit dem Original."
                "Die Wort-für-Wort Übersetzung soll die Struktur der Ausgangssprache zeigen."
            ),
        )

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
        if not self.is_language_supported(source_language) or not self.is_language_supported(target_language):
            raise ValueError(f"Language pair {source_language}-{target_language} not supported")

        try:
            prompt = self._build_translation_prompt(text, source_language, target_language, context, "natural")
            result = await self._natural_agent.run(prompt)
            return result.data.strip()

        except Exception as e:
            raise RuntimeError(f"Natural translation failed: {e}") from e

    async def translate_word_for_word(
        self,
        text: str,
        source_language: str,
        target_language: str,
        preserve_structure: bool = True,
    ) -> str:
        """Translate text word-for-word for dekodierung (decoding).

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
        if not self.is_language_supported(source_language) or not self.is_language_supported(target_language):
            raise ValueError(f"Language pair {source_language}-{target_language} not supported")

        try:
            prompt = self._build_translation_prompt(
                text, source_language, target_language, None, "word_for_word", preserve_structure
            )
            result = await self._word_for_word_agent.run(prompt)
            return result.data.strip()

        except Exception as e:
            raise RuntimeError(f"Word-for-word translation failed: {e}") from e

    async def translate_birkenbihl(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str | None = None,
    ) -> TranslationResult:
        """Perform complete Birkenbihl translation with both natural and word-for-word.

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
        if not self.is_language_supported(source_language) or not self.is_language_supported(target_language):
            raise ValueError(f"Language pair {source_language}-{target_language} not supported")

        try:
            # Get both translations
            natural_translation = await self.translate_natural(text, source_language, target_language, context)
            word_for_word_translation = await self.translate_word_for_word(text, source_language, target_language)

            # Create formatted alignment
            formatted_translation = self._create_formatted_alignment(
                text, natural_translation, word_for_word_translation
            )

            # Create TranslationResult with correct field names
            result = TranslationResult(
                natural_translation=natural_translation,
                word_by_word_translation=word_for_word_translation,
                formatted_decoding=formatted_translation,
            )

            return result

        except Exception as e:
            raise RuntimeError(f"Birkenbihl translation failed: {e}") from e

    @property
    def provider_name(self) -> str:
        """Get the name of the translation provider."""
        return self._provider_name

    @property
    def supported_languages(self) -> list[str]:
        """Get list of supported language codes."""
        # Common languages supported by most AI models
        return [
            "en",  # English
            "de",  # German
            "fr",  # French
            "es",  # Spanish
            "it",  # Italian
            "pt",  # Portuguese
            "nl",  # Dutch
            "da",  # Danish
            "sv",  # Swedish
            "no",  # Norwegian
            "fi",  # Finnish
            "pl",  # Polish
            "ru",  # Russian
            "ja",  # Japanese
            "ko",  # Korean
            "zh",  # Chinese
            "ar",  # Arabic
        ]

    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported by this provider."""
        return language_code.lower() in [lang.lower() for lang in self.supported_languages]

    def _extract_provider_name(self, model: str) -> str:
        """Extract provider name from model string."""
        if "openai" in model.lower():
            return "OpenAI"
        elif "anthropic" in model.lower():
            return "Anthropic"
        elif "google" in model.lower():
            return "Google"
        elif "cohere" in model.lower():
            return "Cohere"
        else:
            return "PydanticAI"

    def _build_translation_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str | None = None,
        translation_type: str = "natural",
        preserve_structure: bool = True,
    ) -> str:
        """Build translation prompt for AI model."""
        language_names = {
            "en": "English",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "da": "Danish",
            "sv": "Swedish",
            "no": "Norwegian",
            "fi": "Finnish",
            "pl": "Polish",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
        }

        source_lang_name = language_names.get(source_language.lower(), source_language)
        target_lang_name = language_names.get(target_language.lower(), target_language)

        if translation_type == "natural":
            prompt = f"Translate the following {source_lang_name} text to {target_lang_name} naturally and fluently:\n\n{text}"
            if context:
                prompt += f"\n\nContext: {context}"
        elif translation_type == "word_for_word":
            prompt = (
                f"Translate the following {source_lang_name} text to {target_lang_name} word-for-word. "
                f"Preserve the original word order and structure. "
                f"Use literal translations even if they sound awkward in {target_lang_name}:\n\n{text}"
            )
            if not preserve_structure:
                prompt += "\n\nNote: Focus on literal meaning over structure preservation."
        else:
            prompt = f"Translate the following {source_lang_name} text to {target_lang_name}:\n\n{text}"

        return prompt

    def _create_formatted_alignment(self, original: str, natural: str, word_for_word: str) -> str:
        """Create formatted alignment for Birkenbihl method display."""
        lines = [
            "=== Birkenbihl Method Translation ===",
            "",
            f"Original: {original}",
            "",
            f"Natural Translation: {natural}",
            "",
            f"Word-for-Word (Dekodierung): {word_for_word}",
            "",
            "=== Vertical Alignment ===",
            "",
        ]

        # Try to create word-by-word alignment
        original_words = original.split()
        word_for_word_words = word_for_word.split()

        # Simple alignment - may not be perfect for all languages
        max_words = max(len(original_words), len(word_for_word_words))

        for i in range(max_words):
            orig_word = original_words[i] if i < len(original_words) else ""
            trans_word = word_for_word_words[i] if i < len(word_for_word_words) else ""

            # Format with padding for alignment
            max_width = max(len(orig_word), len(trans_word), 10)
            lines.append(f"{orig_word:<{max_width}} | {trans_word}")

        return "\n".join(lines)
