"""Grid state model for managing interleaved grid UI state."""

from dataclasses import dataclass, field

from birkenbihl.models.translation import Sentence, WordAlignment
from birkenbihl.utils.text_extractor import split_hyphenated, tokenize_clean


@dataclass
class ColumnState:
    """State for a single grid column."""

    source_word: str
    assigned_words: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if column has no assigned words.

        Returns:
            True if no words assigned
        """
        return len(self.assigned_words) == 0


@dataclass
class GridState:
    """Complete grid state for UI management."""

    columns: list[ColumnState] = field(default_factory=list)
    unassigned_words: list[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if all columns have at least one word.

        Returns:
            True if valid (all columns non-empty)
        """
        return all(not col.is_empty() for col in self.columns)

    def get_error_columns(self) -> list[str]:
        """Get list of empty column source words.

        Returns:
            List of source words with no assignments
        """
        return [col.source_word for col in self.columns if col.is_empty()]

    def to_word_alignments(self) -> list[WordAlignment]:
        """Convert grid state to word alignment list.

        Returns:
            List of word alignments
        """
        alignments = []
        for position, column in enumerate(self.columns):
            for word in column.assigned_words:
                alignment = WordAlignment(
                    source_word=column.source_word,
                    target_word=word,
                    position=position
                )
                alignments.append(alignment)
        return alignments


def build_grid_state(sentence: Sentence) -> GridState:
    """Build grid state from sentence (Domain → UI conversion).

    Args:
        sentence: Sentence with word alignments

    Returns:
        Grid state for UI rendering
    """
    source_words = tokenize_clean(sentence.source_text)
    sorted_alignments = sorted(sentence.word_alignments, key=lambda a: a.position)

    columns = _build_columns(source_words, sorted_alignments)
    unassigned = _find_unassigned_words(sentence, columns)

    return GridState(columns=columns, unassigned_words=unassigned)


def _build_columns(
    source_words: list[str],
    alignments: list[WordAlignment]
) -> list[ColumnState]:
    """Build column states from alignments.

    Args:
        source_words: List of source words
        alignments: Sorted word alignments

    Returns:
        List of column states
    """
    columns = []
    for source_word in source_words:
        target_words = _get_target_words(source_word, alignments)
        columns.append(ColumnState(source_word, target_words))
    return columns


def _get_target_words(
    source_word: str,
    alignments: list[WordAlignment]
) -> list[str]:
    """Get target words for source word from alignments.

    Args:
        source_word: Source word to find
        alignments: Word alignments

    Returns:
        List of target words (hyphenated words split)
    """
    target_words = []
    for alignment in alignments:
        if alignment.source_word == source_word:
            parts = split_hyphenated(alignment.target_word)
            target_words.extend(parts)
    return target_words


def _find_unassigned_words(
    sentence: Sentence,
    columns: list[ColumnState]
) -> list[str]:
    """Find words in natural translation not assigned to any column.

    Args:
        sentence: Original sentence
        columns: Column states

    Returns:
        List of unassigned words
    """
    all_target = set(tokenize_clean(sentence.natural_translation))
    assigned = {word for col in columns for word in col.assigned_words}
    return list(all_target - assigned)
