"""Audio service protocols for abstraction."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models.audio import AudioData, AudioFormat, AudioQuality


@runtime_checkable
class AudioService(Protocol):
    """Protocol for audio services.

    This protocol defines the interface for audio-related services
    in the Birkenbihl learning method.
    """

    def generate_speech(
        self,
        text: str,
        language_code: str,
        voice_name: str | None = None,
        speech_rate: float = 1.0,
        quality: AudioQuality = AudioQuality.MEDIUM,
    ) -> AudioData:
        """Generate speech from text using TTS.

        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'en', 'de', 'es')
            voice_name: Optional specific voice to use
            speech_rate: Speech rate multiplier (0.1 to 3.0)
            quality: Audio quality level

        Returns:
            AudioData object with generated audio information

        Raises:
            TTSError: If text-to-speech generation fails
            UnsupportedLanguageError: If language not supported
        """
        ...

    def play_audio(self, audio_data: AudioData) -> None:
        """Play audio from AudioData object.

        Args:
            audio_data: Audio data to play

        Raises:
            AudioPlaybackError: If playback fails
            FileNotFoundError: If audio file doesn't exist
        """
        ...

    def play_audio_file(self, file_path: Path) -> None:
        """Play audio file directly.

        Args:
            file_path: Path to audio file

        Raises:
            AudioPlaybackError: If playback fails
            FileNotFoundError: If file doesn't exist
        """
        ...

    def stop_playback(self) -> None:
        """Stop current audio playback."""
        ...

    def convert_audio_format(
        self,
        input_data: AudioData,
        target_format: AudioFormat,
        target_quality: AudioQuality | None = None,
    ) -> AudioData:
        """Convert audio to different format.

        Args:
            input_data: Input audio data
            target_format: Target audio format
            target_quality: Optional target quality

        Returns:
            New AudioData with converted audio

        Raises:
            AudioConversionError: If conversion fails
            UnsupportedFormatError: If format not supported
        """
        ...

    def get_audio_info(self, file_path: Path) -> AudioData:
        """Get audio file information.

        Args:
            file_path: Path to audio file

        Returns:
            AudioData object with file information

        Raises:
            FileNotFoundError: If file doesn't exist
            UnsupportedFormatError: If format not supported
        """
        ...

    def is_format_supported(self, format_type: AudioFormat) -> bool:
        """Check if audio format is supported.

        Args:
            format_type: Audio format to check

        Returns:
            True if format is supported, False otherwise
        """
        ...

    def get_available_voices(self, language_code: str | None = None) -> list[str]:
        """Get available TTS voices.

        Args:
            language_code: Optional language to filter voices

        Returns:
            List of available voice names
        """
        ...

    def validate_speech_rate(self, rate: float) -> bool:
        """Validate speech rate parameter.

        Args:
            rate: Speech rate to validate

        Returns:
            True if rate is valid (0.1 to 3.0)
        """
        return 0.1 <= rate <= 3.0

    def create_background_audio(
        self,
        primary_audio: AudioData,
        background_music_path: Path | None = None,
        volume_ratio: float = 0.3,
    ) -> AudioData:
        """Create background audio for passive listening phase.

        Creates audio suitable for the Birkenbihl passive listening phase
        by optionally mixing with background music at lower volume.

        Args:
            primary_audio: Main audio (speech)
            background_music_path: Optional background music file
            volume_ratio: Background music volume relative to speech

        Returns:
            AudioData with mixed audio

        Raises:
            AudioMixingError: If audio mixing fails
        """
        ...


class AudioServiceError(Exception):
    """Base exception for audio service errors."""



class TTSError(AudioServiceError):
    """Raised when text-to-speech generation fails."""



class AudioPlaybackError(AudioServiceError):
    """Raised when audio playback fails."""



class AudioConversionError(AudioServiceError):
    """Raised when audio format conversion fails."""



class UnsupportedFormatError(AudioServiceError):
    """Raised when audio format is not supported."""



class AudioMixingError(AudioServiceError):
    """Raised when audio mixing fails."""

