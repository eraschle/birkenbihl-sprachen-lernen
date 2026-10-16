"""Base translation provider using PydanticAI.

Provides common translation logic shared across OpenAI, Anthropic, and other providers.
"""

import datetime
import logging
import time
from collections.abc import AsyncIterator

from langdetect import detector_factory
from pydantic_ai import Agent
from pydantic_ai.models import Model

from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.languages import Language
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.providers.models import AlignmentResponse, AlternativesResponse, NaturalTranslationResponse
from birkenbihl.providers.prompts import (
    BIRKENBIHL_SYSTEM_PROMPT,
    NATURAL_TRANSLATION_SYSTEM_PROMPT,
    create_alternatives_prompt,
    create_natural_translation_prompt,
    create_regenerate_alignment_prompt,
    create_word_by_word_prompt,
)
from birkenbihl.utils.text_extractor import split_into_sentences

logger = logging.getLogger(__name__)


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
        self._model = model

    def _generate_natural_translations(
        self, sentences: list[str], source_lang: Language, target_lang: Language
    ) -> NaturalTranslationResponse:
        """Generate natural translations (Step 1 of two-step process).

        Args:
            sentences: List of sentences to translate
            source_lang: Source language
            target_lang: Target language

        Returns:
            NaturalTranslationResponse with natural translations only
        """
        agent = Agent(
            model=self._model,
            output_type=NaturalTranslationResponse,
            system_prompt=NATURAL_TRANSLATION_SYSTEM_PROMPT,
        )

        prompt = create_natural_translation_prompt(sentences, source_lang, target_lang)
        logger.debug("Step 1: Generating natural translations")
        result = agent.run_sync(prompt)
        logger.info("Step 1 complete: %d natural translations generated", len(result.output.sentences))
        return result.output

    def _generate_aligned_sentence(
        self, source_text: str, natural_translation: str, source_lang: Language, target_lang: Language
    ) -> Sentence:
        """Generate word alignments for a single sentence (Step 2).

        Args:
            source_text: Original sentence
            natural_translation: Natural translation from Step 1
            source_lang: Source language
            target_lang: Target language

        Returns:
            Sentence whose alignments reference token positions; AI pairs that do not match are FLAGGED
        """
        source_words = source_text.split()
        target_words = natural_translation.split()

        agent = Agent(
            model=self._model,
            output_type=AlignmentResponse,
            system_prompt=BIRKENBIHL_SYSTEM_PROMPT,
        )

        prompt = create_word_by_word_prompt(source_words, target_words, source_lang, target_lang)
        result = agent.run_sync(prompt)

        return align_word_pairs(source_text, natural_translation, self._word_pairs(result.output))

    def _generate_all_alignments(
        self, natural_response: NaturalTranslationResponse, source_lang: Language, target_lang: Language
    ) -> list[Sentence]:
        """Generate word alignments for all sentences (Step 2 orchestration).

        Args:
            natural_response: Natural translations from Step 1
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of complete Sentence objects with alignments
        """
        logger.debug("Step 2: Generating word alignments for %d sentences", len(natural_response.sentences))
        sentences = []

        for idx, nat_sent in enumerate(natural_response.sentences, 1):
            logger.debug("Generating alignments for sentence %d/%d", idx, len(natural_response.sentences))

            sentence = self._generate_aligned_sentence(
                nat_sent.source_text, nat_sent.natural_translation, source_lang, target_lang
            )
            if sentence.needs_review():
                logger.warning("Sentence %d needs review: AI alignment did not match the sentence", idx)
            sentences.append(sentence)

        logger.info("Step 2 complete: %d sentences with alignments", len(sentences))
        return sentences

    def translate(
        self, text: str, source_lang: Language, target_lang: Language, title: str | None = None
    ) -> Translation:
        """Translate text using Birkenbihl method (two-step process).

        Args:
            text: Text to translate (can contain multiple sentences)
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)
            title: Optional title for the translation

        Returns:
            Translation with natural and word-by-word translations

        Raises:
            Exception: If translation fails
        """
        sentences = split_into_sentences(text)
        logger.info("Split text into %d sentences", len(sentences))
        logger.info("=" * 60)
        logger.info("TWO-STEP TRANSLATION START")
        logger.info("=" * 60)
        logger.info("Model: %s", self._model)
        logger.info("Source: %s → Target: %s", source_lang, target_lang)

        start_time = time.time()

        # Step 1: Generate natural translations
        natural_response = self._generate_natural_translations(sentences, source_lang, target_lang)

        # Step 2: Generate word alignments
        complete_sentences = self._generate_all_alignments(natural_response, source_lang, target_lang)

        # Create Translation domain model
        now = datetime.datetime.now(datetime.UTC)
        translation_title = title if title else "Übersetzung"
        translation_title = translation_title[:50] + ("..." if len(translation_title) > 50 else "")

        translation = Translation(
            title=translation_title,
            source_language=source_lang,
            target_language=target_lang,
            sentences=complete_sentences,
            created_at=now,
            updated_at=now,
        )

        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("TWO-STEP TRANSLATION COMPLETE")
        logger.info("=" * 60)
        logger.info("Total time: %.2f seconds", elapsed_time)
        total_alignments = sum(len(s.word_alignments) for s in translation.sentences)
        logger.info("Sentences: %d, Word alignments: %d", len(translation.sentences), total_alignments)

        return translation

    async def translate_stream(
        self, text: str, source_lang: Language, target_lang: Language
    ) -> AsyncIterator[tuple[float, Translation | None]]:
        """Translate text using two-step method with streaming progress.

        Step 1 (Natural Translation): 0% → 50%
        Step 2 (Word Alignments): 50% → 100%

        Args:
            text: Text to translate (can contain multiple sentences)
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Yields:
            Tuple of (progress: float, translation: Translation | None)

        Raises:
            Exception: If translation fails
        """
        sentences = split_into_sentences(text)
        logger.info("Starting two-step streaming translation: %d sentences", len(sentences))

        start_time = time.time()

        # Step 1: Natural translations (0% → 50%)
        yield (0.0, None)
        natural_response = self._generate_natural_translations(sentences, source_lang, target_lang)
        yield (0.5, None)

        # Step 2: Word alignments (50% → 100%)
        complete_sentences = self._generate_all_alignments(natural_response, source_lang, target_lang)

        # Create final Translation
        now = datetime.datetime.now(datetime.UTC)
        translation = Translation(
            title="Übersetzung",
            source_language=source_lang,
            target_language=target_lang,
            sentences=complete_sentences,
            created_at=now,
            updated_at=now,
        )

        yield (1.0, translation)

        elapsed_time = time.time() - start_time
        logger.info("Streaming complete: %.2f seconds", elapsed_time)

    def detect_language(self, text: str) -> Language:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language object

        Raises:
            langdetect.LangDetectException: If detection fails
            KeyError: If detected language is not supported
        """
        from birkenbihl.services.language_service import get_language_by

        # Use langdetect library for language detection
        code = detector_factory.detect(text)
        return get_language_by(code)

    @staticmethod
    def _word_pairs(response: AlignmentResponse) -> list[tuple[str, str]]:
        ordered = sorted(response.word_alignments, key=lambda alignment: alignment.position)
        return [(alignment.source_word, alignment.target_word) for alignment in ordered]

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

        Raises:
            Exception: If generation fails
        """
        agent = Agent(
            model=self._model,
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
        source_lang: Language,
        target_lang: Language,
    ) -> list[WordAlignment]:
        """Generate word-by-word alignment based on given natural translation.

        Args:
            source_text: Original sentence
            natural_translation: Natural translation (chosen by user)
            source_lang: Source language
            target_lang: Target language

        Returns:
            Alignments referencing token positions of source_text and natural_translation;
            AI pairs that do not match the sentence are FLAGGED

        Raises:
            Exception: If alignment generation fails
        """
        agent = Agent(
            model=self._model,
            output_type=AlignmentResponse,
            system_prompt=BIRKENBIHL_SYSTEM_PROMPT,
        )

        prompt = create_regenerate_alignment_prompt(source_text, natural_translation, source_lang, target_lang)
        result = agent.run_sync(prompt)

        return align_word_pairs(source_text, natural_translation, self._word_pairs(result.output)).word_alignments
