"""Tests for AlignmentPreview widget."""

import pytest

from birkenbihl.gui.widgets.alignment_preview import AlignmentPreview
from birkenbihl.models.translation import WordAlignment


class TestAlignmentPreview:
    """Test AlignmentPreview widget."""

    @pytest.fixture
    def qapp(self, qapp):
        """Provide QApplication instance."""
        return qapp

    @pytest.fixture
    def alignments(self):
        """Provide test alignments."""
        return [
            WordAlignment(source_word="Hello", target_word="Hallo", position=0),
            WordAlignment(source_word="World", target_word="Welt", position=1),
        ]

    def test_widget_creation(self, qapp):
        """Test widget creation."""
        widget = AlignmentPreview()
        assert widget is not None

    def test_widget_with_alignments(self, qapp, alignments):
        """Test widget with initial alignments."""
        widget = AlignmentPreview(alignments)
        assert widget._alignments == alignments

    def test_html_generation(self, qapp, alignments):
        """Test HTML generation."""
        widget = AlignmentPreview(alignments)
        html = widget._build_alignment_html()

        assert "Hello" in html
        assert "Hallo" in html
        assert "World" in html
        assert "Welt" in html

    def test_empty_alignments(self, qapp):
        """Test widget with empty alignments."""
        widget = AlignmentPreview([])
        html = widget._build_alignment_html()

        assert "Keine Zuordnungen" in html

    def test_update_data(self, qapp, alignments):
        """Test updating alignments."""
        widget = AlignmentPreview()
        assert widget._alignments == []

        widget.update_data(alignments)
        assert widget._alignments == alignments

    def test_clear(self, qapp, alignments):
        """Test clearing alignments."""
        widget = AlignmentPreview(alignments)
        assert len(widget._alignments) == 2

        widget.clear()
        assert widget._alignments == []
