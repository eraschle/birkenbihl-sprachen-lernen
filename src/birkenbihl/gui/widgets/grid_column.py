"""Grid column widget for interleaved grid - holds one source word and its target words."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from birkenbihl.gui.styles import theme
from birkenbihl.gui.widgets.word_tag import WordTag


class GridColumn(QFrame):
    """Single column in interleaved grid (one source word + target tags).

    Visual layout:
        [Source Word]  ← Header (bold, fixed)
        ┌─────────┐
        │DropZone │    ← Invisible until drag starts
        └─────────┘
        [Tag1]         ← Target words (draggable)
        [Tag2]
    """

    word_dropped = Signal(str)

    def __init__(self, source_word: str, parent: QWidget | None = None):
        """Initialize grid column.

        Args:
            source_word: The original word for this column
            parent: Parent widget
        """
        super().__init__(parent)
        self._source_word = source_word
        self._tags: list[WordTag] = []
        self._drop_zone: QLabel | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        layout.addWidget(self._create_header())
        self._drop_zone = self._create_drop_zone()
        layout.addWidget(self._drop_zone)
        self._drop_zone.hide()

    def _create_header(self) -> QLabel:
        """Create header label with source word.

        Returns:
            Configured header label
        """
        label = QLabel(self._source_word)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(11)
        font.setBold(True)
        label.setFont(font)
        return label

    def _create_drop_zone(self) -> QLabel:
        """Create drop zone indicator.

        Returns:
            Drop zone label
        """
        label = QLabel()
        label.setFixedHeight(30)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(theme.get_drop_zone_style(False))
        return label

    def add_tag(self, tag: WordTag) -> None:
        """Add tag to column (stack vertically).

        Args:
            tag: Word tag to add
        """
        self._tags.append(tag)
        layout = self.layout()
        if layout:
            layout.addWidget(tag)

    def remove_tag(self, tag: WordTag) -> None:
        """Remove tag from column.

        Args:
            tag: Word tag to remove
        """
        if tag in self._tags:
            self._tags.remove(tag)
            tag.setParent(None)
            tag.deleteLater()

    def get_tags(self) -> list[WordTag]:
        """Get all tags in column.

        Returns:
            List of word tags
        """
        return self._tags.copy()

    def is_empty(self) -> bool:
        """Check if column has no tags.

        Returns:
            True if no tags present
        """
        return len(self._tags) == 0

    def set_drop_zone_visible(self, visible: bool) -> None:
        """Show/hide drop zone indicator.

        Args:
            visible: True to show, False to hide
        """
        if self._drop_zone:
            self._drop_zone.setVisible(visible)

    def set_highlighted(self, highlighted: bool) -> None:
        """Highlight column during drag hover.

        Args:
            highlighted: True to highlight
        """
        if self._drop_zone:
            self._drop_zone.setStyleSheet(theme.get_drop_zone_style(highlighted))

    def set_error_state(self, error: bool) -> None:
        """Mark column as error (red) when empty.

        Args:
            error: True to show error state
        """
        style = theme.get_error_frame_style() if error else ""
        self.setStyleSheet(style)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag entering column.

        Args:
            event: Drag event
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.set_highlighted(True)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Handle drag leaving column.

        Args:
            event: Drag event
        """
        if not event.isAccepted():
            self.set_highlighted(False)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle word dropped into column.

        Args:
            event: Drop event
        """
        word = event.mimeData().text()
        self.word_dropped.emit(word)
        self.set_highlighted(False)
        event.acceptProposedAction()
