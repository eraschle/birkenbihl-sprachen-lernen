"""Draggable word tag widget for alignment editor."""

from enum import Enum
from typing import Any

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QDrag, QMouseEvent
from PySide6.QtWidgets import QLabel, QWidget


class TagType(Enum):
    """Type of word tag."""

    SOURCE = "source"  # Original language word (fixed, not draggable)
    TARGET = "target"  # Translated word (draggable)


class TagState(Enum):
    """Visual state of tag."""

    NORMAL = "normal"
    HOVER = "hover"
    DRAGGING = "dragging"
    INVALID = "invalid"


class DraggableWordTag(QLabel):
    """Draggable word chip for alignment editor.

    Displays a single word that can be dragged between columns.
    Visual feedback for different states (normal, hover, dragging, invalid).

    Signals:
        drag_started(str): Emitted when drag begins with word text
        drag_ended(str): Emitted when drag ends with word text
        clicked(): Emitted on click
    """

    drag_started = Signal(str)
    drag_ended = Signal(str)
    clicked = Signal()

    def __init__(self, word: str, tag_type: TagType = TagType.TARGET, parent: QWidget | None = None):
        """Initialize draggable word tag.

        Args:
            word: Text to display
            tag_type: SOURCE (fixed) or TARGET (draggable)
            parent: Parent widget
        """
        super().__init__(word, parent)
        self._word = word
        self._tag_type = tag_type
        self._state = TagState.NORMAL
        self._drag_start_pos = QPoint()

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI properties and styling."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(30)
        self.setMinimumWidth(50)
        self.setMaximumHeight(40)

        if self._tag_type == TagType.TARGET:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._apply_style()

    def _apply_style(self) -> None:
        """Apply stylesheet based on current state."""
        styles = {
            TagState.NORMAL: """
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
            """,
            TagState.HOVER: """
                background-color: #e0e0e0;
                border: 1px solid #999;
                border-radius: 4px;
                padding: 5px 10px;
            """,
            TagState.DRAGGING: """
                background-color: #d0e8ff;
                border: 2px dashed #0078d4;
                border-radius: 4px;
                padding: 5px 10px;
                opacity: 0.7;
            """,
            TagState.INVALID: """
                background-color: #ffe0e0;
                border: 2px solid #ff0000;
                border-radius: 4px;
                padding: 5px 10px;
            """,
        }
        self.setStyleSheet(styles.get(self._state, styles[TagState.NORMAL]))

    def set_state(self, state: TagState) -> None:
        """Update visual state.

        Args:
            state: New state to apply
        """
        self._state = state
        self._apply_style()

    def get_word(self) -> str:
        """Return the word text.

        Returns:
            Word string
        """
        return self._word

    def get_tag_type(self) -> TagType:
        """Return the tag type.

        Returns:
            TagType (SOURCE or TARGET)
        """
        return self._tag_type

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for drag initiation.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton and self._tag_type == TagType.TARGET:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for drag start.

        Args:
            event: Mouse event
        """
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._tag_type != TagType.TARGET:
            return

        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        self.start_drag()

    def start_drag(self) -> None:
        """Initiate drag operation."""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self._word)
        drag.setMimeData(mime_data)

        self.set_state(TagState.DRAGGING)
        self.drag_started.emit(self._word)

        drag.exec(Qt.DropAction.MoveAction)

        self.set_state(TagState.NORMAL)
        self.drag_ended.emit(self._word)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if (event.pos() - self._drag_start_pos).manhattanLength() < 5:
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: Any) -> None:
        """Handle mouse enter for hover effect.

        Args:
            event: Enter event
        """
        if self._state == TagState.NORMAL and self._tag_type == TagType.TARGET:
            self.set_state(TagState.HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event: Any) -> None:
        """Handle mouse leave to remove hover.

        Args:
            event: Leave event
        """
        if self._state == TagState.HOVER:
            self.set_state(TagState.NORMAL)
        super().leaveEvent(event)
