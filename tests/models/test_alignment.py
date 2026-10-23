"""Tests for matching AI word pairs to token positions."""

import pytest

from birkenbihl.models.alignment import align_by_probability, align_word_pairs
from birkenbihl.models.translation import AlignmentStatus
from birkenbihl.models.validation import validate_alignment_complete


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

        assert [a.source_indices for a in sentence.word_alignments] == [[0], [1], [2]]
        assert sentence.needs_review()


class TestAlignByProbability:
    YO_TE = ("Yo te extrañaré", "Ich werde dich vermissen")

    def test_every_target_word_goes_to_its_likeliest_source_word(self) -> None:
        probabilities = [
            [0.96, 0.05, 0.11, 0.02],
            [0.03, 0.04, 0.95, 0.01],
            [0.02, 0.80, 0.05, 0.90],
        ]

        sentence = align_by_probability(*self.YO_TE, probabilities)

        assert _columns(sentence) == [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "werde-vermissen")]
        assert set(_statuses(sentence)) == {AlignmentStatus.SUGGESTED}

    def test_unlikely_word_flags_its_column(self) -> None:
        probabilities = [
            [0.96, 0.05, 0.11, 0.02],
            [0.03, 0.04, 0.95, 0.01],
            [0.02, 0.17, 0.05, 0.90],
        ]

        sentence = align_by_probability(*self.YO_TE, probabilities)

        assert _columns(sentence)[2] == ("extrañaré", "werde-vermissen")
        assert _statuses(sentence) == [AlignmentStatus.SUGGESTED, AlignmentStatus.SUGGESTED, AlignmentStatus.FLAGGED]

    def test_close_runner_up_flags_the_column(self) -> None:
        sentence = align_by_probability("Me gusta", "Mir gefällt", [[0.84, 0.10], [0.75, 0.94]])

        assert _columns(sentence) == [("Me", "Mir"), ("gusta", "gefällt")]
        assert _statuses(sentence) == [AlignmentStatus.FLAGGED, AlignmentStatus.SUGGESTED]

    def test_repeated_words_are_distinguished_by_position(self) -> None:
        probabilities = [
            [0.95, 0.05, 0.02, 0.10, 0.02],
            [0.05, 0.90, 0.02, 0.02, 0.01],
            [0.01, 0.02, 0.97, 0.02, 0.01],
            [0.08, 0.01, 0.02, 0.92, 0.03],
            [0.01, 0.02, 0.01, 0.04, 0.96],
        ]

        sentence = align_by_probability("the dog sees the man", "der Hund sieht der Mann", probabilities)

        assert [a.target_indices for a in sentence.sorted_alignments()] == [[0], [1], [2], [3], [4]]

    def test_source_word_without_target_joins_the_next_column_flagged(self) -> None:
        sentence = align_by_probability("to buy", "kaufen", [[0.20], [0.95]])

        assert _columns(sentence) == [("to-buy", "kaufen")]
        assert _statuses(sentence) == [AlignmentStatus.FLAGGED]
        assert validate_alignment_complete(sentence) == (True, None)

    def test_source_words_without_target_join_the_previous_column_flagged(self) -> None:
        probabilities = [
            [0.9, 0.0, 0.0, 0.0],  # Dónde → Wo
            [0.0, 0.9, 0.0, 0.0],  # está → ist
            [0.0, 0.0, 0.9, 0.0],  # la → der
            [0.0, 0.0, 0.0, 0.8],  # estación → Bahnhof
            [0.0, 0.0, 0.0, 0.1],  # de
            [0.0, 0.0, 0.0, 0.3],  # tren
        ]

        sentence = align_by_probability("¿Dónde está la estación de tren?", "Wo ist der Bahnhof?", probabilities)

        assert _columns(sentence)[-1] == ("estación-de-tren", "Bahnhof")
        assert _statuses(sentence) == [AlignmentStatus.SUGGESTED] * 3 + [AlignmentStatus.FLAGGED]
        assert validate_alignment_complete(sentence) == (True, None)

    def test_without_any_target_word_every_source_word_stays_alone(self) -> None:
        sentence = align_by_probability("Hola mundo", "", [[], []])

        assert [a.source_indices for a in sentence.word_alignments] == [[0], [1]]

    def test_every_target_word_is_used_exactly_once(self) -> None:
        sentence = align_by_probability("a b", "x y z", [[0.6, 0.6, 0.6], [0.6, 0.6, 0.6]])

        assert sorted(i for a in sentence.word_alignments for i in a.target_indices) == [0, 1, 2]

    def test_rejects_matrix_that_does_not_fit_the_sentence(self) -> None:
        with pytest.raises(ValueError, match="2x4"):
            align_by_probability("Hola mundo", "Hallo du schöne Welt", [[0.9, 0.1]])


class TestSourceWordGroups:
    """Several source words may share target words: 'estación de tren' → 'Bahnhof'."""

    def test_space_separated_source_words_form_one_column(self) -> None:
        sentence = align_word_pairs(
            "¿Dónde está la estación de tren?",
            "Wo ist der Bahnhof?",
            [("Dónde", "Wo"), ("está", "ist"), ("la", "der"), ("estación de tren", "Bahnhof")],
        )

        assert _columns(sentence) == [("Dónde", "Wo"), ("está", "ist"), ("la", "der"), ("estación-de-tren", "Bahnhof")]
        assert sentence.get_word_by_word() == "Wo ist der Bahnhof"
        assert not sentence.needs_review()

    def test_hyphen_joined_source_words_form_one_column(self) -> None:
        sentence = align_word_pairs(
            "I've been waiting for you.",
            "Ich habe auf dich gewartet.",
            [("I've", "Ich-habe"), ("been-waiting", "gewartet"), ("for", "auf"), ("you", "dich")],
        )

        assert _columns(sentence)[1] == ("been-waiting", "gewartet")
        assert sentence.word_alignments[1].source_indices == [1, 2]

    def test_source_word_with_own_hyphen_stays_one_word(self) -> None:
        sentence = align_word_pairs("un e-mail", "eine E-Mail", [("un", "eine"), ("e-mail", "E-Mail")])

        assert sentence.word_alignments[1].source_indices == [1]

    def test_words_that_are_not_neighbours_in_the_sentence_are_not_matched(self) -> None:
        sentence = align_word_pairs("Hola amigo mío", "Hallo mein Freund", [("Hola mío", "Hallo"), ("amigo", "Freund")])

        assert sentence.needs_review()
        assert [sentence.target_tokens[i] for i in sentence.unassigned_target_indices()] == ["Hallo", "mein"]

    def test_unnamed_source_word_gets_its_own_flagged_column(self) -> None:
        sentence = align_word_pairs(
            "¿Dónde está la estación de tren?",
            "Wo ist der Bahnhof?",
            [("Dónde", "Wo"), ("está", "ist"), ("la", "der"), ("estación", "Bahnhof")],
        )

        assert _columns(sentence)[-2:] == [("de", ""), ("tren", "")]
        assert _statuses(sentence)[-2:] == [AlignmentStatus.FLAGGED, AlignmentStatus.FLAGGED]
