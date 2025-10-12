"""Tests for alignment UI components."""

from unittest.mock import Mock

import pytest

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.services import language_service as ls
from birkenbihl.ui.components.alignment import (
    AlignmentEditor,
    AlignmentPreview,
    _extract_target_words_for_position,
)
from birkenbihl.ui.models.context import AlignmentContext


@pytest.fixture
def sample_alignments() -> list[WordAlignment]:
    """Create sample word alignments for testing."""
    return [
        WordAlignment(source_word="Yo", target_word="Ich", position=0),
        WordAlignment(source_word="te", target_word="dich", position=1),
        WordAlignment(source_word="extrañaré", target_word="vermissen-werde", position=2),
    ]


@pytest.fixture
def sample_sentence(sample_alignments: list[WordAlignment]) -> Sentence:
    """Create a sample sentence for testing."""
    return Sentence(
        source_text="Yo te extrañaré",
        natural_translation="Ich werde dich vermissen",
        word_alignments=sample_alignments,
    )


@pytest.fixture
def sample_translation(sample_sentence: Sentence) -> Translation:
    """Create a sample translation for testing."""
    return Translation(
        title="Test Translation",
        source_language=ls.get_language_by(name_or_code="es"),
        target_language=ls.get_language_by(name_or_code="de"),
        sentences=[sample_sentence],
    )


@pytest.fixture
def mock_service() -> TranslationService:
    """Create a mock translation service."""
    return Mock(spec=TranslationService)


@pytest.fixture
def alignment_context(
    sample_sentence: Sentence, sample_translation: Translation, mock_service: TranslationService
) -> AlignmentContext:
    """Create an alignment context for testing."""
    return AlignmentContext(
        sentence=sample_sentence,
        translation=sample_translation,
        service=mock_service,
        is_new_translation=True,
    )


class TestAlignmentPreview:
    """Tests for AlignmentPreview component."""

    def test_initialization(self, sample_alignments: list[WordAlignment]) -> None:
        """Test that AlignmentPreview initializes correctly."""
        preview = AlignmentPreview(sample_alignments)
        assert preview.alignments == sample_alignments

    def test_build_alignment_html(self, sample_alignments: list[WordAlignment]) -> None:
        """Test HTML generation for alignment preview."""
        preview = AlignmentPreview(sample_alignments)
        html = preview._build_alignment_html()

        # Check structure
        assert html.startswith("<div style='font-size: 13px; line-height: 1.8;'>")
        assert html.endswith("</div>")

        # Check content for each alignment
        assert "Yo" in html
        assert "Ich" in html
        assert "te" in html
        assert "dich" in html
        assert "extrañaré" in html
        assert "vermissen-werde" in html

        # Check styling
        assert "background-color: #f0f2f6" in html
        assert "color: #0066cc" in html  # Source word color
        assert "color: #009900" in html  # Target word color
        assert "↓" in html  # Arrow

    def test_html_escaping(self) -> None:
        """Test that HTML special characters are escaped."""
        alignments = [
            WordAlignment(source_word="<script>", target_word="&test&", position=0),
        ]
        preview = AlignmentPreview(alignments)
        html = preview._build_alignment_html()

        # HTML should be escaped
        assert "&lt;script&gt;" in html
        assert "&amp;test&amp;" in html
        assert "<script>" not in html

    def test_empty_alignments(self) -> None:
        """Test preview with empty alignment list."""
        preview = AlignmentPreview([])
        html = preview._build_alignment_html()

        # Should have wrapper div but no content
        assert html == "<div style='font-size: 13px; line-height: 1.8;'></div>"


