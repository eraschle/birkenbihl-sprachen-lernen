"""Base translation provider using PydanticAI.

Provides common translation logic shared across OpenAI, Anthropic, and other providers.
"""

import datetime
from collections.abc import AsyncIterator

from langdetect import detector_factory
from pydantic_ai import Agent
from pydantic_ai.models import Model

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.providers import text_utils
from birkenbihl.providers.models import SentenceResponse, TranslationResponse
from birkenbihl.providers.prompts import BIRKENBIHL_SYSTEM_PROMPT, create_translation_prompt


class BaseTranslator:
    """Base translator using PydanticAI for structured outputs.

    Provides common functionality for translation providers:
    - Language detection with langdetect
    - Structured translation using PydanticAI Agent
    - Response model → Domain model conversion

    Follows Dependency Inversion Principle: depends on PydanticAI Model abstraction,
    not concrete provider implementations.
    """

    def __init__(self, model: Model):
        """Initialize translator with PydanticAI model.

        Args:
            model: PydanticAI Model instance (OpenAIModel, AnthropicModel, etc.)
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
        # Split text into sentences deterministically
        sentences = text_utils.split_into_sentences(text)

        # Create user prompt with sentence list
        user_prompt = create_translation_prompt(sentences, source_lang, target_lang)

        # Run PydanticAI agent synchronously
        result = self._agent.run_sync(user_prompt)

        # Validation: If AI merged sentences, redistribute them
        if len(result.output.sentences) == 1 and len(sentences) > 1:
            # AI ignored our instructions and merged sentences - try to fix it
            try:
                result.output.sentences = text_utils.redistribute_merged_translation(
                    result.output.sentences[0], sentences
                )
            except ValueError:
                # Redistribution failed (AI didn't translate all sentences)
                # Fallback: translate each sentence individually
                result.output.sentences = []
                for sentence in sentences:
                    single_prompt = create_translation_prompt([sentence], source_lang, target_lang)
                    single_result = self._agent.run_sync(single_prompt)
                    result.output.sentences.extend(single_result.output.sentences)

        # Convert AI response to domain model
        return self._convert_to_domain_model(result.output, source_lang, target_lang)

    async def translate_stream(
        self, text: str, source_lang: str, target_lang: str
    ) -> AsyncIterator[tuple[float, Translation | None]]:
        """Translate text using Birkenbihl method with streaming progress.

        Yields partial results as sentences are completed, enabling real-time
        progress tracking and incremental UI updates.

        Args:
            text: Text to translate (can contain multiple sentences)
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Yields:
            Tuple of (progress: float, translation: Translation | None)
            - progress: 0.0 to 1.0 based on completed sentences
            - translation: Partial Translation with completed sentences (None initially)

        Raises:
            Exception: If translation fails
        """
        sentences = text_utils.split_into_sentences(text)
        total_sentences = len(sentences)
        user_prompt = create_translation_prompt(sentences, source_lang, target_lang)

        # Track completed sentences for progress calculation
        last_sentence_count = 0
        final_translation = None

        async with self._agent.run_stream(user_prompt) as result:
            async for partial_response in result.stream_output(debounce_by=0.01):
                current_sentence_count = len(partial_response.sentences)

                # Check if new sentences were completed
                if current_sentence_count > last_sentence_count:
                    # Calculate progress based on completed sentences
                    progress = current_sentence_count / total_sentences
                    progress = min(progress, 1.0)

                    # Convert partial response to domain model
                    final_translation = self._convert_to_domain_model(partial_response, source_lang, target_lang)

                    yield (progress, final_translation)
                    last_sentence_count = current_sentence_count

        # Ensure we yield final result with 100% progress if not already done
        if final_translation and last_sentence_count < total_sentences:
            yield (1.0, final_translation)

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
        """Create WordAlignment models from AI Sentence response model."""
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
        """Create Sentence models from AI response model."""
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
        now = datetime.datetime.now(datetime.UTC)

        # Generate default title from first sentence and timestamp
        first_text = response.sentences[0].source_text if response.sentences else "Übersetzung"
        # Truncate to 50 chars max
        default_title = first_text[:50] + ("..." if len(first_text) > 50 else "")

        return Translation(
            title=default_title,
            source_language=source_lang,
            target_language=target_lang,
            sentences=self._create_sentences(response),
            created_at=now,
            updated_at=now,
        )
