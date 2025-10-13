"""Progress widget for async operations."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QWidget


class ProgressWidget(QWidget):
    """Progress bar with status message and cancel button.

    Shows indeterminate or determinate progress for long-running operations.
    Emits cancelled signal when user clicks cancel button.
    """

    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._progress_bar = QProgressBar()  # type: ignore[reportUninitializedInstanceVariable]
        self._message_label = QLabel()  # type: ignore[reportUninitializedInstanceVariable]
        self._cancel_button = QPushButton("Cancel")  # type: ignore[reportUninitializedInstanceVariable]

        self._cancel_button.clicked.connect(self._on_cancel_clicked)

        layout.addWidget(self._message_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._cancel_button)

    def start(self, message: str = "Processing...") -> None:
        """Start indeterminate progress with message."""
        self._progress_bar.setRange(0, 0)
        self._message_label.setText(message)
        self.show()

    def update_progress(self, value: int, maximum: int = 100) -> None:
        """Update progress to specific value."""
        self._progress_bar.setRange(0, maximum)
        self._progress_bar.setValue(value)

    def set_message(self, message: str) -> None:
        """Update status message without changing progress."""
        self._message_label.setText(message)

    def finish(self) -> None:
        """Complete progress and hide widget."""
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(100)
        self.hide()

    def _on_cancel_clicked(self) -> None:
        """Emit cancelled signal when cancel button clicked."""
        self.cancelled.emit()
