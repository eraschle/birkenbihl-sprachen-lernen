"""Tests for AlignmentEditor widget."""

import pytest

from birkenbihl.gui.widgets.alignment_editor import AlignmentEditor
from birkenbihl.models.translation import Sentence, WordAlignment


@pytest.fixture
def sample_sentence() -> Sentence:
    """Create sample sentence for testing."""
    return Sentence(
        source_text="Yo te extrañaré",
        natural_translation="Ich werde dich vermissen",
        word_alignments=[
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
        ],
    )


@pytest.mark.ui
class TestAlignmentEditor:
    """Test suite for AlignmentEditor widget."""

    def test_init_without_sentence(self, qapp) -> None:
        """Test initialization without sentence."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor()
        assert editor._sentence is None
        assert editor._target_words == []
        assert editor._source_mappings == {}

    def test_init_with_sentence(self, qapp, sample_sentence: Sentence) -> None:
        """Test initialization with sentence."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor(sentence=sample_sentence)
        assert editor._sentence == sample_sentence
        assert editor._target_words == ["Ich", "werde", "dich", "vermissen"]
        assert len(editor._source_mappings) == 3

    def test_build_mappings_splits_hyphens(self, qapp, sample_sentence: Sentence) -> None:
        """Test that _build_mappings splits hyphenated words."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor(sentence=sample_sentence)

        # Check that "werde-vermissen" was split into list
        assert editor._source_mappings["Yo"] == ["Ich"]
        assert editor._source_mappings["te"] == ["dich"]
        assert editor._source_mappings["extrañaré"] == ["werde", "vermissen"]

    def test_get_available_target_words_all_available(self, qapp, sample_sentence: Sentence) -> None:
        """Test _get_available_target_words with no mappings."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor(sentence=sample_sentence)
        editor._source_mappings = {}  # Clear mappings

        available = editor._get_available_target_words()
        assert available == ["Ich", "werde", "dich", "vermissen"]

    def test_get_available_target_words_excludes_mapped(self, qapp, sample_sentence: Sentence) -> None:
        """Test _get_available_target_words excludes already mapped words."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor(sentence=sample_sentence)
        editor._source_mappings = {
            "Yo": ["Ich"],
            "te": ["dich"],
        }

        available = editor._get_available_target_words()
        assert available == ["werde", "vermissen"]

    def test_get_available_target_words_includes_current_source(self, qapp, sample_sentence: Sentence) -> None:
        """Test _get_available_target_words includes words from current source."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor(sentence=sample_sentence)
        editor._source_mappings = {
            "Yo": ["Ich", "werde"],
            "te": ["dich"],
        }

        # Should include "werde" because it's for the current source word "Yo"
        available = editor._get_available_target_words(for_source_word="Yo")
        assert "werde" in available
        assert "Ich" in available
        assert "dich" not in available  # Used by "te"

    def test_build_alignments_uses_hook_system(self, qapp, sample_sentence: Sentence) -> None:
        """Test _build_alignments uses hook system correctly."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor(sentence=sample_sentence)
        editor._source_mappings = {
            "Yo": ["Ich"],
            "te": ["dich"],
            "extrañaré": ["werde", "vermissen"],
        }

        alignments = editor._build_alignments()

        assert len(alignments) == 3
        assert alignments[0].source_word == "Yo"
        assert alignments[0].target_word == "Ich"
        assert alignments[1].source_word == "te"
        assert alignments[1].target_word == "dich"
        assert alignments[2].source_word == "extrañaré"
        assert alignments[2].target_word == "werde-vermissen"  # Hyphenated!

    def test_update_data(self, qapp, sample_sentence: Sentence) -> None:
        """Test update_data method."""
        if qapp is None:
            pytest.skip("Qt application not available")

        editor = AlignmentEditor()
        assert editor._sentence is None

        editor.update_data(sample_sentence)
        assert editor._sentence == sample_sentence
        assert len(editor._source_mappings) == 3