class TestAlignmentEditor:
    """Tests for AlignmentEditor component."""

    def test_initialization(self, alignment_context: AlignmentContext) -> None:
        """Test that AlignmentEditor initializes correctly."""
        editor = AlignmentEditor(alignment_context)

        assert editor.context == alignment_context
        assert editor.sentence == alignment_context.sentence
        assert editor.editor_key == f"alignment_editor_{alignment_context.sentence.uuid}"

    def test_extract_target_words(self, alignment_context: AlignmentContext) -> None:
        """Test target word extraction from natural translation and alignments."""
        editor = AlignmentEditor(alignment_context)
        target_words = editor._extract_target_words()

        # Words from natural translation
        assert "Ich" in target_words
        assert "werde" in target_words
        assert "dich" in target_words
        assert "vermissen" in target_words

        # No duplicates
        assert len(target_words) == len(set(target_words))

    def test_extract_target_words_with_hyphens(self) -> None:
        """Test that hyphenated words in alignments are split correctly."""
        sentence = Sentence(
            source_text="Yo te extrañaré",
            natural_translation="Ich werde dich vermissen",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
                WordAlignment(source_word="te", target_word="dich", position=1),
                WordAlignment(source_word="extrañaré", target_word="vermissen-werde", position=2),
            ],
        )

        source_language = ls.get_language_by("es")
        target_language = ls.get_language_by("de")
        translation = Translation(
            title="Test",
            source_language=source_language,
            target_language=target_language,
            sentences=[sentence],
        )

        context = AlignmentContext(
            sentence=sentence,
            translation=translation,
            service=Mock(spec=TranslationService),
            is_new_translation=True,
        )

        editor = AlignmentEditor(context)
        target_words = editor._extract_target_words()

        # Both parts of hyphenated word should be included
        assert "vermissen" in target_words
        assert "werde" in target_words

    def test_build_alignments(self, alignment_context: AlignmentContext) -> None:
        """Test building alignments from editor state."""
        editor = AlignmentEditor(alignment_context)

        # Mock session state
        import streamlit as st

        editor_key = editor.editor_key
        st.session_state[editor_key] = {
            "0_Yo": ["Ich"],
            "1_te": ["dich"],
            "2_extrañaré": ["vermissen", "werde"],
        }

        source_words = ["Yo", "te", "extrañaré"]
        alignments = editor._build_alignments(source_words)

        assert len(alignments) == 3
        assert alignments[0].source_word == "Yo"
        assert alignments[0].target_word == "Ich"
        assert alignments[1].source_word == "te"
        assert alignments[1].target_word == "dich"
        assert alignments[2].source_word == "extrañaré"
        assert alignments[2].target_word == "vermissen-werde"

    def test_build_alignments_empty_target(self, alignment_context: AlignmentContext) -> None:
        """Test that alignments with empty targets are skipped."""
        editor = AlignmentEditor(alignment_context)

        # Mock session state with some empty targets
        import streamlit as st

        editor_key = editor.editor_key
        st.session_state[editor_key] = {
            "0_Yo": ["Ich"],
            "1_te": [],  # Empty target
            "2_extrañaré": ["vermissen", "werde"],
        }

        source_words = ["Yo", "te", "extrañaré"]
        alignments = editor._build_alignments(source_words)

        # Should only have 2 alignments (skipping the empty one)
        assert len(alignments) == 2
        assert alignments[0].source_word == "Yo"
        assert alignments[1].source_word == "extrañaré"


class TestExtractTargetWordsForPosition:
    """Tests for helper function _extract_target_words_for_position."""

    def test_extract_single_word(self) -> None:
        """Test extracting a single target word."""
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
        ]

        result = _extract_target_words_for_position(0, alignments)
        assert result == ["Ich"]

    def test_extract_hyphenated_words(self) -> None:
        """Test extracting hyphenated target words."""
        alignments = [
            WordAlignment(source_word="extrañaré", target_word="vermissen-werde", position=0),
        ]

        result = _extract_target_words_for_position(0, alignments)
        assert result == ["vermissen", "werde"]

    def test_extract_nonexistent_position(self) -> None:
        """Test extracting from a position that doesn't exist."""
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
        ]

        result = _extract_target_words_for_position(99, alignments)
        assert result == []

    def test_extract_with_whitespace(self) -> None:
        """Test that whitespace is stripped from extracted words."""
        alignments = [
            WordAlignment(source_word="test", target_word=" word1 - word2 ", position=0),
        ]

        result = _extract_target_words_for_position(0, alignments)
        assert result == ["word1", "word2"]
        assert " " not in result
        assert "" not in result

    def test_extract_empty_target(self) -> None:
        """Test extracting when target is empty or whitespace."""
        alignments = [
            WordAlignment(source_word="test", target_word=" - - ", position=0),
        ]

        result = _extract_target_words_for_position(0, alignments)
        # Should filter out empty strings
        assert result == []
