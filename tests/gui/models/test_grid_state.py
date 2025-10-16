"""Tests for grid state model."""

import pytest

from birkenbihl.gui.models.grid_state import ColumnState, GridState, build_grid_state
from birkenbihl.models.translation import Sentence, WordAlignment


class TestColumnState:
    """Tests for ColumnState."""

    def test_is_empty_with_no_words(self):
        """Test is_empty returns True when no words assigned."""
        column = ColumnState(source_word="test")
        assert column.is_empty() is True

    def test_is_empty_with_words(self):
        """Test is_empty returns False when words assigned."""
        column = ColumnState(source_word="test", assigned_words=["Wort"])
        assert column.is_empty() is False


class TestGridState:
    """Tests for GridState."""

    def test_is_valid_all_columns_filled(self):
        """Test is_valid returns True when all columns have words."""
        columns = [
            ColumnState("hello", ["Hallo"]),
            ColumnState("world", ["Welt"]),
        ]
        state = GridState(columns=columns)
        assert state.is_valid() is True

    def test_is_valid_some_columns_empty(self):
        """Test is_valid returns False when some columns empty."""
        columns = [
            ColumnState("hello", ["Hallo"]),
            ColumnState("world", []),
        ]
        state = GridState(columns=columns)
        assert state.is_valid() is False

    def test_get_error_columns(self):
        """Test get_error_columns returns empty column source words."""
        columns = [
            ColumnState("hello", ["Hallo"]),
            ColumnState("world", []),
            ColumnState("test", []),
        ]
        state = GridState(columns=columns)
        errors = state.get_error_columns()
        assert errors == ["world", "test"]

    def test_to_word_alignments(self):
        """Test conversion to word alignments."""
        columns = [
            ColumnState("hello", ["Hallo"]),
            ColumnState("world", ["Welt", "da"]),
        ]
        state = GridState(columns=columns)
        alignments = state.to_word_alignments()

        assert len(alignments) == 3
        assert alignments[0].source_word == "hello"
        assert alignments[0].target_word == "Hallo"
        assert alignments[0].position == 0

        assert alignments[1].source_word == "world"
        assert alignments[1].target_word == "Welt"
        assert alignments[1].position == 1

        assert alignments[2].source_word == "world"
        assert alignments[2].target_word == "da"
        assert alignments[2].position == 1


class TestBuildGridState:
    """Tests for build_grid_state function."""

    def test_build_simple_grid(self):
        """Test building grid from simple sentence."""
        sentence = Sentence(
            source_text="Hello world",
            natural_translation="Hallo Welt",
            word_alignments=[
                WordAlignment(source_word="Hello", target_word="Hallo", position=0),
                WordAlignment(source_word="world", target_word="Welt", position=1),
            ],
        )

        state = build_grid_state(sentence)

        assert len(state.columns) == 2
        assert state.columns[0].source_word == "Hello"
        assert state.columns[0].assigned_words == ["Hallo"]
        assert state.columns[1].source_word == "world"
        assert state.columns[1].assigned_words == ["Welt"]
        assert state.unassigned_words == []

    def test_build_with_hyphenated_words(self):
        """Test building grid with hyphenated target words."""
        sentence = Sentence(
            source_text="I miss",
            natural_translation="Ich vermisse",
            word_alignments=[
                WordAlignment(source_word="I", target_word="Ich", position=0),
                WordAlignment(source_word="miss", target_word="vermisse", position=1),
            ],
        )

        state = build_grid_state(sentence)

        assert len(state.columns) == 2
        assert state.columns[0].assigned_words == ["Ich"]
        assert state.columns[1].assigned_words == ["vermisse"]

    def test_build_with_unassigned_words(self):
        """Test building grid with unassigned words in natural translation."""
        sentence = Sentence(
            source_text="Hello world",
            natural_translation="Hallo schöne Welt",
            word_alignments=[
                WordAlignment(source_word="Hello", target_word="Hallo", position=0),
                WordAlignment(source_word="world", target_word="Welt", position=1),
            ],
        )

        state = build_grid_state(sentence)

        assert len(state.unassigned_words) == 1
        assert "schöne" in state.unassigned_words
