"""Base translation provider using PydanticAI.

Provides common translation logic shared across OpenAI, Anthropic, and other providers.
"""

import datetime
import logging
import time
from collections.abc import AsyncIterator
from typing import Protocol

from langdetect import detector_factory
from pydantic_ai import Agent
from pydantic_ai.models import Model

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.providers import text_utils
from birkenbihl.providers.models import (
    AlignmentResponse,
    AlternativesResponse,
    TranslationResponse,
    WordAlignmentResponse,
)
from birkenbihl.providers.prompts import (
    BIRKENBIHL_SYSTEM_PROMPT,
    create_alternatives_prompt,
    create_regenerate_alignment_prompt,
    create_translation_prompt,
)

logger = logging.getLogger(__name__)


class IWordAlignmentResponse(Protocol):
    word_alignments: list[WordAlignmentResponse]


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
        logger.info("Split text into %d sentences", len(sentences))
        logger.debug("Sentences: %s", [s[:50] + "..." if len(s) > 50 else s for s in sentences])

        # Create user prompt with sentence list
        user_prompt = create_translation_prompt(sentences, source_lang, target_lang)
        logger.debug("Created translation prompt")

        # Run PydanticAI agent synchronously
        logger.info("=" * 60)
        logger.info("API REQUEST START")
        logger.info("=" * 60)
        logger.info("Model: %s", self._agent.model)
        logger.info("Source Language: %s", source_lang)
        logger.info("Target Language: %s", target_lang)
        logger.info("Sentences to translate: %d", len(sentences))
        logger.debug("Prompt: %s", user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt)

        start_time = time.time()
        result = self._agent.run_sync(user_prompt)
        elapsed_time = time.time() - start_time

        logger.info("=" * 60)
        logger.info("API RESPONSE RECEIVED")
        logger.info("=" * 60)
        logger.info("Response time: %.2f seconds", elapsed_time)
        logger.info("Sentences received: %d", len(result.output.sentences))
        logger.info("Response cost: %s", result.cost() if hasattr(result, "cost") else "N/A")

        # Log each translated sentence (DEBUG level)
        for i, sent in enumerate(result.output.sentences, 1):
            logger.debug(
                "Sentence %d: '%s' → '%s' (%d word alignments)",
                i,
                sent.source_text[:50] + "..." if len(sent.source_text) > 50 else sent.source_text,
                sent.natural_translation[:50] + "..."
                if len(sent.natural_translation) > 50
                else sent.natural_translation,
                len(sent.word_alignments),
            )

        # Validation: If AI merged sentences, redistribute them
        if len(result.output.sentences) == 1 and len(sentences) > 1:
            logger.warning("AI merged %d sentences into 1, attempting to redistribute...", len(sentences))
            # AI ignored our instructions and merged sentences - try to fix it
            try:
                result.output.sentences = text_utils.redistribute_merged_translation(
                    result.output.sentences[0], sentences
                )
                logger.info("Successfully redistributed merged translation")
            except ValueError as e:
                logger.warning("Redistribution failed (%s), falling back to individual sentence translation", str(e))
                # Redistribution failed (AI didn't translate all sentences)
                # Fallback: translate each sentence individually
                result.output.sentences = []
                for i, sentence in enumerate(sentences, 1):
                    logger.debug("Translating sentence %d/%d individually", i, len(sentences))
                    single_prompt = create_translation_prompt([sentence], source_lang, target_lang)
                    single_result = self._agent.run_sync(single_prompt)
                    result.output.sentences.extend(single_result.output.sentences)
                logger.info("Completed individual sentence translation: %d sentences", len(result.output.sentences))

        # Convert AI response to domain model
        logger.debug("Converting AI response to domain model")
        translation = self._convert_to_domain_model(result.output, source_lang, target_lang)
        logger.info(
            "Translation complete: %d sentences, %d total word alignments",
            len(translation.sentences),
            sum(len(s.word_alignments) for s in translation.sentences),
        )
        return translation

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
        logger.info("Starting streaming translation: %d sentences", total_sentences)
        user_prompt = create_translation_prompt(sentences, source_lang, target_lang)

        # Track completed sentences for progress calculation
        last_sentence_count = 0
        final_translation = None

        logger.info("=" * 60)
        logger.info("STREAMING API REQUEST START")
        logger.info("=" * 60)
        logger.info("Model: %s", self._agent.model)
        logger.info("Source Language: %s", source_lang)
        logger.info("Target Language: %s", target_lang)
        logger.info("Sentences to translate: %d", total_sentences)

        start_time = time.time()
        async with self._agent.run_stream(user_prompt) as result:
            async for partial_response in result.stream_output(debounce_by=0.01):
                current_sentence_count = len(partial_response.sentences)

                # Check if new sentences were completed
                if current_sentence_count > last_sentence_count:
                    # Calculate progress based on completed sentences
                    progress = current_sentence_count / total_sentences
                    progress = min(progress, 1.0)

                    logger.info(
                        "Streaming progress: %d/%d sentences (%.0f%%)",
                        current_sentence_count,
                        total_sentences,
                        progress * 100,
                    )

                    # Convert partial response to domain model
                    final_translation = self._convert_to_domain_model(partial_response, source_lang, target_lang)

                    yield (progress, final_translation)
                    last_sentence_count = current_sentence_count

        # Ensure we yield final result with 100% progress if not already done
        if final_translation and last_sentence_count < total_sentences:
            logger.debug("Yielding final translation result")
            yield (1.0, final_translation)

        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("STREAMING API RESPONSE COMPLETE")
        logger.info("=" * 60)
        logger.info("Total streaming time: %.2f seconds", elapsed_time)
        if final_translation:
            logger.info("Total sentences: %d", len(final_translation.sentences))
            logger.info("Total word alignments: %d", sum(len(s.word_alignments) for s in final_translation.sentences))
            logger.info("Average time per sentence: %.2f seconds", elapsed_time / len(final_translation.sentences))

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

    def _create_word_alignments(self, response: IWordAlignmentResponse) -> list[WordAlignment]:
        """Create WordAlignment models from AI response model."""
        alignments = []
        for align in response.word_alignments:
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

    def generate_alternatives(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        count: int = 3,
    ) -> list[str]:
        """Generate alternative natural translations for a sentence.

        Args:
            source_text: Original sentence to translate
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)
            count: Number of alternative translations to generate (default: 3)

        Returns:
            List of natural translation alternatives

        Raises:
            Exception: If generation fails
        """
        agent = Agent(
            model=self._agent.model,
            output_type=AlternativesResponse,
            system_prompt="You are a language translation expert providing multiple translation alternatives.",
        )

        prompt = create_alternatives_prompt(source_text, source_lang, target_lang, count)
        result = agent.run_sync(prompt)

        return result.output.alternatives

    def regenerate_alignment(
        self,
        source_text: str,
        natural_translation: str,
        source_lang: str,
        target_lang: str,
    ) -> list[WordAlignment]:
        """Generate word-by-word alignment based on given natural translation.

        Args:
            source_text: Original sentence
            natural_translation: Natural translation (chosen by user)
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of WordAlignment objects mapping source words to target words

        Raises:
            Exception: If alignment generation fails
        """
        agent = Agent(
            model=self._agent.model,
            output_type=AlignmentResponse,
            system_prompt=BIRKENBIHL_SYSTEM_PROMPT,
        )

        prompt = create_regenerate_alignment_prompt(source_text, natural_translation, source_lang, target_lang)
        result = agent.run_sync(prompt)

        alignments = self._create_word_alignments(result.output)
        return alignments
