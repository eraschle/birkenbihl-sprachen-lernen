"""Qt tests for the edit mode: correct an AI alignment in the grid and save it."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pytestqt.qtbot import QtBot

from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.views.edit_mode_panel import EditModePanel
from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import AlignmentStatus, Translation
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


@pytest.fixture
def storage_path(tmp_path: Path) -> Path:
    return tmp_path / "translations.json"


@pytest.fixture
def panel_with_ai_error(qtbot: QtBot, tmp_path: Path, storage_path: Path) -> tuple[EditModePanel, Translation]:
    """Edit panel showing 'Yo te extrañaré' where the AI answered 'dir' instead of 'dich'."""
    service = TranslationService(None, JsonStorageProvider(storage_path))
    settings = SettingsService(tmp_path / "settings.yaml")
    settings.load_settings()
    sentence = align_word_pairs(
        "Yo te extrañaré", "Ich werde dich vermissen", [("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")]
    )
    translation = service.save_translation(
        Translation(
            title="AI error",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[sentence],
        )
    )
    state = AppState()
    panel = EditModePanel(service, settings, state)
    qtbot.addWidget(panel)
    state.select_translation(translation)
    return panel, translation


class TestEditModePanel:
    def test_ai_error_blocks_save(self, panel_with_ai_error: tuple[EditModePanel, Translation]) -> None:
        panel, _ = panel_with_ai_error
        grid = panel._interleaved_grid

        assert [tag.get_word() for tag in grid._pool.get_tags()] == ["dich"]
        assert not panel._save_button.isEnabled()

    def test_fixing_the_error_enables_save_and_persists_confirmed_alignment(
        self, panel_with_ai_error: tuple[EditModePanel, Translation], storage_path: Path
    ) -> None:
        panel, translation = panel_with_ai_error

        panel._interleaved_grid._columns[1].word_dropped.emit(2)  # drag "dich" onto "te"

        assert panel._save_button.isEnabled()
        with patch("birkenbihl.gui.views.edit_mode_panel.QMessageBox"):
            panel._save_button.click()

        reloaded = JsonStorageProvider(storage_path).get(translation.uuid)
        assert reloaded is not None
        sentence = reloaded.sentences[0]
        assert sentence.get_word_by_word() == "Ich dich vermissen-werde"
        assert sentence.word_alignments[1].status == AlignmentStatus.CONFIRMED
        assert not sentence.needs_review()

    def test_breaking_a_valid_alignment_disables_save(
        self, panel_with_ai_error: tuple[EditModePanel, Translation]
    ) -> None:
        panel, _ = panel_with_ai_error
        grid = panel._interleaved_grid
        grid._columns[1].word_dropped.emit(2)

        grid._pool.word_dropped.emit(0)  # "Ich" into the pool

        assert not panel._save_button.isEnabled()
