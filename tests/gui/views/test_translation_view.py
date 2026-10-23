"""Qt tests for the translation tab: list of translations and switching between view, create and edit."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot

from birkenbihl.gui.models.app_services import AppServices
from birkenbihl.gui.models.app_state import AppMode
from birkenbihl.gui.views.main_window import MainWindow
from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.translation import Translation
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path) -> MainWindow:
    settings = SettingsService(tmp_path / "settings.yaml")
    settings.load_settings()
    translations = TranslationService(None, JsonStorageProvider(tmp_path / "translations.json"))
    translations.save_translation(
        Translation(
            title="Vorhanden",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[align_word_pairs("Hola amigo", "Hallo Freund", [("Hola", "Hallo"), ("amigo", "Freund")])],
        )
    )
    main_window = MainWindow(AppServices(translations, settings, MagicMock(speech_speed=1.0)))
    qtbot.addWidget(main_window)
    return main_window


def _create_manual_translation(window: MainWindow, title: str) -> None:
    view = window._translation_view
    view._new_button.click()
    panel = view._create_panel
    panel._title_input.setText(title)
    panel._text_input.setPlainText("Buenos días")
    providers = panel._provider_selector._combo
    providers.setCurrentIndex(providers.count() - 1)  # manual entry, no AI
    panel._create_button.click()


def _listed_titles(window: MainWindow) -> list[str]:
    combo = window._translation_view._translation_combo
    return [combo.itemText(i) for i in range(combo.count())]


class TestTranslationList:
    def test_new_translation_appears_in_the_list_and_is_selected(self, window: MainWindow) -> None:
        _create_manual_translation(window, "Neu")

        combo = window._translation_view._translation_combo
        assert sorted(_listed_titles(window)) == ["Neu", "Vorhanden"]
        assert combo.currentText() == "Neu"
        assert window._app_state.mode == AppMode.EDIT

    def test_refreshing_the_list_does_not_leave_edit_mode(self, window: MainWindow) -> None:
        _create_manual_translation(window, "Neu")

        assert window._app_state.mode == AppMode.EDIT
        assert window._app_state.selected_translation is not None
        assert window._app_state.selected_translation.title == "Neu"


class TestNaturalTranslationEditor:
    def test_editable_after_creating_a_translation(self, window: MainWindow) -> None:
        """'New' clears the selection, which disables the editor; loading a translation must enable it again."""
        _create_manual_translation(window, "Neu")

        natural_editor = window._translation_view._edit_panel._natural_editor
        assert natural_editor._text_edit.isEnabled()
        assert natural_editor._generate_button.isEnabled()

    def test_editable_when_editing_an_existing_translation_after_new(self, window: MainWindow) -> None:
        view = window._translation_view
        view._new_button.click()
        view._create_panel._cancel_button.click()

        view._translation_combo.setCurrentIndex(view._translation_combo.findText("Vorhanden"))
        view._edit_button.click()

        assert view._edit_panel._natural_editor._text_edit.isEnabled()
