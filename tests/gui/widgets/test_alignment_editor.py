"""Tests for AlignmentEditor widget."""

from uuid import uuid4

from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from birkenbihl.gui.widgets.alignment_editor import AlignmentEditor
from birkenbihl.models.translation import Sentence, WordAlignment
from tests import conftest


class TestAlignmentEditor:
    """Tests for AlignmentEditor."""

    def test_init_without_sentence(self, qapp: QApplication):
        """Test initialization without sentence."""
        conftest.skrip_test_when_is_not_valid(qapp)
        editor = AlignmentEditor()
        assert editor is not None
        assert editor._sentence is None
        assert editor._controller is None

    def test_init_with_sentence(self, qapp: QApplication):
        """Test initialization with sentence."""
        conftest.skrip_test_when_is_not_valid(qapp)
        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo te extrañaré",
            natural_translation="Ich werde dich vermissen",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
                WordAlignment(source_word="te", target_word="dich", position=1),
                WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
            ],
        )

        editor = AlignmentEditor(sentence=sentence)
        assert editor._sentence is sentence
        assert editor._controller is not None

    def test_build_mappings_from_alignments_with_hyphens(self, qapp: QApplication):
        """Test that hyphenated alignments are split correctly."""
        conftest.skrip_test_when_is_not_valid(qapp)
        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo te extrañaré",
            natural_translation="Ich werde dich vermissen",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
                WordAlignment(source_word="te", target_word="dich", position=1),
                WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
            ],
        )

        editor = AlignmentEditor(sentence=sentence)
        mappings = editor._build_mappings_from_alignments()

        assert mappings["Yo"] == ["Ich"]
        assert mappings["te"] == ["dich"]
        assert mappings["extrañaré"] == ["werde", "vermissen"]  # Split!

    def test_build_mappings_bug_fix_multiple_alignments_same_source(self, qapp: QApplication):
        """Test BUG FIX: Multiple alignments for same source word don't overwrite.

        This is the critical bug fix - when multiple WordAlignments exist
        for the same source_word, they should be combined, not overwritten.
        """
        conftest.skrip_test_when_is_not_valid(qapp)
        sentence = Sentence(
            uuid=uuid4(),
            source_text="extrañaré",
            natural_translation="werde vermissen",
            word_alignments=[
                # Two separate alignments for same source word
                WordAlignment(source_word="extrañaré", target_word="werde", position=0),
                WordAlignment(source_word="extrañaré", target_word="vermissen", position=1),
            ],
        )

        editor = AlignmentEditor(sentence=sentence)
        mappings = editor._build_mappings_from_alignments()

        # Bug fix: Both words should be present
        assert "werde" in mappings["extrañaré"]
        assert "vermissen" in mappings["extrañaré"]
        assert len(mappings["extrañaré"]) == 2

    def test_controller_created_with_correct_data(self, qapp: QApplication):
        """Test that controller is created with correct target words and mappings."""
        conftest.skrip_test_when_is_not_valid(qapp)
        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo te",
            natural_translation="Ich dich",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
                WordAlignment(source_word="te", target_word="dich", position=1),
            ],
        )

        editor = AlignmentEditor(sentence=sentence)

        # Check controller has correct target words
        assert editor._controller is not None
        assert editor._controller._target_words == ["Ich", "dich"]

        # Check controller has correct initial mappings
        assert editor._controller.get_assigned_words("Yo") == ["Ich"]
        assert editor._controller.get_assigned_words("te") == ["dich"]

    def test_build_alignments_uses_hook_system(self, qapp: QApplication):
        """Test that _build_alignments joins multiple words with hyphens."""
        conftest.skrip_test_when_is_not_valid(qapp)
        sentence = Sentence(
            uuid=uuid4(),
            source_text="extrañaré",
            natural_translation="werde vermissen",
            word_alignments=[],
        )

        editor = AlignmentEditor(sentence=sentence)

        # Manually add words to controller
        assert editor._controller is not None
        editor._controller.add_word("extrañaré", "werde")
        editor._controller.add_word("extrañaré", "vermissen")

        # Build alignments
        alignments = editor._build_alignments()

        # Should join with hyphen
        assert len(alignments) == 1
        assert alignments[0].source_word == "extrañaré"
        assert alignments[0].target_word == "werde-vermissen"

    def test_update_data(self, qapp: QApplication):
        """Test update_data reloads sentence."""
        conftest.skrip_test_when_is_not_valid(qapp)
        editor = AlignmentEditor()

        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo",
            natural_translation="Ich",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
            ],
        )

        editor.update_data(sentence)

        assert editor._sentence is sentence
        assert editor._controller is not None
        assert editor._controller.get_assigned_words("Yo") == ["Ich"]

    def test_validate_button_with_valid_alignments(self, qtbot: QtBot):
        """Test validate button with valid alignments emits success signal."""
        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo",
            natural_translation="Ich",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
            ],
        )

        editor = AlignmentEditor(sentence=sentence)

        assert editor is not None
        # Click validate - should emit validation_succeeded signal
        with qtbot.waitSignal(editor.validation_succeeded, timeout=1000):
            editor._on_validate()

    def test_validate_button_with_invalid_alignments(self, qtbot: QtBot):
        """Test validate button with invalid alignments emits signal."""
        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo te",
            natural_translation="Ich werde dich vermissen",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
                # Missing: te -> dich, werde, vermissen
            ],
        )

        editor = AlignmentEditor(sentence=sentence)

        # Click validate - should emit validation_failed
        with qtbot.waitSignal(editor.validation_failed, timeout=1000):
            editor._on_validate()

    def test_apply_button_emits_alignments(self, qtbot: QtBot):
        """Test apply button emits alignment_changed signal."""
        sentence = Sentence(
            uuid=uuid4(),
            source_text="Yo",
            natural_translation="Ich",
            word_alignments=[
                WordAlignment(source_word="Yo", target_word="Ich", position=0),
            ],
        )

        editor = AlignmentEditor(sentence=sentence)

        # Click apply - should emit alignment_changed
        with qtbot.waitSignal(editor.alignment_changed, timeout=1000):
            editor._on_apply()
