"""Qt tests for the drag&drop alignment editor widget."""

from pytestqt.qtbot import QtBot

from birkenbihl.gui.styles import theme
from birkenbihl.gui.widgets.interleaved_grid_editable import InterleavedGridEditable
from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import AlignmentStatus


def _editor(qtbot: QtBot, pairs: list[tuple[str, str]]) -> InterleavedGridEditable:
    editor = InterleavedGridEditable()
    qtbot.addWidget(editor)
    editor.build_grid(align_word_pairs("Yo te extrañaré", "Ich werde dich vermissen", pairs))
    return editor


def _column_words(editor: InterleavedGridEditable) -> list[list[str]]:
    return [[tag.get_word() for tag in column.get_tags()] for column in editor._columns]


CORRECT = [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde")]


class TestInterleavedGridEditable:
    def test_renders_one_column_per_source_word(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, CORRECT)

        assert _column_words(editor) == [["Ich"], ["dich"], ["vermissen", "werde"]]
        assert editor._pool.is_empty()
        assert editor._error_label.text() == ""

    def test_tags_carry_target_positions(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, CORRECT)

        assert [tag.get_target_index() for tag in editor._columns[2].get_tags()] == [3, 1]

    def test_drop_into_column_moves_word_and_emits_alignments(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, CORRECT)

        with qtbot.waitSignal(editor.alignments_changed, timeout=1000) as blocker:
            editor._columns[1].word_dropped.emit(1)  # "werde" onto te

        assert _column_words(editor) == [["Ich"], ["dich", "werde"], ["vermissen"]]
        alignments = blocker.args[0]
        assert alignments[1].target_indices == [2, 1]
        assert alignments[1].status == AlignmentStatus.CONFIRMED

    def test_drop_into_pool_reports_missing_word(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, CORRECT)

        with qtbot.waitSignal(editor.validation_error, timeout=1000) as blocker:
            editor._pool.word_dropped.emit(1)

        assert [tag.get_word() for tag in editor._pool.get_tags()] == ["werde"]
        assert "Fehlende Wörter: werde" in blocker.args[0]

    def test_empty_column_gets_error_style(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, CORRECT)

        editor._columns[0].word_dropped.emit(2)  # "dich" away from te

        assert editor._columns[1].styleSheet() == theme.get_error_frame_style()

    def test_flagged_column_is_highlighted_and_fixed_by_drop(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, [("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")])
        assert editor._columns[1].styleSheet() == theme.get_error_frame_style()  # flagged and empty: error wins
        assert [tag.get_word() for tag in editor._pool.get_tags()] == ["dich"]

        editor._columns[1].word_dropped.emit(2)

        assert editor._columns[1].styleSheet() == ""
        assert editor._error_label.text() == ""

    def test_flagged_column_with_word_is_orange(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-wird")])

        assert editor._columns[2].styleSheet() == theme.get_flagged_frame_style()
        assert editor._columns[2].toolTip() != ""

    def test_confirm_button_only_on_flagged_columns_with_a_word(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde-wird")])

        hidden = [column._confirm_button.isHidden() for column in editor._columns]

        assert hidden == [True, True, False]

    def test_flagged_and_empty_column_has_no_confirm_button(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, [("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")])

        assert editor._columns[1]._confirm_button.isHidden()

    def test_confirm_clears_flag_and_emits_alignments(self, qtbot: QtBot) -> None:
        editor = _editor(qtbot, [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde-wird")])

        with qtbot.waitSignal(editor.alignments_changed, timeout=1000) as blocker:
            editor._columns[2]._confirm_button.click()

        assert blocker.args[0][2].status == AlignmentStatus.CONFIRMED
        assert editor._columns[2].styleSheet() == ""
        assert editor._columns[2]._confirm_button.isHidden()
