"""Sentence list widget for displaying numbered sentences."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from birkenbihl.models.translation import Sentence


class SentenceList(QListWidget):
    """List widget showing numbered sentences from translation.

    Emits sentence_selected signal when user clicks on a sentence.
    """

    sentence_selected = Signal(int)

    def load_sentences(self, sentences: list[Sentence]) -> None:
        """Load sentences with numbering (1. First sentence, 2. Second, ...).

        Args:
            sentences: List of sentences to display
        """
        self.clear()
        for index, sentence in enumerate(sentences):
            preview = self._create_preview(sentence.source_text)
            item_text = f"{index + 1}. {preview}"
            item = QListWidgetItem(item_text)
            item.setData(256, index)
            self.addItem(item)

        if sentences:
            self.setCurrentRow(0)

    def select_sentence(self, index: int) -> None:
        """Programmatically select sentence by index.

        Args:
            index: Sentence index (0-based)
        """
        if 0 <= index < self.count():
            self.setCurrentRow(index)

    def currentChanged(self, current, previous) -> None:  # type: ignore
        """Handle selection change - emit signal with sentence index."""
        super().currentChanged(current, previous)
        if current.isValid():
            index = self.item(current.row()).data(256)
            self.sentence_selected.emit(index)

    def _create_preview(self, text: str, max_length: int = 50) -> str:
        """Create truncated preview of sentence text.

        Args:
            text: Full sentence text
            max_length: Maximum length before truncation

        Returns:
            Truncated text with ellipsis if needed
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
