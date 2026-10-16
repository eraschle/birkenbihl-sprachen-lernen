"""Tests for matching AI word pairs to token positions."""

from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import AlignmentStatus


def _columns(sentence) -> list[tuple[str, str]]:
    return [(sentence.source_word(a), sentence.target_text(a)) for a in sentence.sorted_alignments()]


def _statuses(sentence) -> list[AlignmentStatus]:
    return [a.status for a in sentence.sorted_alignments()]


class TestAlignWordPairs:
    def test_hyphenated_target_becomes_multiple_positions(self) -> None:
        sentence = align_word_pairs(
            "Yo te extrañaré",
            "Ich werde dich vermissen",
            [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde")],
        )

        assert sentence.word_alignments[2].target_indices == [3, 1]
        assert sentence.get_word_by_word() == "Ich dich vermissen-werde"
        assert set(_statuses(sentence)) == {AlignmentStatus.SUGGESTED}

    def test_repeated_words_are_matched_in_order(self) -> None:
        sentence = align_word_pairs(
            "the dog and the man",
            "der Hund und die Frau",
            [("the", "der"), ("dog", "Hund"), ("and", "und"), ("the", "die"), ("man", "Frau")],
        )

        assert _columns(sentence) == [("the", "der"), ("dog", "Hund"), ("and", "und"), ("the", "die"), ("man", "Frau")]

    def test_repeated_target_words_use_distinct_positions(self) -> None:
        sentence = align_word_pairs(
            "The dog and the man",
            "der Hund und der Mann",
            [("The", "der"), ("dog", "Hund"), ("and", "und"), ("the", "der"), ("man", "Mann")],
        )

        assert sentence.word_alignments[0].target_indices == [0]
        assert sentence.word_alignments[3].target_indices == [3]

    def test_same_source_word_twice_in_a_row_collects_targets(self) -> None:
        sentence = align_word_pairs(
            "Yo te extrañaré",
            "Ich werde dich vermissen",
            [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen"), ("extrañaré", "werde")],
        )

        assert _columns(sentence)[2] == ("extrañaré", "vermissen-werde")

    def test_matching_ignores_case_and_punctuation(self) -> None:
        sentence = align_word_pairs("Hola, amigo.", "Hallo, Freund.", [("hola,", "hallo"), ("Amigo", "Freund.")])

        assert _columns(sentence) == [("Hola", "Hallo"), ("amigo", "Freund")]

    def test_target_word_with_own_hyphen_stays_one_token(self) -> None:
        sentence = align_word_pairs("un e-mail", "eine E-Mail", [("un", "eine"), ("e-mail", "E-Mail")])

        assert sentence.word_alignments[1].target_indices == [1]

    def test_unknown_target_word_is_flagged_not_guessed(self) -> None:
        sentence = align_word_pairs(
            "The dog and the man",
            "der Hund und der Mann",
            [("The", "der"), ("dog", "Hund"), ("and", "und"), ("the", "die"), ("man", "Mann")],
        )

        assert sentence.word_alignments[3].target_indices == []
        assert sentence.word_alignments[3].status == AlignmentStatus.FLAGGED
        assert sentence.unassigned_target_indices() == [3]
        assert sentence.needs_review()

    def test_partly_unknown_hyphenated_target_is_flagged(self) -> None:
        sentence = align_word_pairs(
            "Yo te extrañaré",
            "Ich werde dich vermissen",
            [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-wird")],
        )

        assert _columns(sentence)[2] == ("extrañaré", "vermissen")
        assert sentence.word_alignments[2].status == AlignmentStatus.FLAGGED

    def test_source_word_not_in_pairs_is_flagged(self) -> None:
        sentence = align_word_pairs(
            "Yo te extrañaré", "Ich dich vermissen", [("Yo", "Ich"), ("extrañaré", "dich-vermissen")]
        )

        assert sentence.word_alignments[1].target_indices == []
        assert sentence.word_alignments[1].status == AlignmentStatus.FLAGGED

    def test_unknown_source_word_is_ignored_and_its_targets_stay_unassigned(self) -> None:
        sentence = align_word_pairs("Yo te", "Ich dich", [("Yo", "Ich"), ("nosotros", "dich")])

        assert sentence.unassigned_target_indices() == [1]
        assert sentence.word_alignments[1].status == AlignmentStatus.FLAGGED

    def test_one_alignment_per_source_token(self) -> None:
        sentence = align_word_pairs("Yo te extrañaré", "Ich werde dich vermissen", [])

        assert [a.source_index for a in sentence.word_alignments] == [0, 1, 2]
        assert sentence.needs_review()
