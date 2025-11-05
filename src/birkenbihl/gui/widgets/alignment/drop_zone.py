"""Drop zone widget for word alignment columns."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QWidget


class AlignmentDropZone(QLabel):
    """Drop zone for word alignment columns.

    Accepts dropped words and provides visual feedback during drag operations.
    Highlights on hover, shows error state when empty.

    Signals:
        word_dropped(str, int): Emitted when word dropped (word, column_index)
        hover_entered(int): Emitted when drag enters zone
        hover_exited(int): Emitted when drag leaves zone
    """

    word_dropped = Signal(str, int)
    hover_entered = Signal(int)
    hover_exited = Signal(int)

    def __init__(self, column_index: int, parent: QWidget | None = None):
        """Initialize drop zone.

        Args:
            column_index: Index of this column in grid (0-indexed)
            parent: Parent widget
        """
        super().__init__(parent)
        self._column_index = column_index
        self._is_active = False
        self._is_highlighted = False
        self._is_error = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI properties."""
        self.setAcceptDrops(True)
        self.setMinimumHeight(60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("")  # Empty by default
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply stylesheet based on current state."""
        if not self._is_active:
            self.setStyleSheet("background-color: transparent; border: none;")
            return

        if self._is_error:
            style = """
                background-color: rgba(255, 0, 0, 0.05);
                border: 2px solid #ff0000;
                border-radius: 4px;
            """
        elif self._is_highlighted:
            style = """
                background-color: rgba(0, 150, 255, 0.2);
                border: 2px solid #0096ff;
                border-radius: 4px;
            """
        elif self._is_active:
            style = """
                background-color: rgba(0, 150, 255, 0.1);
                border: 2px dashed #0096ff;
                border-radius: 4px;
            """
        else:
            style = "background-color: transparent; border: none;"

        self.setStyleSheet(style)

    def set_active(self, active: bool) -> None:
        """Show/hide drop zone during drag operations.

        Args:
            active: True to show zone, False to hide
        """
        self._is_active = active
        self._apply_style()

    def set_highlight(self, highlight: bool) -> None:
        """Highlight zone when word hovers over.

        Args:
            highlight: True to highlight, False to remove
        """
        self._is_highlighted = highlight
        self._apply_style()

    def set_error(self, error: bool) -> None:
        """Mark zone as error (empty column).

        Args:
            error: True for error state, False for normal
        """
        self._is_error = error
        self._apply_style()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event.

        Args:
            event: Drag enter event
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.set_highlight(True)
            self.hover_entered.emit(self._column_index)

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """Handle drag leave event.

        Args:
            event: Drag leave event
        """
        self.set_highlight(False)
        self.hover_exited.emit(self._column_index)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event.

        Args:
            event: Drop event
        """
        if event.mimeData().hasText():
            word = event.mimeData().text()
            self.word_dropped.emit(word, self._column_index)
            event.acceptProposedAction()
            self.set_highlight(False)

    def get_column_index(self) -> int:
        """Get column index.

        Returns:
            Column index (0-indexed)
        """
        return self._column_index
