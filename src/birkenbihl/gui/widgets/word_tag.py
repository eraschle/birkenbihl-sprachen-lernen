"""Draggable word tag widget for interleaved grid editing."""

from PySide6.QtCore import QEvent, QMimeData, Qt, Signal
from PySide6.QtGui import QCursor, QDrag, QEnterEvent, QMouseEvent
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QWidget


class WordTag(QLabel):
    """Draggable tag representing a single word in interleaved grid.

    Visual: [word] with rounded corners, padding, hover effect.
    Behavior: Click and drag to move between grid columns.
    """

    drag_started = Signal()
    drag_ended = Signal()

    def __init__(self, word: str, parent: QWidget = None):
        """Initialize word tag.

        Args:
            word: The word text to display
            parent: Parent widget
        """
        super().__init__(word, parent)
        self._word = word
        self._is_dragging = False
        self._setup_style()

    def get_word(self) -> str:
        """Get the word text.

        Returns:
            Word text
        """
        return self._word

    def _setup_style(self) -> None:
        """Configure tag appearance."""
        self.setStyleSheet(self._normal_style())
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setMargin(2)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start drag operation on left click.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.drag_started.emit()
            self._start_drag()

    def _start_drag(self) -> None:
        """Execute drag operation."""
        drag = QDrag(self)
        mime_data = QMimeData()
        drag.setMimeData(mime_data)
        mime = drag.mimeData()
        mime.setText(self._word)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)
        self._end_drag()

    def _end_drag(self) -> None:
        """Cleanup after drag ends."""
        self._is_dragging = False
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.drag_ended.emit()

    def enterEvent(self, event: QEnterEvent) -> None:
        """Apply hover style.

        Args:
            event: Enter event
        """
        if not self._is_dragging:
            self.setStyleSheet(self._hover_style())
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Remove hover style.

        Args:
            event: Leave event
        """
        if not self._is_dragging:
            self.setStyleSheet(self._normal_style())
        super().leaveEvent(event)

    def _normal_style(self) -> str:
        """Get normal state stylesheet.

        Returns:
            CSS stylesheet string
        """
        return """
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
            }
        """

    def _hover_style(self) -> str:
        """Get hover state stylesheet.

        Returns:
            CSS stylesheet string
        """
        return """
            QLabel {
                background-color: #e8e8e8;
                border: 1px solid #999;
                border-radius: 4px;
                padding: 5px 10px;
            }
        """
