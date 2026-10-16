"""Text-to-speech provider protocol."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AudioClip:
    """Synthesized speech, ready to be written to a file."""

    data: bytes
    file_extension: str  # without dot, e.g. "wav" or "mp3"


class IAudioProvider(Protocol):
    """Turns text into speech for the Birkenbihl listening phase."""

    name: str

    def supports(self, language_code: str) -> bool:
        """Whether this provider has a voice for the language (ISO 639-1 code, e.g. "es")."""
        ...

    def synthesize(self, text: str, language_code: str, speed: float = 1.0) -> AudioClip:
        """Speak the text in the given language; speed 1.0 is normal, below 1.0 slower.

        Raises:
            AudioError: If the language is not supported or synthesis fails
        """
        ...
