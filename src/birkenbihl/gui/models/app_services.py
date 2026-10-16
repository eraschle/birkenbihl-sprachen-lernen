"""The application services the GUI works with, created once in gui/main.py."""

from dataclasses import dataclass

from birkenbihl.services.audio_service import AudioService
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


@dataclass(frozen=True)
class AppServices:
    translation: TranslationService
    settings: SettingsService
    audio: AudioService
