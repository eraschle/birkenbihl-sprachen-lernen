"""Natural translation editor widget with manual editing and AI generation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


class NaturalEditor(QWidget):
    """Editor for natural translation with manual editing and AI regeneration.

    Provides editable QTextEdit with buttons for explicit editing and AI generation.
    Emits signals when text is changed manually or AI regeneration is requested.
    """

    text_changed = Signal(str)
    generate_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        """Initialize natural editor widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)

        self._text_edit = QTextEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self._text_edit.setPlaceholderText("Natural translation will appear here...")
        layout.addWidget(self._text_edit)

        layout.addLayout(self._create_button_layout())

    def _create_button_layout(self) -> QHBoxLayout:
        """Create button layout with Edit and Generate buttons.

        Returns:
            Button layout
        """
        button_layout = QHBoxLayout()

        self._edit_button = QPushButton("Edit")  # type: ignore[reportUninitializedInstanceVariable]
        self._edit_button.setToolTip("Focus text editor for manual editing")
        button_layout.addWidget(self._edit_button)

        self._generate_button = QPushButton("Generate (AI)")  # type: ignore[reportUninitializedInstanceVariable]
        self._generate_button.setToolTip("Regenerate translation using AI")
        button_layout.addWidget(self._generate_button)

        button_layout.addStretch()
        return button_layout

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self._text_edit.textChanged.connect(self._on_text_changed)
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._generate_button.clicked.connect(self._on_generate_clicked)

    def _on_text_changed(self) -> None:
        """Handle text change - emit signal with current text."""
        self.text_changed.emit(self.get_text())

    def _on_edit_clicked(self) -> None:
        """Handle Edit button click - focus text editor."""
        self._text_edit.setFocus()

    def _on_generate_clicked(self) -> None:
        """Handle Generate button click - emit signal."""
        self.generate_requested.emit()

    def set_text(self, text: str) -> None:
        """Set natural translation text.

        Args:
            text: Natural translation text
        """
        self._text_edit.blockSignals(True)
        self._text_edit.setPlainText(text)
        self._text_edit.blockSignals(False)

    def get_text(self) -> str:
        """Get current text.

        Returns:
            Current text in editor
        """
        return self._text_edit.toPlainText()

    def set_edit_enabled(self, enabled: bool) -> None:
        """Enable or disable editing.

        Args:
            enabled: True to enable editing, False to disable
        """
        self._text_edit.setEnabled(enabled)
        self._edit_button.setEnabled(enabled)
        self._generate_button.setEnabled(enabled)

    def set_loading(self, loading: bool) -> None:
        """Set loading state for AI generation.

        Args:
            loading: True to show loading, False to hide
        """
        if loading:
            self._generate_button.setText("Wird generiert...")
            self._generate_button.setEnabled(False)
        else:
            self._generate_button.setText("Generate (AI)")
            self._generate_button.setEnabled(True)
