"""Local text-to-speech with Piper (https://github.com/rhasspy/piper): free, offline after the first use.

Voices are downloaded once per language (about 60 MB each, from Hugging Face) and kept in the voices directory.
"""

import io
import logging
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig
from piper.download_voices import download_voice

from birkenbihl.exceptions import AudioError
from birkenbihl.protocols.audio import AudioClip

logger = logging.getLogger(__name__)

# One medium-quality voice per language. Languages missing here have no Piper voice of that quality
# (e.g. ja, ko, el, he); they need a cloud provider.
VOICES = {
    "ar": "ar_JO-kareem-medium",
    "cs": "cs_CZ-jirka-medium",
    "da": "da_DK-talesyntese-medium",
    "de": "de_DE-thorsten-medium",
    "en": "en_US-lessac-medium",
    "es": "es_ES-davefx-medium",
    "fa": "fa_IR-amir-medium",
    "fi": "fi_FI-harri-medium",
    "fr": "fr_FR-siwis-medium",
    "hi": "hi_IN-pratham-medium",
    "hu": "hu_HU-anna-medium",
    "it": "it_IT-paola-medium",
    "lv": "lv_LV-aivars-medium",
    "nl": "nl_NL-pim-medium",
    "no": "no_NO-talesyntese-medium",
    "pl": "pl_PL-gosia-medium",
    "pt": "pt_BR-faber-medium",
    "ro": "ro_RO-mihai-medium",
    "ru": "ru_RU-irina-medium",
    "sk": "sk_SK-lili-medium",
    "sl": "sl_SI-artur-medium",
    "sv": "sv_SE-nst-medium",
    "tr": "tr_TR-dfki-medium",
    "uk": "uk_UA-ukrainian_tts-medium",
    "vi": "vi_VN-vais1000-medium",
    "zh": "zh_CN-huayan-medium",
}


class PiperAudioProvider:
    """IAudioProvider using local Piper voices (WAV output)."""

    name = "Piper (lokal)"

    def __init__(self, voices_dir: Path):
        self._voices_dir = voices_dir
        self._loaded: dict[str, PiperVoice] = {}

    def supports(self, language_code: str) -> bool:
        return language_code in VOICES

    def synthesize(self, text: str, language_code: str, speed: float = 1.0) -> AudioClip:
        voice = self._voice(language_code)
        buffer = io.BytesIO()
        try:
            with wave.open(buffer, "wb") as wav_file:
                # length_scale stretches phoneme durations (slower without changing pitch); relative to the
                # voice's own default so "normal" sounds the way the voice was tuned
                config = SynthesisConfig(length_scale=voice.config.length_scale / speed)
                voice.synthesize_wav(text, wav_file, config)
        except Exception as e:
            raise AudioError(f"Piper konnte den Text nicht sprechen: {e}") from e
        return AudioClip(buffer.getvalue(), "wav")

    def _voice(self, language_code: str) -> PiperVoice:
        if not self.supports(language_code):
            raise AudioError(f"Piper hat keine Stimme für die Sprache '{language_code}'")
        if language_code not in self._loaded:
            self._loaded[language_code] = PiperVoice.load(self._voice_file(VOICES[language_code]))
        return self._loaded[language_code]

    def _voice_file(self, voice_name: str) -> Path:
        model = self._voices_dir / f"{voice_name}.onnx"
        if not model.exists() or not model.with_suffix(".onnx.json").exists():
            logger.info("Downloading Piper voice %s to %s", voice_name, self._voices_dir)
            self._voices_dir.mkdir(parents=True, exist_ok=True)
            try:
                download_voice(voice_name, self._voices_dir)
            except Exception as e:
                model.unlink(missing_ok=True)  # do not keep a half-downloaded model
                raise AudioError(f"Piper-Stimme {voice_name} konnte nicht geladen werden: {e}") from e
        return model
