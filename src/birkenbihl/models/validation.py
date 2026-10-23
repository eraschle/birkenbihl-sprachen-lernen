"""Validation of word-by-word alignments against the Birkenbihl rules.

Rules (checked on token positions, so repeated words count individually):
1. Every source word belongs to exactly one column, and every column has at least one target word.
   Several source words may share a column ("estación de tren" → "Bahnhof").
2. Every word of the natural translation is used exactly once.
"""

from collections import Counter

from birkenbihl.models.translation import Sentence


def validate_alignment_complete(sentence: Sentence) -> tuple[bool, str | None]:
    """Check a sentence's alignments.

    Returns:
        (True, None) if valid, otherwise (False, German error message listing every problem)

    Example:
        "Yo te extrañaré" / "Ich werde dich vermissen" with te→dich, extrañaré→vermissen-werde, Yo→Ich
        is valid; leaving out "werde" reports "Fehlende Wörter: werde".
    """
    errors = _source_errors(sentence) + _target_errors(sentence)
    if errors:
        return False, " ".join(errors)
    return True, None


JOIN_HINT = "Teilen sich mehrere Wörter ein Wort der Übersetzung, verbinde sie (z. B. estación de tren → Bahnhof)."


def _source_errors(sentence: Sentence) -> list[str]:
    tokens = sentence.source_tokens
    counts = Counter(index for alignment in sentence.word_alignments for index in alignment.source_indices)
    errors = []

    invalid = sorted(index for index in counts if not 0 <= index < len(tokens))
    if invalid:
        errors.append(f"Ungültige Quellwort-Positionen: {_join(invalid)}.")

    if any(not alignment.source_indices for alignment in sentence.word_alignments):
        errors.append("Spalten ohne Quellwort.")

    duplicated = [tokens[i] for i in sorted(counts) if 0 <= i < len(tokens) and counts[i] > 1]
    if duplicated:
        errors.append(f"Quellwörter mehrfach zugeordnet: {_join(duplicated)}.")

    mapped = {i for a in sentence.word_alignments if a.target_indices for i in a.source_indices}
    unmapped = [token for index, token in enumerate(tokens) if index not in mapped]
    if unmapped:
        errors.append(f"Quellwörter ohne Zielwort: {_join(unmapped)}. {JOIN_HINT}")
    return errors


def _target_errors(sentence: Sentence) -> list[str]:
    tokens = sentence.target_tokens
    counts = Counter(index for alignment in sentence.word_alignments for index in alignment.target_indices)
    errors = []

    invalid = sorted(index for index in counts if not 0 <= index < len(tokens))
    if invalid:
        errors.append(f"Ungültige Zielwort-Positionen: {_join(invalid)}.")

    duplicated = [tokens[i] for i in sorted(counts) if 0 <= i < len(tokens) and counts[i] > 1]
    if duplicated:
        errors.append(f"Mehrfach verwendete Wörter: {_join(duplicated)}.")

    missing = [token for index, token in enumerate(tokens) if index not in counts]
    if missing:
        rule = "Die Wort-für-Wort-Übersetzung muss jedes Wort der natürlichen Übersetzung genau einmal verwenden."
        errors.append(f"Fehlende Wörter: {_join(missing)}. {rule}")
    return errors


def _join(items: list[str] | list[int]) -> str:
    return ", ".join(str(item) for item in items)
