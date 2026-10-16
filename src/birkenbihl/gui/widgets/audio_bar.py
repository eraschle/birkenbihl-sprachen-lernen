"""Listening controls for the Birkenbihl listening phase: play, repeat and save the original text as audio."""

import re
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.utils.async_helper import AsyncWorker
from birkenbihl.services.audio_service import AudioService

AudioJob = Callable[[], Path]

SPEEDS = [("Sehr langsam (0,7×)", 0.7), ("Langsam (0,85×)", 0.85), ("Normal (1×)", 1.0)]


class AudioBar(QWidget):
    """Speaks the selected sentence or the whole text in the source language.

    Audio is generated in the background (the first Piper use per language also downloads a voice), cached by
    AudioService and can be saved as a file for listening outside the app. "Wiederholen" loops playback,
    because the method relies on hearing the same text many times.
    """

    def __init__(self, audio_service: AudioService, state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = audio_service
        self._state = state
        self._worker: AsyncWorker | None = None
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(QAudioOutput(self))
        self._play_sentence_button = self._button("▶ Satz anhören", lambda: self._run(self._sentence_job(), self._play))
        self._play_text_button = self._button("▶ Ganzer Text", lambda: self._run(self._text_job(), self._play))
        self._stop_button = self._button("⏹ Stopp", self._player.stop)
        self._repeat_check = QCheckBox("Wiederholen")
        self._repeat_check.setChecked(True)
        self._speed_combo = self._create_speed_combo()
        self._save_sentence_button = self._button("💾 Satz speichern…", lambda: self._save(self._sentence_job()))
        self._save_text_button = self._button("💾 Text speichern…", lambda: self._save(self._text_job(), whole=True))
        self._status = QLabel()
        self._init_layout()

    def _init_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for widget in (
            self._play_sentence_button,
            self._play_text_button,
            self._stop_button,
            self._repeat_check,
            self._speed_combo,
            self._save_sentence_button,
            self._save_text_button,
            self._status,
        ):
            layout.addWidget(widget)
        layout.addStretch()

    def _create_speed_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setToolTip("Sprechtempo - langsamer hilft am Anfang beim Mithören")
        for label, speed in SPEEDS:
            combo.addItem(label, userData=speed)
        current = min(SPEEDS, key=lambda item: abs(item[1] - self._service.speech_speed))
        combo.setCurrentIndex(SPEEDS.index(current))
        combo.currentIndexChanged.connect(self._on_speed_changed)
        return combo

    def _on_speed_changed(self) -> None:
        self._service.set_speech_speed(self._speed_combo.currentData())
        self._player.stop()
        self._status.setText("Tempo geändert - zum Anhören erneut ▶ drücken")

    def _button(self, text: str, action: Callable[[], object]) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(action)
        return button

    def _sentence_job(self) -> AudioJob:
        translation = self._state.selected_translation
        if translation is None:
            raise RuntimeError("No translation selected")
        sentence = translation.sentences[self._state.selected_sentence_index]
        return lambda: self._service.sentence_audio(sentence, translation)

    def _text_job(self) -> AudioJob:
        translation = self._state.selected_translation
        if translation is None:
            raise RuntimeError("No translation selected")
        return lambda: self._service.text_audio(translation)

    def _run(self, job: AudioJob, on_ready: Callable[[Path], None]) -> None:
        """Generate audio in the background, then hand the file to on_ready."""
        if self._worker is not None:
            return
        self._set_busy(True)
        self._worker = AsyncWorker(job)
        self._worker.task_completed.connect(lambda path: self._finish(on_ready, path))
        self._worker.task_failed.connect(self._fail)
        self._worker.start()

    def _finish(self, on_ready: Callable[[Path], None], path: object) -> None:
        self._worker = None
        self._set_busy(False)
        assert isinstance(path, Path)
        on_ready(path)

    def _fail(self, message: str) -> None:
        self._worker = None
        self._set_busy(False)
        self._status.setText(f"⚠️ {message}")

    def _play(self, path: Path) -> None:
        loops = QMediaPlayer.Loops.Infinite if self._repeat_check.isChecked() else QMediaPlayer.Loops.Once
        self._player.setLoops(loops)
        self._player.setSource(QUrl.fromLocalFile(str(path)))
        self._player.play()

    def _save(self, job: AudioJob, whole: bool = False) -> None:
        self._run(job, lambda path: self._save_file(path, whole))

    def _save_file(self, path: Path, whole: bool) -> None:
        target, _ = QFileDialog.getSaveFileName(
            self, "Audio speichern", str(Path.home() / self._default_name(path, whole)), f"Audio (*{path.suffix})"
        )
        if target:
            saved = self._service.save_as(path, Path(target))
            self._status.setText(f"Gespeichert: {saved}")

    def _default_name(self, path: Path, whole: bool) -> str:
        translation = self._state.selected_translation
        title = re.sub(r"[^\w\- ]", "", translation.title if translation else "") or "Birkenbihl"
        part = "" if whole else f" - Satz {self._state.selected_sentence_index + 1}"
        return f"{title}{part}{path.suffix}"

    def _set_busy(self, busy: bool) -> None:
        self._status.setText("Erzeuge Audio …" if busy else "")
        for widget in (
            self._play_sentence_button,
            self._play_text_button,
            self._speed_combo,
            self._save_sentence_button,
            self._save_text_button,
        ):
            widget.setEnabled(not busy)
