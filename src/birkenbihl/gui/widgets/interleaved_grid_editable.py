"""Editable interleaved grid widget with drag&drop for word alignment editing."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from birkenbihl.gui.models.grid_state import GridState, build_grid_state
from birkenbihl.gui.styles import theme
from birkenbihl.gui.widgets.grid_column import GridColumn
from birkenbihl.gui.widgets.unassigned_pool import UnassignedPool
from birkenbihl.gui.widgets.word_tag import WordTag
from birkenbihl.models.translation import Sentence


class InterleavedGridEditable(QWidget):
    """Editable interleaved grid with drag&drop for word alignment.

    All editing logic lives in GridState; this widget renders it and forwards drops.

    Layout:
        [Column1] [Column2] [Column3] ...  ← Grid columns (orange = flagged for review, red = empty)
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
        self._pool.word_dropped.connect(lambda target_index: self._on_drop(target_index, None))
        layout.addWidget(self._pool)

        self._error_label = QLabel()  # type: ignore[reportUninitializedInstanceVariable]
        self._error_label.setStyleSheet(theme.get_error_label_style())
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)

    def build_grid(self, sentence: Sentence) -> None:
        """Build grid from sentence word alignments.

        Args:
            sentence: Sentence with word alignments
        """
        self._grid_state = build_grid_state(sentence)
        self._render()
        self._validate()

    def grid_state(self) -> GridState | None:
        """Current editing state (None before a sentence is loaded)."""
        return self._grid_state

    def _on_drop(self, target_index: int, column_index: int | None) -> None:
        """Move a dropped word; column_index None means the unassigned pool."""
        if not self._grid_state:
            return
        self._grid_state.move(target_index, column_index)
        self._apply_change()

    def _apply_change(self) -> None:
        """Re-render after an edit and report it."""
        assert self._grid_state is not None
        self._render()
        # Report the change before the validation result: the edit panel enables Save on a valid result
        # only once it knows there are unsaved changes.
        self.alignments_changed.emit(self._grid_state.to_word_alignments())
        self._validate()

    def _on_confirm(self, column_index: int) -> None:
        """Confirm a flagged column as correct without moving words."""
        if not self._grid_state:
            return
        self._grid_state.confirm(column_index)
        self._apply_change()

    def _render(self) -> None:
        """Rebuild columns and pool from the current state."""
        self._clear()
        if not self._grid_state:
            return
        for column_index, column_state in enumerate(self._grid_state.columns):
            column = GridColumn(column_state.source_word)
            column.word_dropped.connect(lambda target_index, col=column_index: self._on_drop(target_index, col))
            column.confirm_requested.connect(lambda col=column_index: self._on_confirm(col))
            for target_index in column_state.target_indices:
                column.add_tag(self._create_tag(target_index))
            self._columns.append(column)
            self._grid_layout.addWidget(column)
        for target_index in self._grid_state.unassigned:
            self._pool.add_tag(self._create_tag(target_index))

    def _clear(self) -> None:
        """Remove all columns and pool tags."""
        for column in self._columns:
            column.setParent(None)
            column.deleteLater()
        self._columns.clear()
        for tag in self._pool.get_tags():
            self._pool.remove_tag(tag)

    def _create_tag(self, target_index: int) -> WordTag:
        """Create word tag with drag feedback connections."""
        assert self._grid_state is not None
        tag = WordTag(self._grid_state.target_word(target_index), target_index)
        tag.drag_started.connect(lambda: self._set_drop_zones_visible(True))
        tag.drag_ended.connect(lambda: self._set_drop_zones_visible(False))
        return tag

    def _set_drop_zones_visible(self, visible: bool) -> None:
        for column in self._columns:
            column.set_drop_zone_visible(visible)

    def _validate(self) -> bool:
        """Apply the Birkenbihl rules, mark columns and report errors.

        Returns:
            True if valid
        """
        if not self._grid_state:
            return True

        is_valid, message = self._grid_state.validate()
        for column, column_state in zip(self._columns, self._grid_state.columns, strict=True):
            column.set_state(error=column_state.is_empty(), flagged=column_state.is_flagged())

        text = "" if is_valid else f"⚠️ {message}"
        self._error_label.setText(text)
        self.validation_error.emit(text)
        return is_valid
