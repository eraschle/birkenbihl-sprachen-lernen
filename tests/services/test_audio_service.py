"""Tests for AudioService: provider choice, caching and saving files."""

from pathlib import Path

import pytest

from birkenbihl.exceptions import AudioError
from birkenbihl.models.settings import AudioSettings
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.protocols.audio import AudioClip
from birkenbihl.services.audio_service import AudioService
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.settings_service import SettingsService


class FakeProvider:
    def __init__(self, name: str, languages: set[str], extension: str):
        self.name = name
        self._languages = languages
        self._extension = extension
        self.calls: list[tuple[str, str]] = []
        self.speeds: list[float] = []

    def supports(self, language_code: str) -> bool:
        return language_code in self._languages

    def synthesize(self, text: str, language_code: str, speed: float = 1.0) -> AudioClip:
        self.calls.append((text, language_code))
        self.speeds.append(speed)
        return AudioClip(f"{self.name}:{text}".encode(), self._extension)


@pytest.fixture
def piper() -> FakeProvider:
    return FakeProvider("Piper", {"es", "de"}, "wav")


@pytest.fixture
def cloud() -> FakeProvider:
    return FakeProvider("ElevenLabs", {"es", "de", "ja"}, "mp3")


def _service(tmp_path: Path, piper: FakeProvider, cloud: FakeProvider, audio: AudioSettings) -> AudioService:
    settings = SettingsService(tmp_path / "settings.yaml")
    settings.load_settings()
    settings.get_settings().audio = audio
    return AudioService(settings, piper, tmp_path / "cache", lambda _: cloud)


def _translation(language: str, *texts: str) -> Translation:
    sentences = [Sentence(source_text=t, natural_translation="", word_alignments=[]) for t in texts]
    return Translation(
        title="t", source_language=get_language_by(language), target_language=get_language_by("de"), sentences=sentences
    )


WITH_KEY = AudioSettings(elevenlabs_api_key="key")


class TestProviderChoice:
    def test_piper_by_default(self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider) -> None:
        assert _service(tmp_path, piper, cloud, WITH_KEY).provider_for("es") is piper

    def test_elevenlabs_when_preferred(self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider) -> None:
        audio = AudioSettings(provider="elevenlabs", elevenlabs_api_key="key")

        assert _service(tmp_path, piper, cloud, audio).provider_for("es") is cloud

    def test_elevenlabs_for_language_without_piper_voice(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        assert _service(tmp_path, piper, cloud, WITH_KEY).provider_for("ja") is cloud

    def test_preferred_elevenlabs_without_key_falls_back_to_piper(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        assert _service(tmp_path, piper, cloud, AudioSettings(provider="elevenlabs")).provider_for("es") is piper

    def test_no_voice_and_no_key_explains_what_to_do(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        with pytest.raises(AudioError, match="ElevenLabs-API-Key eintragen"):
            _service(tmp_path, piper, cloud, AudioSettings()).provider_for("ja")


class TestAudioFiles:
    def test_sentence_audio_speaks_the_source_text(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        translation = _translation("es", "Yo te extrañaré.")

        path = _service(tmp_path, piper, cloud, AudioSettings()).sentence_audio(translation.sentences[0], translation)

        assert path.suffix == ".wav"
        assert path.read_text() == "Piper:Yo te extrañaré."
        assert piper.calls == [("Yo te extrañaré.", "es")]

    def test_repeated_listening_uses_the_cache(self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider) -> None:
        service = _service(tmp_path, piper, cloud, AudioSettings())
        translation = _translation("es", "Hola.")

        first = service.sentence_audio(translation.sentences[0], translation)
        second = service.sentence_audio(translation.sentences[0], translation)

        assert first == second
        assert len(piper.calls) == 1

    def test_changed_text_is_synthesized_again(self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider) -> None:
        service = _service(tmp_path, piper, cloud, AudioSettings())
        translation = _translation("es", "Hola.")
        service.sentence_audio(translation.sentences[0], translation)

        translation.sentences[0].source_text = "Hola amigo."
        service.sentence_audio(translation.sentences[0], translation)

        assert len(piper.calls) == 2

    def test_text_audio_speaks_all_sentences(self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider) -> None:
        translation = _translation("es", "Hola.", "¿Cómo estás?")

        path = _service(tmp_path, piper, cloud, AudioSettings()).text_audio(translation)

        assert path.read_text() == "Piper:Hola. ¿Cómo estás?"

    def test_save_as_uses_the_real_file_type(self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider) -> None:
        service = _service(tmp_path, piper, cloud, AudioSettings(provider="elevenlabs", elevenlabs_api_key="k"))
        translation = _translation("es", "Hola.")
        audio = service.sentence_audio(translation.sentences[0], translation)

        saved = service.save_as(audio, tmp_path / "export" / "Lektion 1.wav")

        assert saved == tmp_path / "export" / "Lektion 1.mp3"
        assert saved.read_bytes() == b"ElevenLabs:Hola."


class TestSpeechSpeed:
    def test_audio_is_generated_at_the_chosen_speed(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        service = _service(tmp_path, piper, cloud, AudioSettings(speech_speed=0.85))
        translation = _translation("es", "Hola.")

        service.sentence_audio(translation.sentences[0], translation)

        assert piper.speeds == [0.85]

    def test_slow_and_normal_versions_are_cached_separately(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        service = _service(tmp_path, piper, cloud, AudioSettings())
        translation = _translation("es", "Hola.")

        normal = service.sentence_audio(translation.sentences[0], translation)
        service.set_speech_speed(0.7)
        slow = service.sentence_audio(translation.sentences[0], translation)
        service.set_speech_speed(1.0)
        normal_again = service.sentence_audio(translation.sentences[0], translation)

        assert slow != normal
        assert normal_again == normal
        assert piper.speeds == [1.0, 0.7]

    def test_speed_change_keeps_other_audio_settings(
        self, tmp_path: Path, piper: FakeProvider, cloud: FakeProvider
    ) -> None:
        service = _service(tmp_path, piper, cloud, AudioSettings(provider="elevenlabs", elevenlabs_api_key="k"))

        service.set_speech_speed(0.7)

        assert service.provider_for("es") is cloud
        assert service.speech_speed == 0.7

    @pytest.mark.parametrize("speed", [0.5, 1.3])
    def test_speed_outside_supported_range_is_rejected(self, speed: float) -> None:
        with pytest.raises(ValueError, match="speech_speed"):
            AudioSettings(speech_speed=speed)


class TestAudioSettingsPersistence:
    def test_audio_settings_survive_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.yaml"
        service = SettingsService(path)
        service.load_settings()
        service.get_settings().audio = AudioSettings(
            provider="elevenlabs", elevenlabs_api_key="key", elevenlabs_voice_id="v1", speech_speed=0.85
        )
        service.save_settings()

        reloaded = SettingsService(path)
        reloaded.load_settings()

        assert reloaded.get_settings().audio == AudioSettings(
            provider="elevenlabs", elevenlabs_api_key="key", elevenlabs_voice_id="v1", speech_speed=0.85
        )

    def test_settings_without_audio_section_use_piper(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.yaml"
        path.write_text("target_language: de\nproviders: []\n")
        service = SettingsService(path)
        service.load_settings()

        assert service.get_settings().audio.provider == "piper"
