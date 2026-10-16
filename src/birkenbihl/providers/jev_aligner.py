"""Word-by-word alignment by Jev (TypeSafe), a decision model that answers yes/no questions with probabilities.

Jev writes no text. For every pair of source word and target word it is asked how likely the target word translates
the source word, all in one request per sentence. Distributing the target words by these probabilities is
done in code (align_by_probability), so every word of the natural translation is used exactly once.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field, create_model
from pydantic_ai import Agent
from pydantic_ai.models import Model

from birkenbihl.models.alignment import align_by_probability
from birkenbihl.models.languages import Language
from birkenbihl.models.translation import Sentence

logger = logging.getLogger(__name__)


class JevAligner:
    """Aligns words from Jev's probability for every source/target word pair."""

    def __init__(self, model: Model):
        self._model = model

    def align(
        self, source_text: str, natural_translation: str, source_lang: Language, target_lang: Language
    ) -> Sentence:
        """Raises ModelAPIError/ModelHTTPError if Jev cannot be reached."""
        sentence = Sentence(source_text=source_text, natural_translation=natural_translation, word_alignments=[])
        source_tokens, target_tokens = sentence.source_tokens, sentence.target_tokens
        agent = Agent(
            self._model,
            output_type=_question_model(source_tokens, target_tokens, source_lang, target_lang),
            instructions=(
                f"Word-by-word alignment (Birkenbihl decoding) of a {source_lang.name_en} sentence "
                f"and its {target_lang.name_en} translation."
            ),
        )
        state = f"{source_lang.name_en}: {source_text}\n{target_lang.name_en}: {natural_translation}"
        result = agent.run_sync(state)
        answers = result.output.model_dump()
        probabilities = [
            [answers[_field_name(source, target)] for target in range(len(target_tokens))]
            for source in range(len(source_tokens))
        ]
        logger.debug("Jev alignment for %r: %s", source_text, probabilities)
        return align_by_probability(source_text, natural_translation, probabilities)


def _field_name(source_index: int, target_index: int) -> str:
    return f"source_{source_index + 1}_target_{target_index + 1}"


def _question_model(
    source_tokens: list[str], target_tokens: list[str], source_lang: Language, target_lang: Language
) -> type[BaseModel]:
    """One probability (0-1) per source/target word pair, positions included so repeated words stay distinct."""
    fields: dict[str, Any] = {
        _field_name(source_index, target_index): (
            float,
            Field(
                ge=0,
                le=1,
                description=(
                    f"Probability that the {target_lang.name_en} word '{target}' (word {target_index + 1}) "
                    f"translates the {source_lang.name_en} word '{source}' (word {source_index + 1})"
                ),
            ),
        )
        for source_index, source in enumerate(source_tokens)
        for target_index, target in enumerate(target_tokens)
    }
    return create_model("WordAlignmentQuestions", **fields)
