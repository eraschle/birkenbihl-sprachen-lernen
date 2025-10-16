"""Pool widget for unassigned words in interleaved grid."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from birkenbihl.gui.widgets.word_tag import WordTag


class UnassignedPool(QFrame):
    """Horizontal pool for words not yet assigned to any column.

    Visual layout:
        [Nicht zugeordnet] → [Tag1] [Tag2] [Tag3]
    """

    word_dropped = Signal(str)

    def __init__(self, parent=None):
        """Initialize unassigned pool.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._tags: list[WordTag] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setAcceptDrops(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self._create_label())
        layout.addStretch()
        self._setup_style()

    def _create_label(self) -> QLabel:
        """Create pool label.

        Returns:
            Label widget
        """
        label = QLabel("Nicht zugeordnet →")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def _setup_style(self) -> None:
        """Configure pool appearance."""
        self.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)

    def add_tag(self, tag: WordTag) -> None:
        """Add tag to pool.

        Args:
            tag: Word tag to add
        """
        self._tags.append(tag)
        layout = self.layout()
        if isinstance(layout, QHBoxLayout):
            layout.insertWidget(layout.count() - 1, tag)

    def remove_tag(self, tag: WordTag) -> None:
        """Remove tag from pool.

        Args:
            tag: Word tag to remove
        """
        if tag in self._tags:
            self._tags.remove(tag)
            tag.setParent(None)
            tag.deleteLater()

    def get_tags(self) -> list[WordTag]:
        """Get all tags in pool.

        Returns:
            List of word tags
        """
        return self._tags.copy()

    def is_empty(self) -> bool:
        """Check if pool is empty.

        Returns:
            True if no tags present
        """
        return len(self._tags) == 0

    def dragEnterEvent(self, event) -> None:
        """Handle drag entering pool.

        Args:
            event: Drag event
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self._set_highlighted(True)

    def dragLeaveEvent(self, event) -> None:
        """Handle drag leaving pool.

        Args:
            event: Drag event
        """
        self._set_highlighted(False)

    def dropEvent(self, event) -> None:
        """Handle word dropped into pool.

        Args:
            event: Drop event
        """
        word = event.mimeData().text()
        self.word_dropped.emit(word)
        self._set_highlighted(False)
        event.acceptProposedAction()

    def _set_highlighted(self, highlighted: bool) -> None:
        """Highlight pool during drag hover.

        Args:
            highlighted: True to highlight
        """
        if highlighted:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 150, 255, 0.1);
                    border: 2px solid #0096ff;
                    border-radius: 4px;
                }
            """)
        else:
            self._setup_style()
