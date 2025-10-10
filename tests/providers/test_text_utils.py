"""Tests for text processing utilities."""

import pytest

from birkenbihl.providers import text_utils
from birkenbihl.providers.models import SentenceResponse, WordAlignmentResponse


class TestSplitIntoSentences:
    """Test sentence splitting functionality."""

    def test_single_sentence(self):
        """Test text with single sentence."""
        text = "Hello world"
        result = text_utils.split_into_sentences(text)
        assert result == ["Hello world"]

    def test_two_sentences_period(self):
        """Test text with two sentences separated by period."""
        text = "Hello world. How are you?"
        result = text_utils.split_into_sentences(text)
        assert result == ["Hello world.", "How are you?"]

    def test_multiple_sentences_mixed_terminators(self):
        """Test text with multiple sentence terminators."""
        text = "First sentence! Second sentence? Third sentence."
        result = text_utils.split_into_sentences(text)
        assert result == ["First sentence!", "Second sentence?", "Third sentence."]

    def test_sentence_with_exclamation(self):
        """Test exclamation mark as sentence terminator."""
        text = "Wow! Amazing!"
        result = text_utils.split_into_sentences(text)
        assert result == ["Wow!", "Amazing!"]

    def test_sentence_with_question(self):
        """Test question mark as sentence terminator."""
        text = "Are you ready? Yes I am."
        result = text_utils.split_into_sentences(text)
        assert result == ["Are you ready?", "Yes I am."]

    def test_empty_string(self):
        """Test empty string."""
        text = ""
        result = text_utils.split_into_sentences(text)
        assert result == []

    def test_whitespace_only(self):
        """Test string with only whitespace."""
        text = "   \n\t  "
        result = text_utils.split_into_sentences(text)
        assert result == []

    def test_sentence_with_extra_whitespace(self):
        """Test sentences with extra whitespace."""
        text = "First sentence.    Second sentence."
        result = text_utils.split_into_sentences(text)
        assert result == ["First sentence.", "Second sentence."]

    def test_sentence_without_terminator(self):
        """Test sentence without terminating punctuation."""
        text = "No terminator here"
        result = text_utils.split_into_sentences(text)
        assert result == ["No terminator here"]

    def test_lowercase_after_period_not_split(self):
        """Test that capital after period triggers split (even for abbreviations)."""
        text = "Mr. Smith went to the store."
        result = text_utils.split_into_sentences(text)
        # Note: Simple regex splits on "Mr. S" - abbreviation detection would be complex
        # For our use case (translating full sentences), this is acceptable
        assert len(result) == 2
        assert "Mr." in result[0]
        assert "Smith" in result[1]

    def test_multiple_spaces_between_sentences(self):
        """Test multiple spaces between sentences."""
        text = "First.     Second."
        result = text_utils.split_into_sentences(text)
        assert result == ["First.", "Second."]

    def test_newline_between_sentences(self):
        """Test newline between sentences."""
        text = "First sentence.\nSecond sentence."
        result = text_utils.split_into_sentences(text)
        assert result == ["First sentence.", "Second sentence."]

    def test_three_sentences(self):
        """Test text with three distinct sentences."""
        text = "One. Two. Three."
        result = text_utils.split_into_sentences(text)
        assert result == ["One.", "Two.", "Three."]

    def test_spanish_text(self):
        """Test splitting Spanish text (with capital letters)."""
        text = "Hola mundo. Cómo estás?"
        result = text_utils.split_into_sentences(text)
        assert result == ["Hola mundo.", "Cómo estás?"]

    def test_german_text(self):
        """Test splitting German text."""
        text = "Hallo Welt. Wie geht es dir?"
        result = text_utils.split_into_sentences(text)
        assert result == ["Hallo Welt.", "Wie geht es dir?"]

    def test_complex_text_with_numbers(self):
        """Test text with numbers and abbreviations."""
        text = "I have 3 apples. She has 5 oranges."
        result = text_utils.split_into_sentences(text)
        assert result == ["I have 3 apples.", "She has 5 oranges."]


