"""Sentence display card widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.models.translation import Sentence


class SentenceCard(QWidget):
    """Collapsible sentence display card.

    Shows source text, natural translation, and alignments.
    Can be expanded/collapsed.
    Emits signal when edit is requested.
    """

    edit_requested = Signal(object)  # Sentence UUID

    def __init__(self, sentence: Sentence, expanded: bool = False, parent=None):
        """Initialize widget.

        Args:
            sentence: Sentence to display
            expanded: Initial expanded state
            parent: Parent widget
        """
        super().__init__(parent)
        self._sentence = sentence
        self._expanded = expanded
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()

        self._source_label = QLabel()
        self._source_label.setWordWrap(True)
        self._source_label.setStyleSheet("font-weight: bold; color: #2196F3;")

        self._toggle_button = QPushButton("▼" if self._expanded else "▶")
        self._toggle_button.setFixedWidth(30)
        self._toggle_button.clicked.connect(self._on_toggle)

        header_layout.addWidget(self._toggle_button)
        header_layout.addWidget(self._source_label, 1)

        layout.addLayout(header_layout)

        self._content_widget = QWidget()
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(30, 0, 0, 0)

        self._natural_label = QLabel()
        self._natural_label.setWordWrap(True)
        self._natural_label.setStyleSheet("color: #4CAF50;")

        self._alignment_count_label = QLabel()
        self._alignment_count_label.setStyleSheet("color: #666; font-size: 12px;")

        self._edit_button = QPushButton("Bearbeiten")
        self._edit_button.clicked.connect(self._on_edit_clicked)

        content_layout.addWidget(self._natural_label)
        content_layout.addWidget(self._alignment_count_label)
        content_layout.addWidget(self._edit_button)

        layout.addWidget(self._content_widget)

        self._update_display()
        self._content_widget.setVisible(self._expanded)

    def _update_display(self) -> None:
        """Update display with sentence data."""
        self._source_label.setText(self._sentence.source_text)
        self._natural_label.setText(f"→ {self._sentence.natural_translation}")

        alignment_count = len(self._sentence.word_alignments)
        self._alignment_count_label.setText(f"{alignment_count} Wort-Zuordnungen")

    def _on_toggle(self) -> None:
        """Handle toggle button click."""
        self._expanded = not self._expanded
        self._toggle_button.setText("▼" if self._expanded else "▶")
        self._content_widget.setVisible(self._expanded)

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        self.edit_requested.emit(self._sentence.uuid)

    def update_data(self, sentence: Sentence) -> None:
        """Update sentence data.

        Args:
            sentence: New sentence data
        """
        self._sentence = sentence
        self._update_display()

    def set_expanded(self, expanded: bool) -> None:
        """Set expanded state.

        Args:
            expanded: Expanded state
        """
        if self._expanded != expanded:
            self._on_toggle()
