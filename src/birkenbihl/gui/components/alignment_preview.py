"""Alignment preview component for word-by-word translations."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QWidget

from birkenbihl.models.translation import WordAlignment


class AlignmentPreview(QWidget):
    """Read-only preview of word-by-word alignment.

    Displays source words and their target translations in a grid layout.
    Each row shows: source_word → target_word.
    """

    def __init__(self, alignments: list[WordAlignment]):
        super().__init__()
        self._alignments = self._sort_by_position(alignments)
        self._setup_ui()

    def _sort_by_position(self, alignments: list[WordAlignment]) -> list[WordAlignment]:
        """Sort alignments by position for correct display order."""
        return sorted(alignments, key=lambda a: a.position)

    def _setup_ui(self) -> None:
        """Create grid layout with alignment rows."""
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self._add_header_row(layout)
        self._add_alignment_rows(layout)

    def _add_header_row(self, layout: QGridLayout) -> None:
        """Add header labels for source and target columns."""
        source_header = self._create_bold_label("Source")
        arrow_header = self._create_bold_label("")
        target_header = self._create_bold_label("Target")

        layout.addWidget(source_header, 0, 0)
        layout.addWidget(arrow_header, 0, 1)
        layout.addWidget(target_header, 0, 2)

    def _add_alignment_rows(self, layout: QGridLayout) -> None:
        """Add one row per word alignment."""
        for row_index, alignment in enumerate(self._alignments, start=1):
            source_label = QLabel(alignment.source_word)
            arrow_label = QLabel("→")
            target_label = QLabel(alignment.target_word)

            layout.addWidget(source_label, row_index, 0)
            layout.addWidget(arrow_label, row_index, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(target_label, row_index, 2)

    def _create_bold_label(self, text: str) -> QLabel:
        """Create bold label for headers."""
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def update_alignments(self, alignments: list[WordAlignment]) -> None:
        """Update displayed alignments with new data."""
        self._alignments = self._sort_by_position(alignments)
        self._clear_layout()
        self._setup_ui()

    def _clear_layout(self) -> None:
        """Remove all widgets from layout."""
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
