"""Word aligner protocol: the word-by-word step of the Birkenbihl translation."""

from typing import Protocol

from birkenbihl.models.languages import Language
from birkenbihl.models.translation import Sentence


class IWordAligner(Protocol):
    """Aligns the words of a sentence with the words of its natural translation.

    Implementations are interchangeable (language model, Jev), see specs/ALIGNMENT_QUALITY.md.
    """

    def align(
        self, source_text: str, natural_translation: str, source_lang: Language, target_lang: Language
    ) -> Sentence:
        """Returns the sentence with one alignment per source token; uncertain alignments are FLAGGED."""
        ...
