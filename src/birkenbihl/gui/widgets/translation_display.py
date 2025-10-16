"""Translation display widget showing natural and word-by-word translations."""

from PySide6.QtWidgets import QGroupBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from birkenbihl.gui.widgets.interleaved_grid import InterleavedGridReadOnly
from birkenbihl.models.translation import Sentence


class TranslationDisplay(QWidget):
    """Display natural translation and word-by-word grid for single sentence.

    Shows two sections:
    1. Natural translation (read-only text)
    2. Word-by-word (interleaved grid)
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialize translation display widget."""
        super().__init__(parent)
        self._init_ui()

    def display_sentence(self, sentence: Sentence) -> None:
        """Display natural translation and word-by-word grid.

        Args:
            sentence: Sentence to display
        """
        self._natural_label.setText(sentence.natural_translation)
        self._interleaved_grid.build_grid(sentence)

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.addWidget(self._create_natural_section())
        layout.addWidget(self._create_word_by_word_section())

    def _create_natural_section(self) -> QGroupBox:
        """Create natural translation section.

        Returns:
            Group box with natural translation label
        """
        group = QGroupBox("Natürliche Übersetzung")
        layout = QVBoxLayout(group)

        self._natural_label = QLabel()
        self._natural_label.setWordWrap(True)
        layout.addWidget(self._natural_label)

        return group

    def _create_word_by_word_section(self) -> QGroupBox:
        """Create word-by-word section with scrollable grid.

        Returns:
            Group box with interleaved grid in scroll area
        """
        group = QGroupBox("Wort-für-Wort")
        layout = QVBoxLayout(group)

        self._interleaved_grid = InterleavedGridReadOnly()

        scroll = QScrollArea()
        scroll.setWidget(self._interleaved_grid)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return group
