"""Validation functions for translation models."""

import re

from birkenbihl.models.translation import WordAlignment


def validate_alignment_complete(
    natural_translation: str,
    alignments: list[WordAlignment],
) -> tuple[bool, str | None]:
    """Validate that all words from natural translation are present in alignments.

    Rules:
    1. Split natural_translation into words (whitespace-separated)
    2. Extract all target_words from alignments
    3. Handle hyphenated combinations: "werde-vermissen" counts as ["werde", "vermissen"]
    4. Check that every word from natural_translation appears in target_words
    5. Check that no words are missing or extra

    Args:
        natural_translation: The natural translation text
        alignments: List of WordAlignment objects

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if validation passes
        - (False, "Fehlende Wörter: X, Y") if words are missing
        - (False, "Zusätzliche Wörter: X, Y") if extra words present

    Example:
        natural = "Ich werde dich vermissen"
        alignments = [
            WordAlignment(..., target_word="Ich", ...),
            WordAlignment(..., target_word="dich", ...),
            WordAlignment(..., target_word="werde-vermissen", ...)
        ]
        Returns: (True, None)
    """
    if not natural_translation.strip():
        if not alignments:
            return (True, None)
        return (False, "Natürliche Übersetzung ist leer, aber Alignments vorhanden")

    if not alignments:
        return (False, "Keine Alignments vorhanden")

    expected_words = _extract_words(natural_translation)
    actual_words = _extract_alignment_words(alignments)

    expected_set = set(expected_words)
    actual_set = set(actual_words)

    missing_words = expected_set - actual_set
    extra_words = actual_set - expected_set

    if missing_words and extra_words:
        error_msg = f"Fehlende Wörter: {', '.join(sorted(missing_words))}; "
        error_msg += f"Zusätzliche Wörter: {', '.join(sorted(extra_words))}. "
        error_msg += "Die Wort-für-Wort Übersetzung muss ALLE Wörter aus der natürlichen Übersetzung verwenden (keine zusammengesetzten Wörter, wenn diese in der natürlichen Übersetzung separat sind)."
        return (False, error_msg)
    elif missing_words:
        error_msg = f"Fehlende Wörter: {', '.join(sorted(missing_words))}. "
        error_msg += "Diese Wörter aus der natürlichen Übersetzung fehlen in den Wort-Alignments."
        return False, error_msg
    elif extra_words:
        error_msg = f"Zusätzliche Wörter: {', '.join(sorted(extra_words))}. "
        error_msg += "Diese Wörter sind in den Alignments, aber nicht in der natürlichen Übersetzung."
        return False, error_msg

    return (True, None)


def _extract_words(text: str) -> list[str]:
    """Extract normalized words from text.

    - Removes punctuation (except apostrophes and hyphens)
    - Converts to lowercase
    - Splits on whitespace

    Args:
        text: Input text

    Returns:
        List of normalized words
    """
    text_no_punct = re.sub(r"[^\w\s'\-]", "", text)
    words = text_no_punct.lower().split()
    return [w for w in words if w]


def validate_source_words_mapped(alignments: list[WordAlignment]) -> tuple[bool, str | None]:
    """Validate that all source words have non-empty target words.

    Checks for:
    1. Empty or whitespace-only target words
    2. Source words without proper mapping

    Args:
        alignments: List of WordAlignment objects

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if all source words have valid targets
        - (False, "error message") if validation fails

    Example:
        # Invalid: source word with empty target
        alignments = [
            WordAlignment(source_word="no", target_word="", position=0),
            WordAlignment(source_word="importante", target_word="unwichtig", position=1),
        ]
        Returns: (False, "Quellwort 'no' hat kein Zielwort")
    """
    unmapped_sources = []

    for alignment in alignments:
        # Check if target is empty or only whitespace
        target_stripped = alignment.target_word.strip()
        if not target_stripped:
            unmapped_sources.append(alignment.source_word)

    if unmapped_sources:
        words_str = ", ".join(f"'{w}'" for w in unmapped_sources)
        return (False, f"Quellwörter ohne Zielwort: {words_str}")

    return (True, None)


def _extract_alignment_words(alignments: list[WordAlignment]) -> list[str]:
    """Extract all words from alignments, splitting hyphenated combinations.

    Removes punctuation (except hyphens used for word combination) to match
    the normalization done in _extract_words().

    Args:
        alignments: List of WordAlignment objects

    Returns:
        List of normalized words (hyphenated words are split, punctuation removed)
    """
    words = []
    for alignment in alignments:
        # Normalize: lowercase and remove punctuation (except hyphens between words)
        target_word = alignment.target_word.lower()

        if "-" in target_word:
            # Split hyphenated words first
            parts = target_word.split("-")
            # Remove punctuation from each part
            for part in parts:
                clean_part = re.sub(r"[^\w'\-]", "", part)
                if clean_part:
                    words.append(clean_part)
        else:
            # Remove punctuation from single word
            clean_word = re.sub(r"[^\w'\-]", "", target_word)
            if clean_word:
                words.append(clean_word)

    return words
