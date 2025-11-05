"""ViewModel for word alignment editor."""

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from birkenbihl.gui.viewmodels.base import BaseViewModel
from birkenbihl.models.translation import Sentence, WordAlignment


@dataclass
class AlignmentState:
    """Current state of alignment editor."""

    source_words: list[str]
    assigned_words: dict[int, list[str]]  # column_index -> words
    unassigned_words: list[str]
    is_valid: bool
    validation_errors: list[str]
    is_dirty: bool  # Has unsaved changes


class AlignmentEditorViewModel(BaseViewModel):
    """ViewModel for word alignment editor.

    Manages state for mapping target words to source words.
    Follows MVVM pattern with Qt signals for view updates.

    Signals (inherited from BaseViewModel):
        error_occurred(str)
        loading_changed(bool)

    New Signals:
        alignment_changed()
        validation_changed(bool, list[str])
        state_changed(AlignmentState)
    """

    alignment_changed = Signal()
    validation_changed = Signal(bool, list)
    state_changed = Signal(object)

    def __init__(self, parent: QObject | None = None):
        """Initialize ViewModel.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._sentence: Sentence | None = None
        self._original_alignments: list[WordAlignment] = []
        self._state = AlignmentState(
            source_words=[],
            assigned_words={},
            unassigned_words=[],
            is_valid=False,
            validation_errors=[],
            is_dirty=False,
        )

    def load_sentence(self, sentence: Sentence) -> None:
        """Load sentence and initialize alignment state.

        Args:
            sentence: Sentence with existing word alignments
        """
        self._sentence = sentence
        self._original_alignments = sentence.word_alignments.copy()

        # Tokenize source and target texts
        source_words = sentence.source_text.split()
        target_words = sentence.natural_translation.split()

        # Build assigned_words dict from existing alignments
        assigned_words: dict[int, list[str]] = {}
        used_target_words: set[str] = set()

        for alignment in sentence.word_alignments:
            position = alignment.position
            target_word = alignment.target_word

            if position not in assigned_words:
                assigned_words[position] = []

            # Handle hyphenated words (e.g., "werde-vermissen")
            if "-" in target_word:
                parts = target_word.split("-")
                assigned_words[position].extend(parts)
                used_target_words.update(parts)
            else:
                assigned_words[position].append(target_word)
                used_target_words.add(target_word)

        # Find unassigned words
        unassigned_words = [w for w in target_words if w not in used_target_words]

        # Update state
        self._state = AlignmentState(
            source_words=source_words,
            assigned_words=assigned_words,
            unassigned_words=unassigned_words,
            is_valid=len(unassigned_words) == 0,
            validation_errors=[],
            is_dirty=False,
        )

        self._emit_state_changed()
        self.validate()

    def assign_word(self, word: str, column_index: int) -> None:
        """Assign target word to source word column.

        Args:
            word: Target word to assign
            column_index: Column index (0-indexed)
        """
        # Remove from unassigned if present
        if word in self._state.unassigned_words:
            self._state.unassigned_words.remove(word)

        # Add to assigned column
        if column_index not in self._state.assigned_words:
            self._state.assigned_words[column_index] = []
        self._state.assigned_words[column_index].append(word)

        self._state.is_dirty = True
        self._emit_state_changed()
        self.validate()

    def unassign_word(self, word: str, column_index: int) -> None:
        """Remove target word from column.

        Args:
            word: Target word to remove
            column_index: Column index to remove from
        """
        if column_index in self._state.assigned_words:
            if word in self._state.assigned_words[column_index]:
                self._state.assigned_words[column_index].remove(word)

                # Remove column entry if now empty
                if not self._state.assigned_words[column_index]:
                    del self._state.assigned_words[column_index]

        # Add back to unassigned
        if word not in self._state.unassigned_words:
            self._state.unassigned_words.append(word)

        self._state.is_dirty = True
        self._emit_state_changed()
        self.validate()

    def validate(self) -> tuple[bool, list[str]]:
        """Validate current alignment state.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        # Check all source words have assignments
        for idx in range(len(self._state.source_words)):
            if idx not in self._state.assigned_words or not self._state.assigned_words[idx]:
                source_word = self._state.source_words[idx]
                errors.append(f"'{source_word}' has no translation")

        # Check unassigned pool is empty
        if self._state.unassigned_words:
            count = len(self._state.unassigned_words)
            errors.append(f"{count} words not assigned")

        is_valid = len(errors) == 0
        self._state.is_valid = is_valid
        self._state.validation_errors = errors

        self.validation_changed.emit(is_valid, errors)
        return (is_valid, errors)

    def to_word_alignments(self) -> list[WordAlignment]:
        """Convert current state to WordAlignment domain models.

        Returns:
            List of WordAlignment objects
        """
        alignments: list[WordAlignment] = []

        for position, words in self._state.assigned_words.items():
            if position >= len(self._state.source_words):
                continue

            source_word = self._state.source_words[position]

            # Join multiple words with hyphens
            target_word = "-".join(words) if len(words) > 1 else words[0]

            alignment = WordAlignment(
                source_word=source_word, target_word=target_word, position=position
            )
            alignments.append(alignment)

        return alignments

    def reset(self) -> None:
        """Reset to original alignment from sentence."""
        if self._sentence:
            self.load_sentence(self._sentence)

    def get_state(self) -> AlignmentState:
        """Get current state.

        Returns:
            Current AlignmentState
        """
        return self._state

    def _emit_state_changed(self) -> None:
        """Emit state changed signal."""
        self.state_changed.emit(self._state)
        self.alignment_changed.emit()
