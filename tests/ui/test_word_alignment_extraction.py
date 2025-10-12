"""Tests for word alignment extraction in UI."""

from birkenbihl.models.translation import WordAlignment


def test_extract_target_words_with_special_characters():
    """Test that target words include special cases like 'um' from 'um zu'."""
    # Arrange
    natural_translation = (
        "Aber ich verstehe, dass deine Zeit gekommen ist, dass Gott dich gerufen hat, um an Seiner Seite zu sein."
    )

    # Word alignments as they might come from the AI
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

    # Extract target words using the same logic as in the UI
    import re

    target_words = re.findall(r"\b\w+\b", natural_translation)

    # Also include all words from existing alignments
    existing_target_words = set()
    for alignment in alignments:
        existing_target_words.update(alignment.target_word.split("-"))

    # Combine both sets
    target_words_set = set(target_words)
    for word in existing_target_words:
        if word not in target_words_set:
            target_words.append(word)
            target_words_set.add(word)

    # Assert
    assert "um" in target_words, "Word 'um' should be in target_words"
    assert "dich" in target_words, "Word 'dich' should be in target_words"
    assert "hat" in target_words, "Word 'hat' should be in target_words"
    assert "gerufen" in target_words, "Word 'gerufen' should be in target_words"

    # Check that all alignment target words are in the options
    for alignment in alignments:
        for word in alignment.target_word.split("-"):
            assert word in target_words, f"Word '{word}' from alignment should be in target_words"


def test_no_empty_or_whitespace_alignments():
    """Test that alignments don't contain empty strings or whitespace."""
    # Arrange
    natural_translation = "Aber ich verstehe, dass Gott dich gerufen hat, um zu sein."

    # Problematic alignments with whitespace
    alignments = [
        WordAlignment(source_word="Mas", target_word="Aber", position=0),
        WordAlignment(source_word="comprendo", target_word="verstehe-ich", position=1),
        WordAlignment(source_word="que", target_word="dass", position=2),
        WordAlignment(source_word="Dios", target_word="Gott", position=3),
        WordAlignment(source_word="te", target_word="dich", position=4),
        WordAlignment(source_word="ha", target_word="hat", position=5),
        WordAlignment(source_word="llamado", target_word=" ", position=6),  # Whitespace - BAD!
        WordAlignment(source_word="para", target_word="um", position=7),
        WordAlignment(source_word="estar", target_word="zu-sein", position=8),
    ]

    # Extract target words
    import re

    target_words = re.findall(r"\b\w+\b", natural_translation)

    # Include existing alignment words (filter out whitespace)
    existing_target_words = set()
    for alignment in alignments:
        # Split and filter out empty/whitespace words
        words = [w.strip() for w in alignment.target_word.split("-")]
        words = [w for w in words if w]  # Filter empty strings
        existing_target_words.update(words)

    # Combine both sets
    target_words_set = set(target_words)
    for word in existing_target_words:
        if word not in target_words_set:
            target_words.append(word)
            target_words_set.add(word)

    # Assert: whitespace should not be in target_words
    assert " " not in target_words, "Whitespace should not be in target_words"
    assert "" not in target_words, "Empty string should not be in target_words"

    # All valid words should be present
    assert "Aber" in target_words
    assert "um" in target_words


def test_wrong_word_order_in_alignment():
    """Test alignment where word order was confused (ha -> gerufen-hat instead of hat)."""
    # Arrange
    natural_translation = "Gott hat dich gerufen"

    # Wrong alignment (ha -> gerufen-hat means wrong order)
    wrong_alignments = [
        WordAlignment(source_word="Dios", target_word="Gott", position=0),
        WordAlignment(source_word="ha", target_word="gerufen-hat", position=1),  # WRONG ORDER
        WordAlignment(source_word="te", target_word="dich", position=2),
        WordAlignment(source_word="llamado", target_word="", position=3),  # MISSING
    ]

    # Correct alignment
    correct_alignments = [
        WordAlignment(source_word="Dios", target_word="Gott", position=0),
        WordAlignment(source_word="ha", target_word="hat", position=1),  # CORRECT
        WordAlignment(source_word="te", target_word="dich", position=2),
        WordAlignment(source_word="llamado", target_word="gerufen", position=3),  # CORRECT
    ]

    # Check validation
    from birkenbihl.models.validation import validate_alignment_complete

    # Wrong alignment should be invalid (wrong order)
    is_valid, error = validate_alignment_complete(natural_translation, wrong_alignments)
    assert not is_valid, "Wrong word order should be invalid"

    # Correct alignment should be valid
    is_valid, error = validate_alignment_complete(natural_translation, correct_alignments)
    assert is_valid, f"Correct alignment should be valid, but got error: {error}"
