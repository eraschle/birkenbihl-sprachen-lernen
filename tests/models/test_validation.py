"""Tests for translation validation functions."""

from birkenbihl.models.translation import WordAlignment
from birkenbihl.models.validation import validate_alignment_complete, validate_source_words_mapped


class TestValidateAlignmentComplete:
    """Tests for validate_alignment_complete function."""

    def test_validate_alignment_complete_success(self) -> None:
        """Test successful validation with all words present."""
        natural = "Ich werde dich vermissen"
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde", position=2),
            WordAlignment(source_word="extrañaré", target_word="vermissen", position=3),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_complete_with_hyphenated_words(self) -> None:
        """Test validation with hyphenated target words."""
        natural = "Ich werde dich vermissen"
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_complete_missing_words(self) -> None:
        """Test validation fails when words are missing."""
        natural = "Ich werde dich vermissen"
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is False
        assert error is not None
        assert "dich" in error.lower()
        assert "fehlende" in error.lower()

    def test_validate_alignment_complete_extra_words(self) -> None:
        """Test validation fails when extra words are present."""
        natural = "Ich werde dich vermissen"
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
            WordAlignment(source_word="mucho", target_word="sehr", position=3),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is False
        assert error is not None
        assert "sehr" in error.lower()
        assert "zusätzliche" in error.lower()

    def test_validate_alignment_with_punctuation(self) -> None:
        """Test validation ignores punctuation."""
        natural = "Hallo, wie geht's dir?"
        alignments = [
            WordAlignment(source_word="Hello", target_word="Hallo", position=0),
            WordAlignment(source_word="how", target_word="wie", position=1),
            WordAlignment(source_word="are", target_word="geht's", position=2),
            WordAlignment(source_word="you", target_word="dir", position=3),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_case_insensitive(self) -> None:
        """Test validation is case-insensitive."""
        natural = "ICH werde DICH vermissen"
        alignments = [
            WordAlignment(source_word="Yo", target_word="ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="WERDE-VERMISSEN", position=2),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_empty_natural(self) -> None:
        """Test validation with empty natural translation."""
        natural = ""
        alignments = []

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_empty_natural_with_alignments(self) -> None:
        """Test validation fails when natural is empty but alignments exist."""
        natural = ""
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is False
        assert error is not None

    def test_validate_alignment_empty_alignments(self) -> None:
        """Test validation fails when alignments are empty but natural is not."""
        natural = "Ich werde dich vermissen"
        alignments = []

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is False
        assert error is not None
        assert "keine alignments" in error.lower()

    def test_validate_alignment_whitespace_natural(self) -> None:
        """Test validation with only whitespace in natural translation."""
        natural = "   "
        alignments = []

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_complex_hyphenation(self) -> None:
        """Test validation with multiple hyphenated words."""
        natural = "Das war ein sehr schöner Moment"
        alignments = [
            WordAlignment(source_word="Eso", target_word="Das", position=0),
            WordAlignment(source_word="fue", target_word="war", position=1),
            WordAlignment(source_word="un", target_word="ein", position=2),
            WordAlignment(source_word="muy", target_word="sehr", position=3),
            WordAlignment(source_word="bello", target_word="schöner", position=4),
            WordAlignment(source_word="momento", target_word="Moment", position=5),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is True
        assert error is None

    def test_validate_alignment_missing_and_extra_words(self) -> None:
        """Test validation when both missing and extra words exist."""
        natural = "Ich werde dich vermissen"
        alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
            WordAlignment(source_word="mucho", target_word="sehr", position=3),
        ]

        is_valid, error = validate_alignment_complete(natural, alignments)

        assert is_valid is False
        assert error is not None
        assert "dich" in error.lower()
        assert "sehr" in error.lower()
        assert "fehlende" in error.lower()
        assert "zusätzliche" in error.lower()


class TestValidateSourceWordsMapped:
    """Tests for validate_source_words_mapped function."""

    def test_all_source_words_mapped(self) -> None:
        """Test successful validation when all source words have targets."""
        alignments = [
            WordAlignment(source_word="no", target_word="nicht", position=0),
            WordAlignment(source_word="importante", target_word="wichtig", position=1),
        ]

        is_valid, error = validate_source_words_mapped(alignments)

        assert is_valid is True
        assert error is None

    def test_source_word_with_empty_target(self) -> None:
        """Test validation fails when source word has empty target."""
        alignments = [
            WordAlignment(source_word="no", target_word="", position=0),
            WordAlignment(source_word="importante", target_word="unwichtig", position=1),
        ]

        is_valid, error = validate_source_words_mapped(alignments)

        assert is_valid is False
        assert error is not None
        assert "no" in error
        assert "quellwörter ohne zielwort" in error.lower()

    def test_source_word_with_whitespace_target(self) -> None:
        """Test validation fails when source word has only whitespace target."""
        alignments = [
            WordAlignment(source_word="ha", target_word="gerufen-hat", position=0),
            WordAlignment(source_word="llamado", target_word=" ", position=1),
        ]

        is_valid, error = validate_source_words_mapped(alignments)

        assert is_valid is False
        assert error is not None
        assert "llamado" in error
        assert "quellwörter ohne zielwort" in error.lower()

    def test_multiple_unmapped_source_words(self) -> None:
        """Test validation reports all unmapped source words."""
        alignments = [
            WordAlignment(source_word="ha", target_word="", position=0),
            WordAlignment(source_word="llamado", target_word=" ", position=1),
            WordAlignment(source_word="para", target_word="um", position=2),
        ]

        is_valid, error = validate_source_words_mapped(alignments)

        assert is_valid is False
        assert error is not None
        assert "ha" in error
        assert "llamado" in error
        assert "quellwörter ohne zielwort" in error.lower()

    def test_hyphenated_target_words_valid(self) -> None:
        """Test that hyphenated target words are considered valid mappings."""
        alignments = [
            WordAlignment(source_word="I've", target_word="Ich-habe", position=0),
            WordAlignment(source_word="met", target_word="getroffen", position=1),
        ]

        is_valid, error = validate_source_words_mapped(alignments)

        assert is_valid is True
        assert error is None

    def test_empty_alignments_list(self) -> None:
        """Test validation with empty alignments list."""
        alignments = []

        is_valid, error = validate_source_words_mapped(alignments)

        assert is_valid is True
        assert error is None
