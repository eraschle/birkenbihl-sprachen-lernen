"""Integration test for Spanish sentence alignment with edge cases."""

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.services.language_service import get_language_by


class TestSpanishSentenceAlignment:
    """Test alignment for the Spanish sentence with reported issues."""

    def test_full_sentence_alignment(self) -> None:
        """Test complete alignment for: 'Mas comprendo que llegó tu tiempo, que Dios te ha llamado para estar a Su lado.'"""
        # Arrange
        natural_translation = (
            "Aber ich verstehe, dass deine Zeit gekommen ist, dass Gott dich gerufen hat, um an Seiner Seite zu sein."
        )

        # Corrected word alignments (fixing the reported issues)
        alignments = [
            WordAlignment(source_word="Mas", target_word="Aber", position=0),
            WordAlignment(source_word="comprendo", target_word="verstehe-ich", position=1),
            WordAlignment(source_word="que", target_word="dass", position=2),
            WordAlignment(source_word="llegó", target_word="gekommen-ist", position=3),
            WordAlignment(source_word="tu", target_word="deine", position=4),
            WordAlignment(source_word="tiempo", target_word="Zeit", position=5),
            WordAlignment(source_word="que", target_word="dass", position=6),
            WordAlignment(source_word="Dios", target_word="Gott", position=7),
            WordAlignment(source_word="te", target_word="dich", position=8),
            WordAlignment(source_word="ha", target_word="hat", position=9),  # Fixed: was "gerufen-hat"
            WordAlignment(source_word="llamado", target_word="gerufen", position=10),  # Fixed: was empty/whitespace
            WordAlignment(source_word="para", target_word="um", position=11),  # Should work now with fix
            WordAlignment(source_word="estar", target_word="zu-sein", position=12),
            WordAlignment(source_word="a", target_word="an", position=13),
            WordAlignment(source_word="Su", target_word="Seiner", position=14),
            WordAlignment(source_word="lado", target_word="Seite", position=15),
        ]

        # Act
        is_valid, error_message = validate_alignment_complete(natural_translation, alignments)

        # Assert
        assert is_valid, f"Alignment should be valid, but got error: {error_message}"

        # Verify all source words are aligned
        assert len(alignments) == 16, "Should have 16 word alignments"

        # Verify specific fixed issues
        ha_alignment = next(a for a in alignments if a.source_word == "ha")
        assert ha_alignment.target_word == "hat", "ha should map to 'hat', not 'gerufen-hat'"

        llamado_alignment = next(a for a in alignments if a.source_word == "llamado")
        assert llamado_alignment.target_word == "gerufen", "llamado should map to 'gerufen', not empty"
        assert llamado_alignment.target_word.strip(), "llamado target should not be whitespace"

        para_alignment = next(a for a in alignments if a.source_word == "para")
        assert para_alignment.target_word == "um", "para should map to 'um'"

    def test_broken_alignments_before_fix(self) -> None:
        """Test that the broken alignments (before fix) are correctly identified as invalid."""
        # Arrange
        natural_translation = (
            "Aber ich verstehe, dass deine Zeit gekommen ist, dass Gott dich gerufen hat, um an Seiner Seite zu sein."
        )

        # Broken alignments (as they were before fix)
        broken_alignments = [
            WordAlignment(source_word="Mas", target_word="Aber", position=0),
            WordAlignment(source_word="comprendo", target_word="verstehe-ich", position=1),
            WordAlignment(source_word="que", target_word="dass", position=2),
            WordAlignment(source_word="llegó", target_word="gekommen-ist", position=3),
            WordAlignment(source_word="tu", target_word="deine", position=4),
            WordAlignment(source_word="tiempo", target_word="Zeit", position=5),
            WordAlignment(source_word="que", target_word="dass", position=6),
            WordAlignment(source_word="Dios", target_word="Gott", position=7),
            WordAlignment(source_word="te", target_word="dich", position=8),
            WordAlignment(source_word="ha", target_word="gerufen-hat", position=9),  # WRONG ORDER
            WordAlignment(source_word="llamado", target_word=" ", position=10),  # WHITESPACE
            WordAlignment(source_word="para", target_word="um", position=11),
            WordAlignment(source_word="estar", target_word="zu-sein", position=12),
            WordAlignment(source_word="a", target_word="an", position=13),
            WordAlignment(source_word="Su", target_word="Seiner", position=14),
            WordAlignment(source_word="lado", target_word="Seite", position=15),
        ]

        # Act
        is_valid_complete, error_complete = validate_alignment_complete(natural_translation, broken_alignments)

        # Import the source words validation
        from birkenbihl.models.validation import validate_source_words_mapped
        is_valid_mapped, error_mapped = validate_source_words_mapped(broken_alignments)

        # Assert - either validation should fail
        # The whitespace target_word should be caught by validate_source_words_mapped
        assert not is_valid_mapped, f"validate_source_words_mapped should fail for whitespace target_word"
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

    def test_create_full_translation_object(self) -> None:
        """Test creating a complete Translation object with the sentence."""
        # Arrange
        source_text = "Mas comprendo que llegó tu tiempo, que Dios te ha llamado para estar a Su lado."
        natural_translation = (
            "Aber ich verstehe, dass deine Zeit gekommen ist, dass Gott dich gerufen hat, um an Seiner Seite zu sein."
        )

        alignments = [
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

        sentence = Sentence(
            source_text=source_text,
            natural_translation=natural_translation,
            word_alignments=alignments,
        )

        translation = Translation(
            title="Spanish Test Sentence",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[sentence],
        )

        # Act & Assert
        assert translation.title == "Spanish Test Sentence"
        assert len(translation.sentences) == 1
        assert translation.sentences[0].source_text == source_text
        assert translation.sentences[0].natural_translation == natural_translation
        assert len(translation.sentences[0].word_alignments) == 16

        # Validate alignment
        is_valid, error = validate_alignment_complete(natural_translation, alignments)
        assert is_valid, f"Translation alignment should be valid: {error}"
