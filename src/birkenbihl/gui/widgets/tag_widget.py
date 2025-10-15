"""Tag widget with removable functionality."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class TagWidget(QWidget):
    """A removable tag widget (like chips in Material Design).

    Features:
    - Displays text label
    - Has a close button (×) that is ALWAYS visible on the right side
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
        layout.setSpacing(4)

        # Create label
        self._label = QLabel(text)
        layout.addWidget(self._label)

        # Create close button (ALWAYS visible on the right)
        self._close_btn = QPushButton("×")
        self._close_btn.setMinimumSize(20, 20)
        self._close_btn.setMaximumSize(20, 20)
        self._close_btn.setVisible(True)  # ALWAYS visible!
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
                border: 1px solid #999;
                border-radius: 10px;
                background-color: #cccccc;
                color: #333;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: white;
                border-color: #f44336;
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
