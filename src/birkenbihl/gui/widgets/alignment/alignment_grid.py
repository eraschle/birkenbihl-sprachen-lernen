"""Alignment grid widget with interleaved layout."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QWidget

from birkenbihl.gui.widgets.alignment.alignment_column import AlignmentColumn


class AlignmentGrid(QWidget):
    """Interleaved grid of alignment columns.

    Each column represents one source word with vertically stacked target words.
    Columns arranged horizontally with scroll support for many words.

    Signals:
        grid_changed(): Emitted when any column changes
        validation_needed(): Emitted after user interaction
        word_moved(str, int, int): Word moved from one column to another (word, from_col, to_col)
    """

    grid_changed = Signal()
    validation_needed = Signal()
    word_moved = Signal(str, int, int)

    def __init__(self, parent: QWidget | None = None):
        """Initialize alignment grid.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._columns: list[AlignmentColumn] = []
        self._current_dragged_word: str | None = None
        self._dragged_from_column: int | None = None

        self._scroll_area: QScrollArea
        self._grid_container: QWidget
        self._grid_layout: QHBoxLayout

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for horizontal scrolling
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(True)  # type: ignore
        self._scroll_area.setVerticalScrollBarPolicy(False)  # type: ignore

        # Container for grid columns
        self._grid_container = QWidget()
        self._grid_layout = QHBoxLayout(self._grid_container)
        self._grid_layout.setContentsMargins(10, 10, 10, 10)
        self._grid_layout.setSpacing(0)

        self._scroll_area.setWidget(self._grid_container)
        layout.addWidget(self._scroll_area)

    def build_grid(self, source_words: list[str], alignments: dict[int, list[str]]) -> None:
        """Build grid from source words and alignments.

        Args:
            source_words: List of source words (one per column)
            alignments: Dict mapping column index to list of target words
        """
        self.clear_grid()

        for idx, source_word in enumerate(source_words):
            target_words = alignments.get(idx, [])
            self.add_column(source_word, target_words)

        self.grid_changed.emit()

    def add_column(self, source_word: str, target_words: list[str] | None = None) -> None:
        """Add single column to grid.

        Args:
            source_word: Source word for column header
            target_words: Optional list of target words to populate
        """
        column_index = len(self._columns)
        column = AlignmentColumn(source_word, column_index)

        # Connect signals
        column.word_added.connect(self._on_word_added)
        column.word_removed.connect(self._on_word_removed)

        self._columns.append(column)
        self._grid_layout.addWidget(column)

        # Populate with target words if provided
        if target_words:
            for word in target_words:
                column.add_word(word)

    def get_column(self, index: int) -> AlignmentColumn | None:
        """Get column by index.

        Args:
            index: Column index

        Returns:
            AlignmentColumn or None if out of range
        """
        if 0 <= index < len(self._columns):
            return self._columns[index]
        return None

    def clear_grid(self) -> None:
        """Remove all columns."""
        for column in self._columns:
            self._grid_layout.removeWidget(column)
            column.deleteLater()

        self._columns.clear()
        self.grid_changed.emit()

    def get_alignments(self) -> dict[int, list[str]]:
        """Extract current alignments as dict.

        Returns:
            Dict mapping column index to list of target words
        """
        alignments: dict[int, list[str]] = {}
        for idx, column in enumerate(self._columns):
            words = column.get_words()
            if words:
                alignments[idx] = words
        return alignments

    def get_empty_columns(self) -> list[int]:
        """Get indices of empty columns.

        Returns:
            List of column indices that have no words
        """
        return [idx for idx, col in enumerate(self._columns) if col.is_empty()]

    def set_all_drop_zones_active(self, active: bool) -> None:
        """Show/hide all drop zones during drag.

        Args:
            active: True to show, False to hide
        """
        for column in self._columns:
            column.set_drop_zone_active(active)

    def _on_word_added(self, word: str, column_index: int) -> None:
        """Handle word added to column.

        Args:
            word: Word that was added
            column_index: Column it was added to
        """
        # If this was a move operation, remove from source column
        if self._dragged_from_column is not None and self._dragged_from_column != column_index:
            source_column = self.get_column(self._dragged_from_column)
            if source_column:
                source_column.remove_word(word)
                self.word_moved.emit(word, self._dragged_from_column, column_index)

        self._dragged_from_column = None
        self._current_dragged_word = None

        self.grid_changed.emit()
        self.validation_needed.emit()

    def _on_word_removed(self, word: str, column_index: int) -> None:
        """Handle word removed from column.

        Args:
            word: Word that was removed
            column_index: Column it was removed from
        """
        # Track which column word came from for move operations
        self._dragged_from_column = column_index
        self._current_dragged_word = word

        self.grid_changed.emit()
        self.validation_needed.emit()

    def get_source_words(self) -> list[str]:
        """Get all source words in order.

        Returns:
            List of source words
        """
        return [col.get_source_word() for col in self._columns]

    def validate(self) -> tuple[bool, list[str]]:
        """Validate current grid state.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []
        empty_indices = self.get_empty_columns()

        if empty_indices:
            empty_words = [self._columns[idx].get_source_word() for idx in empty_indices]
            errors.append(f"{len(empty_indices)} columns empty: {', '.join(empty_words)}")

        for idx in empty_indices:
            self._columns[idx].set_error_state(True)

        # Clear error state for non-empty columns
        for idx, col in enumerate(self._columns):
            if idx not in empty_indices:
                col.set_error_state(False)

        return (len(errors) == 0, errors)
