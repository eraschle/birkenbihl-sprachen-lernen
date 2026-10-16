"""Cloud text-to-speech with ElevenLabs (https://elevenlabs.io): natural voices, needs an API key.

Used when Piper has no voice for a language, or when the user prefers its pronunciation.
"""

import httpx

from birkenbihl.exceptions import AudioError
from birkenbihl.protocols.audio import AudioClip

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
MODEL_ID = "eleven_multilingual_v2"
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # premade voice "George"; any voice of the account works
MIN_SPEED, MAX_SPEED = 0.7, 1.2  # range ElevenLabs accepts for voice_settings.speed

# Languages of eleven_multilingual_v2
LANGUAGES = {
    "ar", "bg", "cs", "da", "de", "el", "en", "es", "fi", "fr", "hi", "hr", "id", "it", "ja", "ko",
    "nl", "pl", "pt", "ro", "ru", "sk", "sv", "tr", "uk", "zh",
}  # fmt: skip


class ElevenLabsAudioProvider:
    """IAudioProvider using the ElevenLabs API (MP3 output)."""

    name = "ElevenLabs"

    def __init__(self, api_key: str, voice_id: str = DEFAULT_VOICE_ID, client: httpx.Client | None = None):
        self._api_key = api_key
        self._voice_id = voice_id
        self._client = client or httpx.Client(timeout=60)

    def supports(self, language_code: str) -> bool:
        return language_code in LANGUAGES

    def synthesize(self, text: str, language_code: str, speed: float = 1.0) -> AudioClip:
        if not self.supports(language_code):
            raise AudioError(f"ElevenLabs unterstützt die Sprache '{language_code}' nicht")
        try:
            response = self._client.post(
                API_URL.format(voice_id=self._voice_id),
                params={"output_format": "mp3_44100_128"},
                headers={"xi-api-key": self._api_key},
                json={
                    "text": text,
                    "model_id": MODEL_ID,
                    "language_code": language_code,
                    "voice_settings": {"speed": min(max(speed, MIN_SPEED), MAX_SPEED)},
                },
            )
        except httpx.HTTPError as e:
            raise AudioError(f"ElevenLabs ist nicht erreichbar: {e}") from e
        if response.status_code != 200:
            raise AudioError(f"ElevenLabs-Fehler {response.status_code}: {response.text[:200]}")
        return AudioClip(response.content, "mp3")
