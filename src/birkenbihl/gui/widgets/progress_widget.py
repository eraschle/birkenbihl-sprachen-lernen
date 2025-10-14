"""Progress display widget with cancellation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProgressWidget(QWidget):
    """Progress bar with cancel button.

    Shows progress (0-100%) and optional message.
    Emits signal when cancel is requested.
    Can be shown/hidden dynamically.
    """

    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        """Initialize widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        self._message_label = QLabel()  # type: ignore[reportUninitializedInstanceVariable]
        self._progress_bar = QProgressBar()  # type: ignore[reportUninitializedInstanceVariable]
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._is_indeterminate = False  # type: ignore[reportUninitializedInstanceVariable]

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_button = QPushButton("Abbrechen")  # type: ignore[reportUninitializedInstanceVariable]
        self._cancel_button.clicked.connect(self._on_cancel_clicked)

        button_layout.addWidget(self._cancel_button)
        button_layout.addStretch()

        layout.addWidget(self._message_label)
        layout.addWidget(self._progress_bar)
        layout.addLayout(button_layout)

    def set_progress(self, value: float) -> None:
        """Set progress value.

        Args:
            value: Progress value (0.0 to 1.0)
        """
        percent = int(value * 100)
        self._progress_bar.setValue(percent)

    def set_message(self, message: str) -> None:
        """Set progress message.

        Args:
            message: Message to display
        """
        self._message_label.setText(message)

    def start(self, message: str = "Übersetzen...", indeterminate: bool = False) -> None:
        """Start progress display.

        Args:
            message: Initial message
            indeterminate: If True, show busy indicator instead of progress bar
        """
        self.set_message(message)
        if indeterminate:
            self._progress_bar.setRange(0, 0)
            self._is_indeterminate = True
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
            self._is_indeterminate = False
        self.show()

    def finish(self) -> None:
        """Finish progress and hide widget."""
        if not self._is_indeterminate:
            self.set_progress(1.0)
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(100)
            self._is_indeterminate = False
        self.hide()

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.cancel_requested.emit()

    def set_cancel_enabled(self, enabled: bool) -> None:
        """Enable or disable cancel button.

        Args:
            enabled: Enable state
        """
        self._cancel_button.setEnabled(enabled)
