"""Alignment column widget for interleaved grid."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from birkenbihl.gui.widgets.alignment.draggable_word_tag import DraggableWordTag, TagType
from birkenbihl.gui.widgets.alignment.drop_zone import AlignmentDropZone


class AlignmentColumn(QWidget):
    """Single column in interleaved alignment grid.

    Contains one source word (fixed header) and multiple target words
    (draggable tags) stacked vertically.

    Signals:
        word_added(str, int): Word added to column (word, column_index)
        word_removed(str, int): Word removed from column (word, column_index)
    """

    word_added = Signal(str, int)
    word_removed = Signal(str, int)

    def __init__(self, source_word: str, column_index: int, parent: QWidget | None = None):
        """Initialize alignment column.

        Args:
            source_word: Original word to display in header
            column_index: Position in grid (0-indexed)
            parent: Parent widget
        """
        super().__init__(parent)
        self._source_word = source_word
        self._column_index = column_index
        self._word_tags: dict[str, DraggableWordTag] = {}
        self._is_error = False

        self._header_label: QLabel
        self._drop_zone: AlignmentDropZone
        self._tags_container: QWidget
        self._tags_layout: QVBoxLayout

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        # Source word header (fixed)
        self._header_label = QLabel(self._source_word)
        self._header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header_label.setMinimumWidth(80)
        self._header_label.setStyleSheet("""
            font-weight: bold;
            color: #333;
            padding: 8px;
            background-color: #f5f5f5;
            border: 1px solid #ccc;
            border-bottom: 2px solid #0078d4;
        """)
        layout.addWidget(self._header_label)

        # Drop zone
        self._drop_zone = AlignmentDropZone(self._column_index)
        self._drop_zone.word_dropped.connect(self._on_word_dropped)
        layout.addWidget(self._drop_zone)

        # Container for target word tags
        self._tags_container = QWidget()
        self._tags_layout = QVBoxLayout(self._tags_container)
        self._tags_layout.setContentsMargins(2, 2, 2, 2)
        self._tags_layout.setSpacing(5)
        self._tags_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._tags_container)

        # Column border
        self.setStyleSheet("""
            AlignmentColumn {
                border-right: 1px solid #ddd;
                background-color: white;
            }
        """)

    def add_word(self, word: str) -> None:
        """Add target word tag to column (stacks vertically).

        Args:
            word: Word text to add
        """
        if word in self._word_tags:
            return

        tag = DraggableWordTag(word, TagType.TARGET)
        tag.drag_started.connect(lambda w: self._on_tag_drag_started(w))
        self._word_tags[word] = tag
        self._tags_layout.addWidget(tag)

        self._update_error_state()
        self.word_added.emit(word, self._column_index)

    def remove_word(self, word: str) -> None:
        """Remove target word tag from column.

        Args:
            word: Word text to remove
        """
        if word not in self._word_tags:
            return

        tag = self._word_tags.pop(word)
        self._tags_layout.removeWidget(tag)
        tag.deleteLater()

        self._update_error_state()
        self.word_removed.emit(word, self._column_index)

    def get_words(self) -> list[str]:
        """Return all target words in this column.

        Returns:
            List of word strings
        """
        return list(self._word_tags.keys())

    def is_empty(self) -> bool:
        """Check if column has no target words.

        Returns:
            True if empty, False otherwise
        """
        return len(self._word_tags) == 0

    def set_error_state(self, error: bool) -> None:
        """Highlight column header if empty (validation error).

        Args:
            error: True for error state, False for normal
        """
        self._is_error = error
        self._drop_zone.set_error(error)

        if error:
            self._header_label.setStyleSheet("""
                font-weight: bold;
                color: #ff0000;
                padding: 8px;
                background-color: #ffe0e0;
                border: 1px solid #ff0000;
                border-bottom: 2px solid #ff0000;
            """)
        else:
            self._header_label.setStyleSheet("""
                font-weight: bold;
                color: #333;
                padding: 8px;
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-bottom: 2px solid #0078d4;
            """)

    def get_column_index(self) -> int:
        """Get column index.

        Returns:
            Column index (0-indexed)
        """
        return self._column_index

    def get_source_word(self) -> str:
        """Get source word.

        Returns:
            Source word string
        """
        return self._source_word

    def _on_word_dropped(self, word: str, column_index: int) -> None:
        """Handle word dropped in this column.

        Args:
            word: Word that was dropped
            column_index: This column's index
        """
        self.add_word(word)

    def _on_tag_drag_started(self, word: str) -> None:
        """Handle tag drag start from this column.

        Args:
            word: Word being dragged
        """
        # Mark for removal when drag completes
        pass

    def _update_error_state(self) -> None:
        """Update error state based on whether column is empty."""
        self.set_error_state(self.is_empty())

    def set_drop_zone_active(self, active: bool) -> None:
        """Show/hide drop zone during drag operations.

        Args:
            active: True to show, False to hide
        """
        self._drop_zone.set_active(active)
