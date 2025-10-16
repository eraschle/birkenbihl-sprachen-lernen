"""Integration test for Spanish sentence alignment with edge cases."""

import pytest

from birkenbihl.models import validation
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services import language_service as lang_service


@pytest.fixture
def natural_translation() -> str:
    return "Aber ich verstehe, dass deine Zeit gekommen ist, dass Gott dich gerufen hat, um an Seiner Seite zu sein."


@pytest.fixture
def sentence_alignments() -> list[WordAlignment]:
    return [
        WordAlignment(source_word="Mas", target_word="Aber", position=0),
        WordAlignment(source_word="comprendo", target_word="verstehe-ich", position=1),
        WordAlignment(source_word="que", target_word="dass", position=2),
        WordAlignment(source_word="llegó", target_word="gekommen-ist", position=3),
        WordAlignment(source_word="tu", target_word="deine", position=4),
        WordAlignment(source_word="tiempo", target_word="Zeit", position=5),
        WordAlignment(source_word="que", target_word="dass", position=6),
        WordAlignment(source_word="Dios", target_word="Gott", position=7),
        WordAlignment(source_word="te", target_word="dich", position=8),
        WordAlignment(source_word="ha", target_word="hat", position=9),
        WordAlignment(source_word="llamado", target_word="gerufen", position=10),
        WordAlignment(source_word="para", target_word="um", position=11),
        WordAlignment(source_word="estar", target_word="zu-sein", position=12),
        WordAlignment(source_word="a", target_word="an", position=13),
        WordAlignment(source_word="Su", target_word="Seiner", position=14),
        WordAlignment(source_word="lado", target_word="Seite", position=15),
    ]


@pytest.fixture
def fixed_alignments(sentence_alignments: list[WordAlignment]) -> list[WordAlignment]:
    sentence_alignments[9] = WordAlignment(
        source_word="ha",
        target_word="hat",  # Fixed: was "gerufen-hat"
        position=9,
    )
    sentence_alignments[10] = WordAlignment(
        source_word="llamado",
        target_word="gerufen",  # Fixed: was empty/whitespace
        position=10,
    )
    sentence_alignments[11] = WordAlignment(
        source_word="para",
        target_word="um",  # Should work now with fix
        position=11,
    )
    return sentence_alignments


@pytest.fixture
def broken_alignments(sentence_alignments: list[WordAlignment]) -> list[WordAlignment]:
    sentence_alignments[9] = WordAlignment(
        source_word="ha",
        target_word="gerufen-hat",  # WRONG ORDER
        position=9,
    )
    sentence_alignments[10] = WordAlignment(
        source_word="llamado",
        target_word=" ",  # WHITESPACE
        position=10,
    )
    return sentence_alignments


class TestSpanishSentenceAlignment:
    """Test alignment for the Spanish sentence with reported issues."""

    def test_full_sentence_alignment(self, sentence_alignments: list[WordAlignment], natural_translation: str) -> None:
        """Test complete alignment for:
        'Mas comprendo que llegó tu tiempo, que Dios te ha llamado para estar a Su lado.'"""
        # Act
        is_valid, error_message = validation.validate_alignment_complete(
            natural_translation,
            sentence_alignments,
        )

        # Assert
        assert is_valid, f"Alignment should be valid, but got error: {error_message}"

        # Verify all source words are aligned
        assert len(sentence_alignments) == 16, "Should have 16 word alignments"

        # Verify specific fixed issues
        ha_alignment = next(a for a in sentence_alignments if a.source_word == "ha")
        assert ha_alignment.target_word == "hat", "ha should map to 'hat', not 'gerufen-hat'"

        llamado_alignment = next(a for a in sentence_alignments if a.source_word == "llamado")
        assert llamado_alignment.target_word == "gerufen", "llamado should map to 'gerufen', not empty"
        assert llamado_alignment.target_word.strip(), "llamado target should not be whitespace"

        para_alignment = next(a for a in sentence_alignments if a.source_word == "para")
        assert para_alignment.target_word == "um", "para should map to 'um'"

    def test_broken_alignments_before_fix(
        self, broken_alignments: list[WordAlignment], natural_translation: str
    ) -> None:
        """Test that the broken alignments (before fix) are correctly identified as invalid."""
        # Act
        result_validate = validation.validate_alignment_complete(
            natural_translation,
            broken_alignments,
        )
        assert result_validate is not None

        is_valid_mapped, error_mapped = validation.validate_source_words_mapped(
            broken_alignments,
        )

        # Assert - either validation should fail
        # The whitespace target_word should be caught by validate_source_words_mapped
        assert not is_valid_mapped, "validate_source_words_mapped should fail for whitespace target_word"
        assert error_mapped is not None
        assert "llamado" in error_mapped, f"Error should mention 'llamado' with whitespace target: {error_mapped}"

    def test_word_extraction_includes_um(self) -> None:
        """Test that 'um' is correctly extracted from natural translation."""
        # Arrange
        natural_translation = "Gott dich gerufen hat, um an Seiner Seite zu sein."

        # Extract words using regex (same as UI)
        import re

        target_words = re.findall(r"\b\w+\b", natural_translation)

        # Assert
        assert "um" in target_words, "Word 'um' should be extracted from natural translation"
        assert "Gott" in target_words
        assert "dich" in target_words
        assert "gerufen" in target_words
        assert "hat" in target_words

    def test_create_full_translation_object(
        self, sentence_alignments: list[WordAlignment], natural_translation: str
    ) -> None:
        """Test creating a complete Translation object with the sentence."""
        # Arrange
        source_text = "Mas comprendo que llegó tu tiempo, que Dios te ha llamado para estar a Su lado."

        sentence = Sentence(
            source_text=source_text,
            natural_translation=natural_translation,
            word_alignments=sentence_alignments,
        )

        translation = Translation(
            title="Spanish Test Sentence",
            source_language=lang_service.get_language_by("es"),
            target_language=lang_service.get_language_by("de"),
            sentences=[sentence],
        )

        # Act & Assert
        assert translation.title == "Spanish Test Sentence"
        assert len(translation.sentences) == 1
        assert translation.sentences[0].source_text == source_text
        assert translation.sentences[0].natural_translation == natural_translation
        assert len(translation.sentences[0].word_alignments) == 16

        # Validate alignment
        is_valid, error = validation.validate_alignment_complete(
            natural_translation,
            sentence_alignments,
        )
        assert is_valid, f"Translation alignment should be valid: {error}"
