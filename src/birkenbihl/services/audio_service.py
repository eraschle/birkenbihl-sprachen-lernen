"""Audio for the Birkenbihl listening phase: speak sentences or whole texts and save them as files.

The learner listens to the original (source language) text many times, so generated audio is cached:
playing a sentence again does not synthesize it again.
"""

import hashlib
import shutil
from collections.abc import Callable
from pathlib import Path

from birkenbihl.exceptions import AudioError
from birkenbihl.models.settings import AudioSettings
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.protocols.audio import IAudioProvider
from birkenbihl.providers.elevenlabs_audio_provider import DEFAULT_VOICE_ID, ElevenLabsAudioProvider
from birkenbihl.services.settings_service import SettingsService

CloudProviderFactory = Callable[[AudioSettings], IAudioProvider]


def create_elevenlabs(settings: AudioSettings) -> IAudioProvider:
    return ElevenLabsAudioProvider(settings.elevenlabs_api_key, settings.elevenlabs_voice_id or DEFAULT_VOICE_ID)


class AudioService:
    """Chooses a text-to-speech provider per language and manages the generated audio files.

    Provider choice: ElevenLabs if the user prefers it and it speaks the language; otherwise Piper (local)
    if it has a voice; otherwise ElevenLabs if an API key is configured.
    """

    def __init__(
        self,
        settings_service: SettingsService,
        piper: IAudioProvider,
        cache_dir: Path,
        cloud_factory: CloudProviderFactory = create_elevenlabs,
    ):
        self._settings_service = settings_service
        self._piper = piper
        self._cache_dir = cache_dir
        self._cloud_factory = cloud_factory

    def provider_for(self, language_code: str) -> IAudioProvider:
        """Raises AudioError, with a hint what to configure, if no provider speaks the language."""
        settings = self._settings_service.get_settings().audio
        cloud = self._cloud_factory(settings) if settings.elevenlabs_api_key else None
        if settings.provider == "elevenlabs" and cloud and cloud.supports(language_code):
            return cloud
        if self._piper.supports(language_code):
            return self._piper
        if cloud and cloud.supports(language_code):
            return cloud
        hint = "Bitte in den Einstellungen einen ElevenLabs-API-Key eintragen."
        raise AudioError(f"Für die Sprache '{language_code}' gibt es keine lokale Stimme. {hint}")

    def sentence_audio(self, sentence: Sentence, translation: Translation) -> Path:
        """Audio file of one sentence in the source language (generated once, then cached)."""
        return self._audio(sentence.source_text, translation.source_language.code)

    def text_audio(self, translation: Translation) -> Path:
        """Audio file of the whole text in the source language, sentence after sentence."""
        text = " ".join(sentence.source_text for sentence in translation.sentences)
        return self._audio(text, translation.source_language.code)

    @property
    def speech_speed(self) -> float:
        return self._settings_service.get_settings().audio.speech_speed

    def set_speech_speed(self, speed: float) -> None:
        """Remember the speed for the next audio; saved with the other settings."""
        settings = self._settings_service.get_settings()
        settings.audio = settings.audio.model_copy(update={"speech_speed": speed})

    def save_as(self, audio_file: Path, target: Path) -> Path:
        """Copy a generated audio file to where the user wants it; the file type decides the extension."""
        target = target.with_suffix(audio_file.suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(audio_file, target)
        return target

    def _audio(self, text: str, language_code: str) -> Path:
        provider = self.provider_for(language_code)
        speed = self.speech_speed
        key = hashlib.sha256(f"{provider.name}|{language_code}|{speed}|{text}".encode()).hexdigest()[:24]
        cached = next(self._cache_dir.glob(f"{key}.*"), None)
        if cached:
            return cached
        clip = provider.synthesize(text, language_code, speed)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._cache_dir / f"{key}.{clip.file_extension}"
        path.write_bytes(clip.data)
        return path
