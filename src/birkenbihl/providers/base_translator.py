"""Base translation provider using PydanticAI.

Provides common translation logic shared across OpenAI, Anthropic, and other providers.
"""

import datetime
import logging
import os
import time

from pydantic_ai import Agent
from pydantic_ai.models import Model

from birkenbihl.models.languages import Language
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.protocols import IWordAligner
from birkenbihl.providers.llm_aligner import LLMAligner
from birkenbihl.providers.models import NaturalTranslationResponse
from birkenbihl.providers.prompts import NATURAL_TRANSLATION_SYSTEM_PROMPT, create_natural_translation_prompt
from birkenbihl.utils.text_extractor import split_into_sentences

logger = logging.getLogger(__name__)

# pydantic-ai prints an advertising banner on the first run; it would land in the middle of CLI output
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")


class BaseTranslator:
    """Base translator using PydanticAI for structured outputs.

    Provides common functionality for translation providers:
    - Structured translation using PydanticAI Agent
    - Response model → Domain model conversion

    Follows Dependency Inversion Principle: depends on PydanticAI Model abstraction,
    not concrete provider implementations.
    """

    def __init__(self, model: Model, aligner: IWordAligner | None = None):
        """Initialize translator with PydanticAI model.

        Args:
            model: PydanticAI Model instance (OpenAIModel, AnthropicModel, etc.) for the natural translation
            aligner: Word-by-word step; defaults to the same language model (LLMAligner)
        """
        self._model = model
        self._aligner = aligner or LLMAligner(model)

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

            sentence = self._aligner.align(nat_sent.source_text, nat_sent.natural_translation, source_lang, target_lang)
            if sentence.needs_review():
                logger.warning("Sentence %d needs review: uncertain or incomplete word alignment", idx)
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
        return self._aligner.align(source_text, natural_translation, source_lang, target_lang).word_alignments
