"""Tests for GridState, the model behind the drag&drop alignment editor."""

import pytest

from birkenbihl.gui.models.grid_state import GridState, build_grid_state
from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import AlignmentStatus


def _grid(pairs: list[tuple[str, str]], source: str = "Yo te extrañaré", natural: str = "Ich werde dich vermissen"):
    return build_grid_state(align_word_pairs(source, natural, pairs))


def _words(grid: GridState) -> list[list[str]]:
    return [[grid.target_word(i) for i in column.target_indices] for column in grid.columns]


CORRECT = [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde")]


class TestBuildGridState:
    def test_one_column_per_source_word(self) -> None:
        grid = _grid(CORRECT)

        assert [c.source_word for c in grid.columns] == ["Yo", "te", "extrañaré"]
        assert _words(grid) == [["Ich"], ["dich"], ["vermissen", "werde"]]
        assert grid.unassigned == []

    def test_unmatched_ai_word_lands_in_pool_and_column_is_flagged(self) -> None:
        grid = _grid([("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")])

        assert grid.columns[1].is_flagged()
        assert grid.columns[1].is_empty()
        assert [grid.target_word(i) for i in grid.unassigned] == ["dich"]

    def test_repeated_source_words_keep_their_own_targets(self) -> None:
        grid = _grid(
            [("the", "der"), ("dog", "Hund"), ("and", "und"), ("the", "die"), ("man", "Frau")],
            source="the dog and the man",
            natural="der Hund und die Frau",
        )

        assert _words(grid)[0] == ["der"]
        assert _words(grid)[3] == ["die"]

    def test_repeated_target_words_are_distinct(self) -> None:
        grid = _grid(
            [("The", "der"), ("dog", "Hund"), ("and", "und"), ("the", "der"), ("man", "Mann")],
            source="The dog and the man",
            natural="der Hund und der Mann",
        )

        assert grid.columns[0].target_indices == [0]
        assert grid.columns[3].target_indices == [3]


class TestMove:
    def test_move_between_columns_confirms_both(self) -> None:
        grid = _grid(CORRECT)

        grid.move(1, to_column=1)  # "werde" from extrañaré to te

        assert _words(grid) == [["Ich"], ["dich", "werde"], ["vermissen"]]
        assert grid.columns[1].status == AlignmentStatus.CONFIRMED
        assert grid.columns[2].status == AlignmentStatus.CONFIRMED
        assert grid.columns[0].status == AlignmentStatus.SUGGESTED

    def test_move_to_pool_and_back(self) -> None:
        grid = _grid(CORRECT)

        grid.move(0, to_column=None)
        assert grid.unassigned == [0]
        assert grid.columns[0].is_empty()

        grid.move(0, to_column=0)
        assert grid.unassigned == []
        assert _words(grid)[0] == ["Ich"]

    def test_moving_one_of_two_equal_words_moves_only_that_one(self) -> None:
        grid = _grid(
            [("The", "der"), ("dog", "Hund"), ("and", "und"), ("the", "der"), ("man", "Mann")],
            source="The dog and the man",
            natural="der Hund und der Mann",
        )

        grid.move(3, to_column=None)

        assert grid.columns[0].target_indices == [0]
        assert grid.columns[3].target_indices == []
        assert grid.unassigned == [3]

    def test_fixing_a_flagged_column_confirms_it(self) -> None:
        grid = _grid([("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")])

        grid.move(grid.unassigned[0], to_column=1)

        assert grid.columns[1].status == AlignmentStatus.CONFIRMED
        assert grid.validate() == (True, None)


class TestValidate:
    def test_valid_alignment(self) -> None:
        assert _grid(CORRECT).validate() == (True, None)

    def test_empty_column_is_invalid(self) -> None:
        grid = _grid(CORRECT)
        grid.move(2, to_column=0)  # "dich" away from te

        is_valid, message = grid.validate()

        assert not is_valid
        assert message is not None
        assert "Quellwörter ohne Zielwort: te" in message

    def test_word_left_in_pool_is_invalid(self) -> None:
        grid = _grid(CORRECT)
        grid.move(1, to_column=None)  # "werde" into pool

        is_valid, message = grid.validate()

        assert not is_valid
        assert message is not None
        assert "Fehlende Wörter: werde" in message

    def test_to_word_alignments_carries_status(self) -> None:
        grid = _grid(CORRECT)
        grid.move(1, to_column=1)

        alignments = grid.to_word_alignments()

        assert [(a.source_indices, a.target_indices) for a in alignments] == [([0], [0]), ([1], [2, 1]), ([2], [3])]
        assert [a.status for a in alignments] == [
            AlignmentStatus.SUGGESTED,
            AlignmentStatus.CONFIRMED,
            AlignmentStatus.CONFIRMED,
        ]


class TestConfirm:
    def test_confirm_flagged_column_without_changing_it(self) -> None:
        grid = _grid([("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde-wird")])
        assert grid.columns[2].is_flagged()

        grid.confirm(2)

        assert grid.columns[2].status == AlignmentStatus.CONFIRMED
        assert _words(grid)[2] == ["vermissen", "werde"]
        assert grid.validate() == (True, None)

    def test_empty_column_cannot_be_confirmed(self) -> None:
        grid = _grid([("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")])

        grid.confirm(1)

        assert grid.columns[1].status == AlignmentStatus.FLAGGED


STATION = ("¿Dónde está la estación de tren?", "Wo ist der Bahnhof?")
STATION_AI = [("Dónde", "Wo"), ("está", "ist"), ("la", "der"), ("estación", "Bahnhof")]


class TestJoinAndSplit:
    def test_source_words_without_target_get_columns(self) -> None:
        grid = _grid(STATION_AI, *STATION)

        assert [c.source_word for c in grid.columns] == ["Dónde", "está", "la", "estación", "de", "tren"]
        assert grid.columns[4].is_empty()
        assert grid.columns[5].is_empty()

    def test_joining_empty_columns_into_their_left_neighbour_makes_the_sentence_valid(self) -> None:
        grid = _grid(STATION_AI, *STATION)

        grid.join(4, 3)  # "de" into "estación"
        grid.join(4, 3)  # "tren" into "estación-de"

        assert [c.source_word for c in grid.columns] == ["Dónde", "está", "la", "estación-de-tren"]
        assert _words(grid)[3] == ["Bahnhof"]
        assert grid.columns[3].status == AlignmentStatus.CONFIRMED
        assert grid.validate() == (True, None)
        assert grid.to_word_alignments()[3].source_indices == [3, 4, 5]

    def test_join_with_right_neighbour(self) -> None:
        grid = _grid(STATION_AI, *STATION)

        grid.join(4, 5)

        assert grid.columns[4].source_word == "de-tren"
        assert grid.columns[4].is_joined()

    def test_only_neighbours_can_be_joined(self) -> None:
        grid = _grid(STATION_AI, *STATION)

        with pytest.raises(ValueError, match="not neighbours"):
            grid.join(0, 2)

    def test_split_gives_every_word_its_own_column_and_keeps_targets_on_the_first(self) -> None:
        grid = _grid(STATION_AI, *STATION)
        grid.join(4, 3)

        grid.split(3)

        assert [c.source_word for c in grid.columns] == ["Dónde", "está", "la", "estación", "de", "tren"]
        assert _words(grid)[3:] == [["Bahnhof"], [], []]

    def test_loading_a_saved_group_keeps_it(self) -> None:
        grid = _grid(STATION_AI[:3] + [("estación de tren", "Bahnhof")], *STATION)

        assert grid.columns[-1].source_word == "estación-de-tren"
        assert grid.columns[-1].source_indices == [3, 4, 5]
