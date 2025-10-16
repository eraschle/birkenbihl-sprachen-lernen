"""Tests for text extraction and normalization utilities."""

import pytest

from birkenbihl.utils.text_extractor import (
    clean_trailing_punctuation,
    extract_normalized_words,
    normalize_word_for_matching,
    split_hyphenated,
    split_into_sentences,
)


class TestExtractNormalizedWords:
    """Tests for extract_normalized_words() - Extract and normalize words from text."""

    @pytest.mark.parametrize(
        "input_text,expected,description",
        [
            # Basic cases
            ("Hello world", ["hello", "world"], "basic words"),
            ("Hello, world!", ["hello", "world"], "with punctuation"),
            ("one two three", ["one", "two", "three"], "multiple words"),
            # Special characters to preserve
            ("don't worry", ["don't", "worry"], "apostrophes preserved"),
            ("I've been there", ["i've", "been", "there"], "contractions preserved"),
            ("word-by-word", ["word-by-word"], "hyphens preserved"),
            ("mother-in-law", ["mother-in-law"], "compound with hyphens"),
            # Abbreviations (dots removed, but letters kept)
            ("U.S.A. rocks", ["usa", "rocks"], "abbreviation dots removed"),
            ("Mr. Smith", ["mr", "smith"], "title abbreviation"),
            # International characters
            ("¿Qué pasa?", ["qué", "pasa"], "Spanish inverted question mark"),
            ("Hola, ¿cómo estás?", ["hola", "cómo", "estás"], "Spanish with accents"),
            # Quotes and brackets
            ('"Hello" world', ["hello", "world"], "double quotes removed"),
            ("(test) word", ["test", "word"], "parentheses removed"),
            ("[foo] bar", ["foo", "bar"], "square brackets removed"),
            # Mixed punctuation
            ("Hello, world! How are you?", ["hello", "world", "how", "are", "you"], "mixed punctuation"),
            ("Test... more text!", ["test", "more", "text"], "ellipsis removed"),
            # Edge cases
            ("", [], "empty string"),
            ("   ", [], "only whitespace"),
            ("!!!", [], "only punctuation"),
            (".,;:!?", [], "various punctuation only"),
            ("   hello   ", ["hello"], "leading and trailing whitespace"),
        ],
    )
    def test_various_cases(self, input_text: str, expected: list[str], description: str) -> None:
        result = extract_normalized_words(input_text)
        assert result == expected, f"Failed: {description}"


class TestNormalizeWordForMatching:
    """Tests for normalize_word_for_matching() - Normalize single word for comparison."""

    @pytest.mark.parametrize(
        "input_word,expected,description",
        [
            # Basic normalization
            ("Hello", "hello", "uppercase to lowercase"),
            ("WORLD", "world", "all caps to lowercase"),
            ("TeSt", "test", "mixed case to lowercase"),
            # Whitespace handling
            ("  word  ", "word", "leading and trailing spaces"),
            ("\ttest\t", "test", "tabs removed"),
            ("  HELLO  ", "hello", "spaces and uppercase"),
            # Edge cases
            ("", "", "empty string"),
            ("   ", "", "only whitespace"),
            ("a", "a", "single character"),
        ],
    )
    def test_normalization_cases(self, input_word: str, expected: str, description: str) -> None:
        result = normalize_word_for_matching(input_word)
        assert result == expected, f"Failed: {description}"


class TestSplitHyphenated:
    """Tests for split_hyphenated() - Split hyphenated words and remove punctuation."""

    @pytest.mark.parametrize(
        "input_word,expected,description",
        [
            # Hyphenated words
            ("werde-vermissen", ["werde", "vermissen"], "basic hyphenated"),
            ("a-b-c", ["a", "b", "c"], "multiple hyphens"),
            ("mother-in-law", ["mother", "in", "law"], "compound with multiple hyphens"),
            ("Es-ist", ["Es", "ist"], "German contraction - case preserved"),
            # Single words
            ("hello", ["hello"], "single word no hyphen"),
            ("test", ["test"], "simple word"),
            # With punctuation
            ("hello!", ["hello"], "trailing exclamation"),
            ("world.", ["world"], "trailing period"),
            ("test?", ["test"], "trailing question mark"),
            ("test-word!", ["test", "word"], "hyphenated with trailing punctuation"),
            ("hello,", ["hello"], "trailing comma"),
            # Apostrophes preserved
            ("don't-worry", ["don't", "worry"], "hyphenated with apostrophe"),
            ("it's-fine", ["it's", "fine"], "contraction in compound"),
            # Mixed punctuation
            ("(test)", ["test"], "parentheses removed"),
            ('"hello"', ["hello"], "quotes removed"),
            ("test...", ["test"], "ellipsis removed"),
            # Edge cases
            ("", [], "empty string"),
            ("-", [], "only hyphen"),
            ("---", [], "multiple hyphens only"),
            ("a-", ["a"], "trailing hyphen"),
            ("-b", ["b"], "leading hyphen"),
            ("!!!", [], "only punctuation"),
        ],
    )
    def test_splitting_cases(self, input_word: str, expected: list[str], description: str) -> None:
        result = split_hyphenated(input_word)
        assert result == expected, f"Failed: {description}"