class TestRedistributeMergedTranslation:
    """Test redistribution of merged translation responses."""

    def test_simple_two_sentence_split(self):
        """Test basic splitting of two merged sentences."""
        merged = SentenceResponse(
            source_text="Hello world. How are you",
            natural_translation="Hallo Welt. Wie geht es dir",
            word_alignments=[
                WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
                WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
                WordAlignmentResponse(source_word="How", target_word="Wie", position=2),
                WordAlignmentResponse(source_word="are", target_word="geht-es", position=3),
                WordAlignmentResponse(source_word="you", target_word="dir", position=4),
            ],
        )

        source_sentences = ["Hello world", "How are you"]
        result = text_utils.redistribute_merged_translation(merged, source_sentences)

        # Verify we got 2 sentences
        assert len(result) == 2

        # Verify first sentence
        assert result[0].source_text == "Hello world"
        assert result[0].natural_translation == "Hallo Welt."
        assert len(result[0].word_alignments) == 2
        assert result[0].word_alignments[0].source_word == "Hello"
        assert result[0].word_alignments[0].target_word == "Hallo"
        assert result[0].word_alignments[0].position == 0
        assert result[0].word_alignments[1].position == 1

        # Verify second sentence
        assert result[1].source_text == "How are you"
        assert result[1].natural_translation == "Wie geht es dir"
        assert len(result[1].word_alignments) == 3

        # Verify hyphenated word stays intact
        assert result[1].word_alignments[1].source_word == "are"
        assert result[1].word_alignments[1].target_word == "geht-es"
        assert result[1].word_alignments[1].position == 1

        # Verify positions renumbered
        assert result[1].word_alignments[0].position == 0
        assert result[1].word_alignments[1].position == 1
        assert result[1].word_alignments[2].position == 2

    def test_three_sentence_split(self):
        """Test splitting three merged sentences."""
        merged = SentenceResponse(
            source_text="One. Two. Three.",
            natural_translation="Eins. Zwei. Drei.",
            word_alignments=[
                WordAlignmentResponse(source_word="One", target_word="Eins", position=0),
                WordAlignmentResponse(source_word="Two", target_word="Zwei", position=1),
                WordAlignmentResponse(source_word="Three", target_word="Drei", position=2),
            ],
        )

        source_sentences = ["One", "Two", "Three"]
        result = text_utils.redistribute_merged_translation(merged, source_sentences)

        assert len(result) == 3
        assert result[0].natural_translation == "Eins."
        assert result[1].natural_translation == "Zwei."
        assert result[2].natural_translation == "Drei."

    def test_case_insensitive_matching(self):
        """Test that source_word matching is case-insensitive."""
        merged = SentenceResponse(
            source_text="hello WORLD. how ARE you",
            natural_translation="Hallo Welt. Wie geht es dir",
            word_alignments=[
                WordAlignmentResponse(source_word="hello", target_word="Hallo", position=0),
                WordAlignmentResponse(source_word="WORLD", target_word="Welt", position=1),
                WordAlignmentResponse(source_word="how", target_word="Wie", position=2),
                WordAlignmentResponse(source_word="ARE", target_word="geht-es", position=3),
                WordAlignmentResponse(source_word="you", target_word="dir", position=4),
            ],
        )

        source_sentences = ["hello WORLD", "how ARE you"]
        result = text_utils.redistribute_merged_translation(merged, source_sentences)

        assert len(result) == 2
        assert len(result[0].word_alignments) == 2
        assert len(result[1].word_alignments) == 3

    def test_mismatch_sentence_count_raises_error(self):
        """Test that mismatched sentence counts raise ValueError."""
        merged = SentenceResponse(
            source_text="Hello world",
            natural_translation="Hallo Welt",
            word_alignments=[
                WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
                WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
            ],
        )

        # Expect 2 sentences but natural only has 1
        source_sentences = ["Hello", "world"]

        with pytest.raises(ValueError, match="Natural translation split into 1 sentences but expected 2"):
            text_utils.redistribute_merged_translation(merged, source_sentences)

    def test_unknown_source_word_raises_error(self):
        """Test that unknown source_word raises ValueError."""
        merged = SentenceResponse(
            source_text="Hello world",
            natural_translation="Hallo Welt",
            word_alignments=[
                WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
                WordAlignmentResponse(source_word="UNKNOWN", target_word="Welt", position=1),
            ],
        )

        source_sentences = ["Hello world"]

        with pytest.raises(ValueError, match="Could not match source_word 'UNKNOWN'"):
            text_utils.redistribute_merged_translation(merged, source_sentences)
