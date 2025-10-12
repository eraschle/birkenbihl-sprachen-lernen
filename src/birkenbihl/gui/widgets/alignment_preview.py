"""Word alignment preview widget."""

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from birkenbihl.models.translation import WordAlignment


class AlignmentPreview(QWidget):
    """Read-only word alignment preview.

    Displays source words above target words in HTML format.
    Similar to Streamlit UI alignment display.
    """

    def __init__(self, alignments: list[WordAlignment] | None = None, parent=None):
        """Initialize widget.

        Args:
            alignments: Word alignments to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._alignments = alignments or []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text_browser = QTextBrowser()
        self._text_browser.setReadOnly(True)
        self._text_browser.setOpenExternalLinks(False)

        layout.addWidget(self._text_browser)

        self._render_alignments()

    def _render_alignments(self) -> None:
        """Render alignments as HTML."""
        html = self._build_alignment_html()
        self._text_browser.setHtml(html)

    def _build_alignment_html(self) -> str:
        """Build HTML for alignment display.

        Returns:
            HTML string
        """
        if not self._alignments:
            return "<p><i>Keine Zuordnungen vorhanden</i></p>"

        html = """
        <style>
            .alignment-container {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                padding: 10px;
            }
            .word-pair {
                display: inline-flex;
                flex-direction: column;
                align-items: center;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            .source-word {
                font-size: 14px;
                color: #2196F3;
                margin-bottom: 4px;
                font-weight: 500;
            }
            .target-word {
                font-size: 14px;
                color: #4CAF50;
                font-weight: 500;
            }
            .arrow {
                font-size: 10px;
                color: #999;
            }
        </style>
        <div class="alignment-container">
        """

        sorted_alignments = sorted(self._alignments, key=lambda a: a.position)

        for alignment in sorted_alignments:
            html += f"""
            <div class="word-pair">
                <span class="source-word">{alignment.source_word}</span>
                <span class="arrow">↓</span>
                <span class="target-word">{alignment.target_word}</span>
            </div>
            """

        html += "</div>"
        return html

    def update_data(self, alignments: list[WordAlignment]) -> None:
        """Update alignments display.

        Args:
            alignments: New alignments to display
        """
        self._alignments = alignments
        self._render_alignments()

    def clear(self) -> None:
        """Clear alignment display."""
        self._alignments = []
        self._render_alignments()