class TestCleanTrailingPunctuation:
    """Tests for clean_trailing_punctuation() - Extract trailing punctuation from word."""

    @pytest.mark.parametrize(
        "input_word,expected_word,expected_punct,description",
        [
            # Single trailing punctuation
            ("world!", "world", "!", "trailing exclamation"),
            ("hello.", "hello", ".", "trailing period"),
            ("test?", "test", "?", "trailing question mark"),
            ("word,", "word", ",", "trailing comma"),
            ("text;", "text", ";", "trailing semicolon"),
            ("hello:", "hello", ":", "trailing colon"),
            # Multiple trailing punctuation
            ("hello...", "hello", "...", "ellipsis"),
            ("test!?", "test", "!?", "multiple punctuation"),
            ("word!!", "word", "!!", "double exclamation"),
            ("test?!", "test", "?!", "question and exclamation"),
            # No trailing punctuation
            ("test", "test", "", "no punctuation"),
            ("hello", "hello", "", "plain word"),
            ("world123", "world123", "", "word with numbers"),
            # Apostrophes - regex treats as punctuation
            ("runnin'", "runnin", "'", "apostrophe at end treated as punctuation by regex"),
            ("don't", "don't", "", "apostrophe in middle NOT trailing - returns full word"),
            # Only punctuation
            ("!", "", "!", "only exclamation"),
            ("...", "", "...", "only ellipsis"),
            ("!?", "", "!?", "only mixed punctuation"),
            # Edge cases
            ("", "", "", "empty string"),
            ("   ", "", "   ", "whitespace treated as trailing punctuation"),
            ("a", "a", "", "single letter"),
        ],
    )
    def test_punctuation_extraction(
        self, input_word: str, expected_word: str, expected_punct: str, description: str
    ) -> None:
        word, punct = clean_trailing_punctuation(input_word)
        assert word == expected_word, f"Failed word extraction: {description}"
        assert punct == expected_punct, f"Failed punctuation extraction: {description}"


class TestSplitIntoSentences:
    """Tests for split_into_sentences() - Split text into sentences.

    The function uses pattern: r"(?<=[.!?])\s+(?=[A-Z])"
    This means: Split after .!? when followed by whitespace AND capital letter.
    """

    @pytest.mark.parametrize(
        "input_text,expected,description",
        [
            # Normal cases - should split
            ("Hello world. How are you?", ["Hello world.", "How are you?"], "two sentences with period and question"),
            ("First! Second? Third.", ["First!", "Second?", "Third."], "mixed terminators"),
            ("One. Two. Three.", ["One.", "Two.", "Three."], "three short sentences"),
            (
                "This is sentence one. This is sentence two.",
                ["This is sentence one.", "This is sentence two."],
                "longer sentences",
            ),
            # Single sentence
            ("Hello world", ["Hello world"], "no terminator"),
            ("Just one sentence.", ["Just one sentence."], "one sentence with period"),
            ("Only this!", ["Only this!"], "one sentence with exclamation"),
            # Abbreviations - LIMITATION: Function DOES split on capital letter after period!
            ("Mr. Smith went home.", ["Mr.", "Smith went home."], "Mr. abbreviation - splits incorrectly"),
            ("Dr. Jones is here.", ["Dr.", "Jones is here."], "Dr. abbreviation - splits incorrectly"),
            ("Mrs. Johnson called.", ["Mrs.", "Johnson called."], "Mrs. abbreviation - splits incorrectly"),
            (
                "I live in the U.S.A. and love it.",
                ["I live in the U.S.A. and love it."],
                "U.S.A. with lowercase after - does NOT split",
            ),
            (
                "The U.S. is big. Canada too.",
                ["The U.S. is big.", "Canada too."],
                "U.S. mid-sentence then capital",
            ),
            # Lowercase after terminator - should NOT split
            ("Test. lowercase", ["Test. lowercase"], "lowercase after period prevents split"),
            ("End! no capital", ["End! no capital"], "lowercase after exclamation"),
            ("Really? yes", ["Really? yes"], "lowercase after question"),
            # Whitespace variations
            ("First.  Second.", ["First.", "Second."], "multiple spaces"),
            ("First.   Third.", ["First.", "Third."], "many spaces"),
            ("One.\tTwo.", ["One.", "Two."], "tab between sentences"),
            ("First.\nSecond.", ["First.", "Second."], "newline between sentences"),
            ("A.\n\nB.", ["A.", "B."], "double newline"),
            # International
            ("¿Cómo estás? Bien.", ["¿Cómo estás?", "Bien."], "Spanish inverted question mark"),
            ("¡Hola! ¿Qué tal?", ["¡Hola! ¿Qué tal?"], "Spanish - no capital after exclamation, no split"),
            # Mixed cases
            ("Hello. World! How? Good.", ["Hello.", "World!", "How?", "Good."], "all terminators"),
            # Edge cases
            ("", [], "empty string"),
            ("   ", [], "only whitespace"),
            ("No period at end", ["No period at end"], "no sentence terminator"),
            ("...", ["..."], "only ellipsis"),
            ("Test.", ["Test."], "single sentence with period"),
            # Extra whitespace in input
            ("  Hello. World.  ", ["Hello.", "World."], "leading and trailing whitespace"),
            # Numbers and special characters
            ("Version 1.0 is out. Get it now!", ["Version 1.0 is out.", "Get it now!"], "decimal number"),
            ("Price is $5.99. Buy now!", ["Price is $5.99.", "Buy now!"], "price format"),
        ],
    )
    def test_sentence_splitting(self, input_text: str, expected: list[str], description: str) -> None:
        result = split_into_sentences(input_text)
        assert result == expected, f"Failed: {description}"
