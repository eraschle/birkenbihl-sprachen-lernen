"""Grid state model for the editable interleaved grid (word alignment editor).

Words are identified by their position in the sentence, so repeated words ("der Hund und der Mann") can be
moved independently. A column holds one or more neighbouring source words; the user can join a column with
its neighbour when several source words share one target word ("estación de tren" → "Bahnhof").
"""

from dataclasses import dataclass, field

from birkenbihl.models.translation import SOURCE_JOINER, AlignmentStatus, Sentence, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete


@dataclass
class ColumnState:
    """Source words of one column and the target words assigned to them."""

    source_indices: list[int]
    source_word: str  # shown in the header, e.g. "estación-de-tren"
    target_indices: list[int] = field(default_factory=list)
    status: AlignmentStatus = AlignmentStatus.SUGGESTED

    def is_empty(self) -> bool:
        return not self.target_indices

    def is_flagged(self) -> bool:
        return self.status == AlignmentStatus.FLAGGED

    def is_joined(self) -> bool:
        return len(self.source_indices) > 1


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

    def confirm(self, column_index: int) -> None:
        """Mark a column as reviewed without changing it (e.g. a flagged AI suggestion that is correct).

        Empty columns cannot be confirmed: they still need a target word.
        """
        column = self.columns[column_index]
        if not column.is_empty():
            column.status = AlignmentStatus.CONFIRMED

    def join(self, column_index: int, neighbour_index: int) -> None:
        """Join two neighbouring columns: their source words share their target words."""
        if abs(column_index - neighbour_index) != 1 or not 0 <= neighbour_index < len(self.columns):
            raise ValueError(f"Columns {column_index} and {neighbour_index} are not neighbours")
        left, right = sorted((column_index, neighbour_index))
        first, second = self.columns[left], self.columns[right]
        joined = self._new_column(first.source_indices + second.source_indices)
        joined.target_indices = first.target_indices + second.target_indices
        self.columns[left : right + 1] = [joined]

    def split(self, column_index: int) -> None:
        """Give every source word of a joined column its own column; the first keeps the target words."""
        column = self.columns[column_index]
        parts = [self._new_column([source]) for source in column.source_indices]
        parts[0].target_indices = column.target_indices
        self.columns[column_index : column_index + 1] = parts

    def _new_column(self, source_indices: list[int]) -> ColumnState:
        tokens = self.sentence.source_tokens
        word = SOURCE_JOINER.join(tokens[index] for index in source_indices)
        return ColumnState(source_indices, word, status=AlignmentStatus.CONFIRMED)

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
            WordAlignment(source_indices=list(c.source_indices), target_indices=list(c.target_indices), status=c.status)
            for c in self.columns
        ]

    def validate(self) -> tuple[bool, str | None]:
        """Same Birkenbihl rules as TranslationService applies when saving."""
        edited = self.sentence.model_copy(update={"word_alignments": self.to_word_alignments()})
        return validate_alignment_complete(edited)


def build_grid_state(sentence: Sentence) -> GridState:
    """Build grid state from sentence (Domain → UI conversion), columns in source word order.

    Source words that belong to no alignment get their own empty, FLAGGED column.
    """
    columns = [_column(sentence, alignment) for alignment in sentence.sorted_alignments()]
    columns += [
        ColumnState([index], sentence.source_tokens[index], status=AlignmentStatus.FLAGGED)
        for index in sentence.unassigned_source_indices()
    ]
    columns.sort(key=lambda column: min(column.source_indices, default=-1))
    return GridState(sentence=sentence, columns=columns, unassigned=sentence.unassigned_target_indices())


def _column(sentence: Sentence, alignment: WordAlignment) -> ColumnState:
    return ColumnState(
        list(alignment.source_indices),
        sentence.source_word(alignment),
        list(alignment.target_indices),
        alignment.status,
    )
