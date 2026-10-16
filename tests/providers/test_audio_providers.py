"""Tests for the Piper (local) and ElevenLabs (cloud) text-to-speech providers."""

import json
import os
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from birkenbihl.exceptions import AudioError
from birkenbihl.providers.elevenlabs_audio_provider import DEFAULT_VOICE_ID, MODEL_ID, ElevenLabsAudioProvider
from birkenbihl.providers.piper_audio_provider import VOICES, PiperAudioProvider


class FakeVoice:
    def synthesize_wav(self, text: str, wav_file: wave.Wave_write, config: object) -> None:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * len(text))


def _with_voice_files(voices_dir: Path, voice: str) -> None:
    voices_dir.mkdir(parents=True, exist_ok=True)
    (voices_dir / f"{voice}.onnx").write_bytes(b"model")
    (voices_dir / f"{voice}.onnx.json").write_text("{}")


class TestPiperAudioProvider:
    def test_supported_languages(self) -> None:
        provider = PiperAudioProvider(Path("unused"))

        assert provider.supports("es")
        assert provider.supports("de")
        assert not provider.supports("ja")

    def test_synthesize_returns_wav_and_loads_voice_once(self, tmp_path: Path) -> None:
        _with_voice_files(tmp_path, VOICES["es"])
        provider = PiperAudioProvider(tmp_path)

        with patch("birkenbihl.providers.piper_audio_provider.PiperVoice.load", return_value=FakeVoice()) as load:
            first = provider.synthesize("Hola", "es")
            provider.synthesize("Adiós", "es")

        assert first.file_extension == "wav"
        assert first.data.startswith(b"RIFF")
        load.assert_called_once_with(tmp_path / f"{VOICES['es']}.onnx")

    def test_missing_voice_is_downloaded(self, tmp_path: Path) -> None:
        provider = PiperAudioProvider(tmp_path / "voices")

        def fake_download(voice: str, directory: Path) -> None:
            _with_voice_files(directory, voice)

        with (
            patch("birkenbihl.providers.piper_audio_provider.download_voice", side_effect=fake_download) as download,
            patch("birkenbihl.providers.piper_audio_provider.PiperVoice.load", return_value=FakeVoice()),
        ):
            provider.synthesize("Hallo", "de")

        download.assert_called_once_with(VOICES["de"], tmp_path / "voices")

    def test_failed_download_raises_audio_error_and_leaves_no_partial_model(self, tmp_path: Path) -> None:
        provider = PiperAudioProvider(tmp_path)

        def broken_download(voice: str, directory: Path) -> None:
            (directory / f"{voice}.onnx").write_bytes(b"half")
            raise OSError("connection reset")

        with (
            patch("birkenbihl.providers.piper_audio_provider.download_voice", side_effect=broken_download),
            pytest.raises(AudioError, match="konnte nicht geladen werden"),
        ):
            provider.synthesize("Hallo", "de")

        assert not (tmp_path / f"{VOICES['de']}.onnx").exists()

    def test_unsupported_language(self) -> None:
        with pytest.raises(AudioError, match="keine Stimme"):
            PiperAudioProvider(Path("unused")).synthesize("こんにちは", "ja")

    @pytest.mark.slow
    @pytest.mark.skipif(not os.environ.get("BIRKENBIHL_PIPER_VOICES"), reason="set BIRKENBIHL_PIPER_VOICES to a dir")
    def test_real_german_voice(self) -> None:
        """Real synthesis; the voice is downloaded into BIRKENBIHL_PIPER_VOICES if missing."""
        clip = PiperAudioProvider(Path(os.environ["BIRKENBIHL_PIPER_VOICES"])).synthesize("Guten Morgen", "de")

        assert clip.data.startswith(b"RIFF")
        assert len(clip.data) > 10_000


def _elevenlabs(handler) -> ElevenLabsAudioProvider:  # type: ignore[no-untyped-def]
    return ElevenLabsAudioProvider("secret-key", client=httpx.Client(transport=httpx.MockTransport(handler)))


class TestElevenLabsAudioProvider:
    def test_request_and_mp3_response(self) -> None:
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, content=b"ID3mp3-bytes")

        clip = _elevenlabs(handler).synthesize("Yo te extrañaré", "es")

        assert clip.data == b"ID3mp3-bytes"
        assert clip.file_extension == "mp3"
        request = seen[0]
        assert request.url.path == f"/v1/text-to-speech/{DEFAULT_VOICE_ID}"
        assert request.headers["xi-api-key"] == "secret-key"
        assert json.loads(request.content) == {"text": "Yo te extrañaré", "model_id": MODEL_ID, "language_code": "es"}

    def test_api_error_becomes_audio_error(self) -> None:
        provider = _elevenlabs(lambda request: httpx.Response(401, text="invalid api key"))

        with pytest.raises(AudioError, match="401: invalid api key"):
            provider.synthesize("Hola", "es")

    def test_network_error_becomes_audio_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("blocked")

        with pytest.raises(AudioError, match="nicht erreichbar"):
            _elevenlabs(handler).synthesize("Hola", "es")

    def test_covers_languages_piper_lacks(self) -> None:
        provider = ElevenLabsAudioProvider("key", client=MagicMock())

        assert provider.supports("ja")
        assert provider.supports("ko")
        assert not provider.supports("xx")
