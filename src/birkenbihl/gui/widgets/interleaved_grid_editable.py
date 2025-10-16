"""Editable interleaved grid widget with drag&drop for word alignment editing."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from birkenbihl.gui.models.grid_state import ColumnState, GridState, build_grid_state
from birkenbihl.gui.widgets.grid_column import GridColumn
from birkenbihl.gui.widgets.unassigned_pool import UnassignedPool
from birkenbihl.gui.widgets.word_tag import WordTag
from birkenbihl.models.translation import Sentence


class InterleavedGridEditable(QWidget):
    """Editable interleaved grid with drag&drop for word alignment.

    Layout:
        [Column1] [Column2] [Column3] ...  ← Grid columns
        [Unassigned Pool]                  ← Pool at bottom
        [Error Message]                    ← Validation feedback
    """

    alignments_changed = Signal(list)
    validation_error = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        """Initialize editable grid.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._columns: list[GridColumn] = []
        self._grid_state: GridState | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self._grid_layout = QHBoxLayout()  # type: ignore[reportUninitializedInstanceVariable]
        self._grid_layout.setSpacing(15)
        layout.addLayout(self._grid_layout)

        self._pool = UnassignedPool()  # type: ignore[reportUninitializedInstanceVariable]
        self._pool.word_dropped.connect(self._on_pool_drop)
        layout.addWidget(self._pool)

        self._error_label = QLabel()  # type: ignore[reportUninitializedInstanceVariable]
        self._error_label.setStyleSheet("QLabel { color: #ff0000; }")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._error_label)

    def build_grid(self, sentence: Sentence) -> None:
        """Build grid from sentence word alignments.

        Args:
            sentence: Sentence with word alignments
        """
        self._clear_grid()
        self._grid_state = build_grid_state(sentence)
        self._render_grid()
        self._validate()

    def _clear_grid(self) -> None:
        """Clear all columns and pool."""
        for column in self._columns:
            column.setParent(None)
            column.deleteLater()
        self._columns.clear()

        for tag in self._pool.get_tags():
            self._pool.remove_tag(tag)

    def _render_grid(self) -> None:
        """Render grid from current state."""
        if not self._grid_state:
            return

        self._render_columns()
        self._render_pool()

    def _render_columns(self) -> None:
        """Render grid columns."""
        if not self._grid_state:
            return

        for column_state in self._grid_state.columns:
            column = self._create_column(column_state)
            self._columns.append(column)
            self._grid_layout.addWidget(column)

    def _create_column(self, column_state: ColumnState) -> GridColumn:
        """Create grid column from state.

        Args:
            column_state: Column state data

        Returns:
            Configured grid column
        """
        column = GridColumn(column_state.source_word)
        column.word_dropped.connect(lambda word, col=column: self._on_column_drop(col, word))

        for word in column_state.assigned_words:
            tag = self._create_tag(word)
            column.add_tag(tag)

        return column

    def _render_pool(self) -> None:
        """Render unassigned pool."""
        if not self._grid_state:
            return

        for word in self._grid_state.unassigned_words:
            tag = self._create_tag(word)
            self._pool.add_tag(tag)

    def _create_tag(self, word: str) -> WordTag:
        """Create word tag with event connections.

        Args:
            word: Word text

        Returns:
            Configured word tag
        """
        tag = WordTag(word)
        tag.drag_started.connect(self._on_drag_started)
        tag.drag_ended.connect(self._on_drag_ended)
        return tag

    def _on_drag_started(self) -> None:
        """Handle tag drag start - show drop zones."""
        for column in self._columns:
            column.set_drop_zone_visible(True)

    def _on_drag_ended(self) -> None:
        """Handle tag drag end - hide drop zones."""
        for column in self._columns:
            column.set_drop_zone_visible(False)

    def _on_column_drop(self, column: GridColumn, word: str) -> None:
        """Handle word dropped into column.

        Args:
            column: Target column
            word: Dropped word
        """
        old_tag = self._find_tag_by_word(word)
        if old_tag:
            self._remove_tag_from_current_location(old_tag)
            new_tag = self._create_tag(word)
            column.add_tag(new_tag)
            self._update_state()

    def _on_pool_drop(self, word: str) -> None:
        """Handle word dropped into pool.

        Args:
            word: Dropped word
        """
        old_tag = self._find_tag_by_word(word)
        if old_tag:
            self._remove_tag_from_current_location(old_tag)
            new_tag = self._create_tag(word)
            self._pool.add_tag(new_tag)
            self._update_state()

    def _find_tag_by_word(self, word: str) -> WordTag | None:
        """Find tag by word text.

        Args:
            word: Word to find

        Returns:
            Word tag or None
        """
        for column in self._columns:
            for tag in column.get_tags():
                if tag.get_word() == word:
                    return tag

        for tag in self._pool.get_tags():
            if tag.get_word() == word:
                return tag

        return None

    def _remove_tag_from_current_location(self, tag: WordTag) -> None:
        """Remove tag from its current location.

        Args:
            tag: Tag to remove
        """
        for column in self._columns:
            if tag in column.get_tags():
                column.remove_tag(tag)
                return

        if tag in self._pool.get_tags():
            self._pool.remove_tag(tag)

    def _update_state(self) -> None:
        """Update grid state from UI and emit changes."""
        if not self._grid_state:
            return

        for i, column in enumerate(self._columns):
            words = [tag.get_word() for tag in column.get_tags()]
            self._grid_state.columns[i].assigned_words = words

        pool_words = [tag.get_word() for tag in self._pool.get_tags()]
        self._grid_state.unassigned_words = pool_words

        self._validate()
        alignments = self._grid_state.to_word_alignments()
        self.alignments_changed.emit(alignments)

    def _validate(self) -> bool:
        """Validate grid - all columns must have at least one tag.

        Returns:
            True if valid
        """
        if not self._grid_state:
            return True

        is_valid = self._grid_state.is_valid()
        error_columns = self._grid_state.get_error_columns()

        for column in self._columns:
            is_error = column._source_word in error_columns
            column.set_error_state(is_error)

        if is_valid:
            if hasattr(self, "_error_label") and self._error_label:
                self._error_label.setText("")
            self.validation_error.emit("")
        else:
            msg = f"⚠️ Folgende Wörter haben keine Übersetzung: {', '.join(error_columns)}"
            if hasattr(self, "_error_label") and self._error_label:
                self._error_label.setText(msg)
            self.validation_error.emit(msg)

        return is_valid
