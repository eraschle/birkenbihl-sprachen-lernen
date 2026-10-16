"""Qt tests for the listening controls in the translation tab."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtMultimedia import QMediaPlayer
from pytestqt.qtbot import QtBot

from birkenbihl.gui.models.app_services import AppServices
from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.views.main_window import MainWindow
from birkenbihl.gui.widgets.audio_bar import AudioBar
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.protocols.audio import AudioClip
from birkenbihl.services.audio_service import AudioService
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


class FakePiper:
    name = "Piper"

    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.speeds: list[float] = []

    def supports(self, language_code: str) -> bool:
        return language_code == "es"

    def synthesize(self, text: str, language_code: str, speed: float = 1.0) -> AudioClip:
        self.spoken.append(text)
        self.speeds.append(speed)
        return AudioClip(b"RIFF" + text.encode(), "wav")


def _translation(language: str = "es") -> Translation:
    return Translation(
        title="Lektion 1: Abschied",
        source_language=get_language_by(language),
        target_language=get_language_by("de"),
        sentences=[
            Sentence(source_text=text, natural_translation="", word_alignments=[])
            for text in ("Yo te extrañaré.", "Hasta pronto.")
        ],
    )


@pytest.fixture
def piper() -> FakePiper:
    return FakePiper()


@pytest.fixture
def audio_service(tmp_path: Path, piper: FakePiper) -> AudioService:
    settings = SettingsService(tmp_path / "settings.yaml")
    settings.load_settings()
    return AudioService(settings, piper, tmp_path / "cache")


def _bar(qtbot: QtBot, audio_service: AudioService, translation: Translation, sentence_index: int = 0) -> AudioBar:
    state = AppState()
    state.select_translation(translation)
    state.select_sentence(sentence_index)
    bar = AudioBar(audio_service, state)
    qtbot.addWidget(bar)
    return bar


def _wait_idle(qtbot: QtBot, bar: AudioBar) -> None:
    qtbot.waitUntil(lambda: bar._worker is None, timeout=5000)


class TestAudioBar:
    def test_play_sentence_loops_by_default(self, qtbot: QtBot, audio_service: AudioService, piper: FakePiper) -> None:
        bar = _bar(qtbot, audio_service, _translation(), sentence_index=1)

        bar._play_sentence_button.click()
        _wait_idle(qtbot, bar)

        assert piper.spoken == ["Hasta pronto."]
        assert bar._player.source().toLocalFile().endswith(".wav")
        assert bar._player.loops() == QMediaPlayer.Loops.Infinite

    def test_play_once_without_repeat(self, qtbot: QtBot, audio_service: AudioService) -> None:
        bar = _bar(qtbot, audio_service, _translation())
        bar._repeat_check.setChecked(False)

        bar._play_text_button.click()
        _wait_idle(qtbot, bar)

        assert bar._player.loops() == QMediaPlayer.Loops.Once

    def test_save_whole_text_as_file(
        self, qtbot: QtBot, audio_service: AudioService, piper: FakePiper, tmp_path: Path
    ) -> None:
        bar = _bar(qtbot, audio_service, _translation())
        target = tmp_path / "Musik" / "Lektion 1.wav"

        with patch(
            "birkenbihl.gui.widgets.audio_bar.QFileDialog.getSaveFileName", return_value=(str(target), "")
        ) as dlg:
            bar._save_text_button.click()
            _wait_idle(qtbot, bar)

        assert piper.spoken == ["Yo te extrañaré. Hasta pronto."]
        assert target.read_bytes().startswith(b"RIFF")
        assert dlg.call_args.args[2].endswith("Lektion 1 Abschied.wav")
        assert "Gespeichert" in bar._status.text()

    def test_suggested_file_name_contains_sentence_number(self, qtbot: QtBot, audio_service: AudioService) -> None:
        bar = _bar(qtbot, audio_service, _translation(), sentence_index=1)

        with patch("birkenbihl.gui.widgets.audio_bar.QFileDialog.getSaveFileName", return_value=("", "")) as dlg:
            bar._save_sentence_button.click()
            _wait_idle(qtbot, bar)

        assert dlg.call_args.args[2].endswith("Lektion 1 Abschied - Satz 2.wav")

    def test_language_without_voice_shows_what_to_do(self, qtbot: QtBot, audio_service: AudioService) -> None:
        bar = _bar(qtbot, audio_service, _translation("ja"))

        bar._play_sentence_button.click()
        _wait_idle(qtbot, bar)

        assert "ElevenLabs-API-Key" in bar._status.text()
        assert bar._play_sentence_button.isEnabled()

    def test_speed_choice_is_used_for_the_next_audio(
        self, qtbot: QtBot, audio_service: AudioService, piper: FakePiper
    ) -> None:
        bar = _bar(qtbot, audio_service, _translation())
        assert bar._speed_combo.currentData() == 1.0

        bar._speed_combo.setCurrentIndex(bar._speed_combo.findData(0.7))
        bar._play_sentence_button.click()
        _wait_idle(qtbot, bar)

        assert audio_service.speech_speed == 0.7
        assert piper.speeds == [0.7]

    def test_speed_combo_shows_saved_speed(self, qtbot: QtBot, audio_service: AudioService) -> None:
        audio_service.set_speech_speed(0.85)

        bar = _bar(qtbot, audio_service, _translation())

        assert bar._speed_combo.currentData() == 0.85

    def test_buttons_disabled_while_generating(self, qtbot: QtBot, audio_service: AudioService) -> None:
        bar = _bar(qtbot, audio_service, _translation())

        bar._play_sentence_button.click()

        assert not bar._save_text_button.isEnabled()
        _wait_idle(qtbot, bar)
        assert bar._save_text_button.isEnabled()


def test_main_window_shows_audio_bar_for_selected_translation(
    qtbot: QtBot, tmp_path: Path, audio_service: AudioService
) -> None:
    settings = SettingsService(tmp_path / "settings.yaml")
    settings.load_settings()
    services = AppServices(TranslationService(None, JsonStorageProvider(tmp_path / "t.json")), settings, audio_service)
    window = MainWindow(services)
    qtbot.addWidget(window)
    view_panel = window._translation_view._view_panel

    assert view_panel._audio_bar.isHidden()
    window._app_state.select_translation(_translation())
    assert not view_panel._audio_bar.isHidden()
