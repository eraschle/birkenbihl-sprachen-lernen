"""Interleaved grid widget for read-only word-by-word display."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from birkenbihl.models.translation import Sentence
from birkenbihl.utils.text_extractor import split_hyphenated, tokenize_clean


class InterleavedGridReadOnly(QWidget):
    """Read-only interleaved grid showing word-by-word alignments.

    Layout:
        Row 0: Source words (bold, centered)
        Row 1: Connection lines (│)
        Row 2+: Target words (stacked vertically per column)

    Example:
        The   cat    sat
         │     │     │
        Die   Katze  saß
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialize interleaved grid widget."""
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setHorizontalSpacing(15)
        self._grid.setVerticalSpacing(2)

    def build_grid(self, sentence: Sentence) -> None:
        """Build interleaved grid from sentence word alignments.

        Args:
            sentence: Sentence with word alignments
        """
        self._clear_grid()

        if not sentence.word_alignments:
            self._show_empty_message()
            return

        grid_structure = self._build_grid_structure(sentence)
        self._render_columns(grid_structure)

    def _clear_grid(self) -> None:
        """Clear all widgets from grid layout."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

    def _show_empty_message(self) -> None:
        """Show message when no alignments exist."""
        label = QLabel("Keine Wort-Zuordnungen vorhanden")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grid.addWidget(label, 0, 0)

    def _build_grid_structure(self, sentence: Sentence) -> dict[str, list[str]]:
        """Convert word alignments to grid column structure.

        Args:
            sentence: Sentence with word alignments

        Returns:
            Dict mapping source_word → list of target_words
        """
        source_words = tokenize_clean(sentence.source_text)
        sorted_alignments = sorted(sentence.word_alignments, key=lambda a: a.position)

        grid: dict[str, list[str]] = {word: [] for word in source_words}

        for alignment in sorted_alignments:
            source = alignment.source_word
            target_parts = split_hyphenated(alignment.target_word)

            if source in grid:
                grid[source].extend(target_parts)

        return grid

    def _render_columns(self, grid: dict[str, list[str]]) -> None:
        """Render grid columns from structure.

        Args:
            grid: Grid structure (source → target words)
        """
        for col_index, (source_word, target_words) in enumerate(grid.items()):
            self._add_column(col_index, source_word, target_words)

    def _add_column(self, col: int, source: str, targets: list[str]) -> None:
        """Add single column to grid (source + connection + targets).

        Args:
            col: Column index
            source: Source word
            targets: List of target words (stacked vertically)
        """
        self._add_source_label(col, source)
        self._add_connection_label(col)
        self._add_target_labels(col, targets)

    def _add_source_label(self, col: int, word: str) -> None:
        """Add source word label to row 0.

        Args:
            col: Column index
            word: Source word
        """
        label = QLabel(word)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(11)
        font.setBold(True)
        label.setFont(font)
        self._grid.addWidget(label, 0, col)

    def _add_connection_label(self, col: int) -> None:
        """Add connection line to row 1.

        Args:
            col: Column index
        """
        label = QLabel("│")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._grid.addWidget(label, 1, col)

    def _add_target_labels(self, col: int, words: list[str]) -> None:
        """Add target words stacked vertically starting at row 2.

        Args:
            col: Column index
            words: List of target words
        """
        for row_offset, word in enumerate(words):
            label = QLabel(word)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = label.font()
            font.setPointSize(10)
            label.setFont(font)
            self._grid.addWidget(label, 2 + row_offset, col)
