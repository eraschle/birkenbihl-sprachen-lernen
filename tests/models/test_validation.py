"""Tests for Birkenbihl alignment validation on token positions."""

from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import Sentence, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete


def _sentence(source: str, natural: str, alignments: list[tuple[int, list[int]]]) -> Sentence:
    return Sentence(
        source_text=source,
        natural_translation=natural,
        word_alignments=[WordAlignment(source_index=s, target_indices=t) for s, t in alignments],
    )


class TestValidateAlignmentComplete:
    def test_valid_birkenbihl_example(self) -> None:
        sentence = align_word_pairs(
            "Yo te extrañaré",
            "Ich werde dich vermissen",
            [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde")],
        )

        assert validate_alignment_complete(sentence) == (True, None)

    def test_missing_target_word(self) -> None:
        sentence = _sentence("Yo te extrañaré", "Ich werde dich vermissen", [(0, [0]), (1, [2]), (2, [3])])

        is_valid, error = validate_alignment_complete(sentence)

        assert not is_valid
        assert error is not None
        assert "Fehlende Wörter: werde" in error

    def test_repeated_word_must_be_used_each_time(self) -> None:
        """Set comparison would accept this: one 'der' is enough. Positions require both."""
        sentence = _sentence(
            "The dog and the man", "der Hund und der Mann", [(0, [0]), (1, [1]), (2, [2]), (3, [0]), (4, [4])]
        )

        is_valid, error = validate_alignment_complete(sentence)

        assert not is_valid
        assert error is not None
        assert "Mehrfach verwendete Wörter: der" in error
        assert "Fehlende Wörter: der" in error

    def test_source_word_without_target(self) -> None:
        sentence = _sentence("Yo te extrañaré", "Ich dich vermissen", [(0, [0]), (1, []), (2, [1, 2])])

        is_valid, error = validate_alignment_complete(sentence)

        assert not is_valid
        assert error is not None
        assert "Quellwörter ohne Zielwort: te" in error

    def test_source_word_missing_from_alignments(self) -> None:
        sentence = _sentence("Yo te extrañaré", "Ich dich vermissen", [(0, [0]), (2, [1, 2])])

        is_valid, error = validate_alignment_complete(sentence)

        assert not is_valid
        assert error is not None
        assert "Quellwörter ohne Zielwort: te" in error

    def test_source_word_aligned_twice(self) -> None:
        sentence = _sentence("Yo te", "Ich dich", [(0, [0]), (1, [1]), (1, [])])

        is_valid, error = validate_alignment_complete(sentence)

        assert not is_valid
        assert error is not None
        assert "Quellwörter mehrfach zugeordnet: te" in error

    def test_out_of_range_positions(self) -> None:
        sentence = _sentence("Yo", "Ich", [(0, [0, 5]), (3, [0])])

        is_valid, error = validate_alignment_complete(sentence)

        assert not is_valid
        assert error is not None
        assert "Ungültige Quellwort-Positionen: 3" in error
        assert "Ungültige Zielwort-Positionen: 5" in error

    def test_punctuation_is_not_a_word(self) -> None:
        sentence = align_word_pairs(
            "Hola, ¿cómo estás?",
            "Hallo, wie geht's dir?",
            [("Hola", "Hallo"), ("cómo", "wie"), ("estás", "geht's-dir")],
        )

        assert sentence.target_tokens == ["Hallo", "wie", "geht's", "dir"]
        assert validate_alignment_complete(sentence) == (True, None)

    def test_empty_sentence_is_valid(self) -> None:
        sentence = _sentence("", "", [])

        assert validate_alignment_complete(sentence) == (True, None)

    def test_reports_all_problems_at_once(self) -> None:
        sentence = _sentence("Yo te extrañaré", "Ich werde dich vermissen", [(0, [0]), (2, [3, 3])])

        _, error = validate_alignment_complete(sentence)

        assert error is not None
        assert "Quellwörter ohne Zielwort: te" in error
        assert "Mehrfach verwendete Wörter: vermissen" in error
        assert "Fehlende Wörter: werde, dich" in error
