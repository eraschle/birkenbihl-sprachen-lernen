"""Unassigned words pool widget for alignment editor."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from birkenbihl.gui.widgets.alignment.draggable_word_tag import DraggableWordTag, TagType
from birkenbihl.gui.widgets.alignment.flow_layout import FlowLayout


class UnassignedWordsPool(QWidget):
    """Pool of target words not assigned to source words.

    Displays unassigned words in a flow layout with drag-and-drop support.
    Words can be dragged from pool to alignment columns.

    Signals:
        word_count_changed(int): Emitted when pool size changes
        pool_emptied(): Emitted when last word removed
        word_dragged(str): Emitted when word drag starts
    """

    word_count_changed = Signal(int)
    pool_emptied = Signal()
    word_dragged = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        """Initialize unassigned words pool.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._word_tags: dict[str, DraggableWordTag] = {}
        self._title_label: QLabel
        self._pool_container: QWidget
        self._flow_layout: FlowLayout
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self._title_label = QLabel("Unassigned Words (0)")
        self._title_label.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(self._title_label)

        self._pool_container = QWidget()
        self._flow_layout = FlowLayout(self._pool_container, margin=5, spacing=8)
        self._pool_container.setMinimumHeight(80)
        self._pool_container.setStyleSheet("""
            background-color: #fafafa;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        layout.addWidget(self._pool_container)

    def add_word(self, word: str) -> None:
        """Add word to pool.

        Args:
            word: Word text to add
        """
        if word in self._word_tags:
            return

        tag = DraggableWordTag(word, TagType.TARGET)
        tag.drag_started.connect(lambda w: self._on_word_dragged(w))
        self._word_tags[word] = tag
        self._flow_layout.addWidget(tag)

        self._update_title()
        self.word_count_changed.emit(len(self._word_tags))

    def remove_word(self, word: str) -> None:
        """Remove word from pool.

        Args:
            word: Word text to remove
        """
        if word not in self._word_tags:
            return

        tag = self._word_tags.pop(word)
        self._flow_layout.removeWidget(tag)
        tag.deleteLater()

        self._update_title()
        count = len(self._word_tags)
        self.word_count_changed.emit(count)

        if count == 0:
            self.pool_emptied.emit()

    def set_words(self, words: list[str]) -> None:
        """Replace all words in pool.

        Args:
            words: List of words to set
        """
        self.clear()
        for word in words:
            self.add_word(word)

    def get_words(self) -> list[str]:
        """Return all words in pool.

        Returns:
            List of word strings
        """
        return list(self._word_tags.keys())

    def clear(self) -> None:
        """Remove all words from pool."""
        for word in list(self._word_tags.keys()):
            self.remove_word(word)

    def is_empty(self) -> bool:
        """Check if pool has no words.

        Returns:
            True if empty, False otherwise
        """
        return len(self._word_tags) == 0

    def _update_title(self) -> None:
        """Update title label with word count."""
        count = len(self._word_tags)
        self._title_label.setText(f"Unassigned Words ({count})")

        if count > 0:
            self._title_label.setStyleSheet("font-weight: bold; color: #ff6600;")
        else:
            self._title_label.setStyleSheet("font-weight: bold; color: #00aa00;")

    def _on_word_dragged(self, word: str) -> None:
        """Handle word drag start.

        Args:
            word: Word being dragged
        """
        self.word_dragged.emit(word)
