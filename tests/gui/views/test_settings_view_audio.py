"""Qt tests for the audio section of the settings view."""

from pathlib import Path

from pytestqt.qtbot import QtBot

from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.gui.views.settings_view import SettingsView
from birkenbihl.models.settings import AudioSettings
from birkenbihl.services.settings_service import SettingsService


def _view(qtbot: QtBot, path: Path) -> tuple[SettingsView, SettingsViewModel]:
    service = SettingsService(path)
    service.load_settings()
    viewmodel = SettingsViewModel(service)
    view = SettingsView(viewmodel)
    qtbot.addWidget(view)
    return view, viewmodel


def test_audio_settings_are_shown(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("audio:\n  provider: elevenlabs\n  elevenlabs_api_key: key\n  elevenlabs_voice_id: v1\n")

    view, _ = _view(qtbot, path)

    assert view._audio_provider_combo.currentData() == "elevenlabs"
    assert view._elevenlabs_key_edit.text() == "key"
    assert view._elevenlabs_voice_edit.text() == "v1"


def test_entered_audio_settings_are_saved(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    view, viewmodel = _view(qtbot, path)

    view._elevenlabs_key_edit.setText("secret")
    view._elevenlabs_key_edit.editingFinished.emit()
    view._audio_provider_combo.setCurrentIndex(view._audio_provider_combo.findData("elevenlabs"))
    viewmodel.save_settings()

    reloaded = SettingsService(path)
    reloaded.load_settings()
    assert reloaded.get_settings().audio == AudioSettings(provider="elevenlabs", elevenlabs_api_key="secret")


def test_editing_audio_settings_keeps_speech_speed(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "settings.yaml"
    path.write_text("audio:\n  speech_speed: 0.7\n")
    view, viewmodel = _view(qtbot, path)

    view._elevenlabs_key_edit.setText("secret")
    view._elevenlabs_key_edit.editingFinished.emit()

    assert viewmodel.audio.speech_speed == 0.7
    assert viewmodel.audio.elevenlabs_api_key == "secret"
