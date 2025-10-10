"""Base translation provider using PydanticAI.

Provides common translation logic shared across OpenAI, Anthropic, and other providers.
"""

from datetime import datetime, timezone

from langdetect import detector_factory
from pydantic_ai import Agent

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.providers.models import SentenceResponse, TranslationResponse
from birkenbihl.providers.prompts import BIRKENBIHL_SYSTEM_PROMPT, create_translation_prompt


class BaseTranslator:
    """Base translator using PydanticAI for structured outputs.

    Provides common functionality for translation providers:
    - Language detection with langdetect
    - Structured translation using PydanticAI Agent
    - Response model → Domain model conversion
    """

    def __init__(self, model: str):
        """Initialize translator with specific model.

        Args:
            model: PydanticAI model string (e.g., 'openai:gpt-4o', 'anthropic:claude-3-5-sonnet-20241022')
        """
        self._agent = Agent(
            model=model,
            output_type=TranslationResponse,
            system_prompt=BIRKENBIHL_SYSTEM_PROMPT,
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> Translation:
        """Translate text using Birkenbihl method.

        Args:
            text: Text to translate (can contain multiple sentences)
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Returns:
            Translation with natural and word-by-word translations

        Raises:
            Exception: If translation fails
        """
        # Create user prompt
        user_prompt = create_translation_prompt(text, source_lang, target_lang)

        # Run PydanticAI agent synchronously
        result = self._agent.run_sync(user_prompt)

        # Convert AI response to domain model
        return self._convert_to_domain_model(result.output, source_lang, target_lang)

    def detect_language(self, text: str) -> str:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language code (en, es, de, etc.)

        Raises:
            langdetect.LangDetectException: If detection fails
        """
        # Use langdetect library for language detection
        return detector_factory.detect(text)

    def _create_word_alignments(self, sentence: SentenceResponse) -> list[WordAlignment]:
        alignments = []
        for align in sentence.word_alignments:
            word_alignment = WordAlignment(
                source_word=align.source_word,
                target_word=align.target_word,
                position=align.position,
            )
            alignments.append(word_alignment)
        return alignments

    def _create_sentences(self, translation: TranslationResponse) -> list[Sentence]:
        sentences = []
        for sent in translation.sentences:
            sentence = Sentence(
                source_text=sent.source_text,
                natural_translation=sent.natural_translation,
                word_alignments=self._create_word_alignments(sent),
            )
            sentences.append(sentence)
        return sentences

    def _convert_to_domain_model(
        self, response: TranslationResponse, source_lang: str, target_lang: str
    ) -> Translation:
        """Convert AI response model to domain Translation model.

        Args:
            response: AI response with translations
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Domain Translation model with UUIDs and timestamps
        """
        # Create Translation with metadata
        now = datetime.now(timezone.utc)
        return Translation(
            source_language=source_lang,
            target_language=target_lang,
            sentences=self._create_sentences(response),
            created_at=now,
            updated_at=now,
        )
