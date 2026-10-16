"""Base translation provider using PydanticAI.

Provides common translation logic shared across OpenAI, Anthropic, and other providers.
"""

import datetime
import logging
import os
import time

from pydantic_ai import Agent, ModelRetry
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models import Model

from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.languages import Language
from birkenbihl.models.translation import AlignmentStatus, Sentence, Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.providers.models import AlignmentResponse, NaturalTranslationResponse
from birkenbihl.providers.prompts import (
    BIRKENBIHL_SYSTEM_PROMPT,
    NATURAL_TRANSLATION_SYSTEM_PROMPT,
    create_natural_translation_prompt,
    create_word_by_word_prompt,
)
from birkenbihl.utils.text_extractor import split_into_sentences

logger = logging.getLogger(__name__)

# pydantic-ai prints an advertising banner on the first run; it would land in the middle of CLI output
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

# Extra attempts the model gets to fix an alignment that breaks the Birkenbihl rules
ALIGNMENT_RETRIES = 2


class BaseTranslator:
    """Base translator using PydanticAI for structured outputs.

    Provides common functionality for translation providers:
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

    def _align(
        self, source_text: str, natural_translation: str, source_lang: Language, target_lang: Language
    ) -> Sentence:
        """Generate the word-by-word alignment for one sentence, letting the model correct its mistakes.

        Every answer is matched to the sentence's tokens and checked against the Birkenbihl rules. A broken
        answer goes back to the model with the concrete problems (ModelRetry). If it is still broken after
        ALIGNMENT_RETRIES corrections, the last attempt is returned with its problems FLAGGED for the user.

        Returns:
            Sentence whose alignments reference token positions
        """
        attempts: list[Sentence] = []
        agent = Agent(
            model=self._model,
            output_type=AlignmentResponse,
            system_prompt=BIRKENBIHL_SYSTEM_PROMPT,
            retries=ALIGNMENT_RETRIES,
        )

        @agent.output_validator
        def check_birkenbihl_rules(output: AlignmentResponse) -> AlignmentResponse:
            sentence = align_word_pairs(source_text, natural_translation, self._word_pairs(output))
            attempts.append(sentence)
            problems = _alignment_problems(sentence)
            if problems:
                logger.info("Alignment attempt %d rejected: %s", len(attempts), problems)
                raise ModelRetry(problems)
            return output

        sentence = Sentence(source_text=source_text, natural_translation=natural_translation, word_alignments=[])
        prompt = create_word_by_word_prompt(sentence.source_tokens, sentence.target_tokens, source_lang, target_lang)
        try:
            agent.run_sync(prompt)
        except UnexpectedModelBehavior:
            if not attempts:
                raise
            logger.warning("Alignment still broken after %d attempts, flagged for review", len(attempts))
        return attempts[-1]

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

            sentence = self._align(nat_sent.source_text, nat_sent.natural_translation, source_lang, target_lang)
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

    @staticmethod
    def _word_pairs(response: AlignmentResponse) -> list[tuple[str, str]]:
        ordered = sorted(response.word_alignments, key=lambda alignment: alignment.position)
        return [(alignment.source_word, alignment.target_word) for alignment in ordered]

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
        return self._align(source_text, natural_translation, source_lang, target_lang).word_alignments


def _alignment_problems(sentence: Sentence) -> str | None:
    """Feedback for the model if its alignment breaks the rules, None if it is acceptable."""
    is_valid, error = validate_alignment_complete(sentence)
    if not is_valid:
        return f"The word-by-word alignment breaks the Birkenbihl rules: {error}"
    flagged = [sentence.source_word(a) for a in sentence.word_alignments if a.status == AlignmentStatus.FLAGGED]
    if flagged:
        words = ", ".join(flagged)
        return f"The targets for {words} contain words that are not in the natural translation. Use only its words."
    return None
