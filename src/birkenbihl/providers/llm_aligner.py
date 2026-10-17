"""Word-by-word alignment by a language model that corrects its own mistakes."""

import logging

from pydantic_ai import Agent, ModelRetry
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models import Model

from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.languages import Language
from birkenbihl.models.translation import AlignmentStatus, Sentence
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.providers.models import AlignmentResponse
from birkenbihl.providers.prompts import BIRKENBIHL_SYSTEM_PROMPT, create_word_by_word_prompt

logger = logging.getLogger(__name__)

# Extra attempts the model gets to fix an alignment that breaks the Birkenbihl rules
ALIGNMENT_RETRIES = 2


class LLMAligner:
    """Asks a language model for word pairs and matches them to the sentence's tokens."""

    def __init__(self, model: Model):
        self._model = model

    def align(
        self, source_text: str, natural_translation: str, source_lang: Language, target_lang: Language
    ) -> Sentence:
        """Generate the word-by-word alignment for one sentence, letting the model correct its mistakes.

        Every answer is matched to the sentence's tokens and checked against the Birkenbihl rules. A broken
        answer goes back to the model with the concrete problems (ModelRetry). If it is still broken after
        ALIGNMENT_RETRIES corrections, the last attempt is returned with its problems FLAGGED for the user.
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
            sentence = align_word_pairs(source_text, natural_translation, _word_pairs(output))
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


def _word_pairs(response: AlignmentResponse) -> list[tuple[str, str]]:
    ordered = sorted(response.word_alignments, key=lambda alignment: alignment.position)
    return [(alignment.source_word, alignment.target_word) for alignment in ordered]


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
