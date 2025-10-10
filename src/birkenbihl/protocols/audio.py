"""Audio provider protocol for text-to-speech functionality."""

from pathlib import Path
from typing import Protocol


class IAudioProvider(Protocol):
    """Protocol for audio/text-to-speech providers.

    Defines interface for generating audio from text in the original language,
    supporting the Birkenbihl method's active listening phase.
    """

    def generate_audio(self, text: str, language: str) -> bytes:
        """Generate audio data from text.

        Args:
            text: Text to convert to speech
            language: Language code (en, es, de)

        Returns:
            Audio data as bytes (format depends on implementation)

        Raises:
            AudioError: If audio generation fails
        """
        ...

    def save_audio_file(self, text: str, language: str, output_path: Path) -> Path:
        """Generate and save audio to file.

        Args:
            text: Text to convert to speech
            language: Language code (en, es, de)
            output_path: Path where audio file should be saved

        Returns:
            Path to saved audio file

        Raises:
            AudioError: If generation or save fails
        """
        ...

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes.

        Returns:
            List of ISO 639-1 language codes
        """
        ...
