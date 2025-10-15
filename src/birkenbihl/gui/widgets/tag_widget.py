"""Tag widget with removable functionality."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class TagWidget(QWidget):
    """A removable tag widget (like chips in Material Design).

    Features:
    - Displays text label
    - Has a close button (×) that appears on hover
    - Emits removed signal when × is clicked
    - Rounded corners with Material Design styling
    """

    removed = Signal()

    def __init__(self, text: str, parent: QWidget | None = None):
        """Initialize the tag widget.

        Args:
            text: The text to display in the tag
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._text = text

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(2)

        # Create label
        self._label = QLabel(text)
        layout.addWidget(self._label)

        # Create close button
        self._close_btn = QPushButton("×")
        self._close_btn.setMaximumSize(14, 14)
        self._close_btn.setFlat(True)
        self._close_btn.setVisible(False)
        self._close_btn.clicked.connect(self.removed.emit)
        layout.addWidget(self._close_btn)

        # Apply styling
        self.setStyleSheet(
            """
            TagWidget {
                background-color: #e0e0e0;
                border-radius: 8px;
            }
            TagWidget:hover {
                background-color: #d0d0d0;
            }
            QPushButton {
                border: none;
                background: transparent;
                color: #666;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #f44336;
            }
            QLabel {
                font-size: 11px;
            }
            """
        )

    def get_text(self) -> str:
        """Get the text displayed in the tag.

        Returns:
            The tag text
        """
        return self._text

    def enterEvent(self, event):
        """Show close button when mouse enters the widget."""
        self._close_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide close button when mouse leaves the widget."""
        self._close_btn.setVisible(False)
        super().leaveEvent(event)
