"""Grid state model for the editable interleaved grid (word alignment editor).

Words are identified by their position in the natural translation, so repeated words
("der Hund und der Mann") can be moved independently.
"""

from dataclasses import dataclass, field

from birkenbihl.models.translation import AlignmentStatus, Sentence, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete


@dataclass
class ColumnState:
    """One source word and the target words assigned to it."""

    source_index: int
    source_word: str
    target_indices: list[int] = field(default_factory=list)
    status: AlignmentStatus = AlignmentStatus.SUGGESTED

    def is_empty(self) -> bool:
        return not self.target_indices

    def is_flagged(self) -> bool:
        return self.status == AlignmentStatus.FLAGGED


@dataclass
class GridState:
    """Editable state of one sentence's word-by-word alignment."""

    sentence: Sentence
    columns: list[ColumnState] = field(default_factory=list)
    unassigned: list[int] = field(default_factory=list)

    def target_word(self, target_index: int) -> str:
        return self.sentence.target_tokens[target_index]

    def move(self, target_index: int, to_column: int | None) -> None:
        """Move a target word into a column, or into the unassigned pool when to_column is None.

        Columns the user changes count as reviewed and become CONFIRMED.
        """
        self._take(target_index)
        if to_column is None:
            self.unassigned.append(target_index)
            return
        column = self.columns[to_column]
        column.target_indices.append(target_index)
        column.status = AlignmentStatus.CONFIRMED

    def _take(self, target_index: int) -> None:
        if target_index in self.unassigned:
            self.unassigned.remove(target_index)
            return
        for column in self.columns:
            if target_index in column.target_indices:
                column.target_indices.remove(target_index)
                column.status = AlignmentStatus.CONFIRMED
                return

    def to_word_alignments(self) -> list[WordAlignment]:
        return [
            WordAlignment(source_index=c.source_index, target_indices=list(c.target_indices), status=c.status)
            for c in self.columns
        ]

    def validate(self) -> tuple[bool, str | None]:
        """Same Birkenbihl rules as TranslationService applies when saving."""
        edited = self.sentence.model_copy(update={"word_alignments": self.to_word_alignments()})
        return validate_alignment_complete(edited)


def build_grid_state(sentence: Sentence) -> GridState:
    """Build grid state from sentence (Domain → UI conversion), one column per source word."""
    by_source = {alignment.source_index: alignment for alignment in sentence.word_alignments}
    columns = [_column(index, word, by_source.get(index)) for index, word in enumerate(sentence.source_tokens)]
    return GridState(sentence=sentence, columns=columns, unassigned=sentence.unassigned_target_indices())


def _column(source_index: int, source_word: str, alignment: WordAlignment | None) -> ColumnState:
    if alignment is None:
        return ColumnState(source_index, source_word, status=AlignmentStatus.FLAGGED)
    return ColumnState(source_index, source_word, list(alignment.target_indices), alignment.status)
