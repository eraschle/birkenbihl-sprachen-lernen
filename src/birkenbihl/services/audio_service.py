"""Audio service for text-to-speech operations (Phase 2).

This service is currently a stub and will be implemented in Phase 2
to support the Birkenbihl method's active listening phase.
"""

from pathlib import Path

from birkenbihl.models.translation import Sentence
from birkenbihl.protocols import IAudioProvider


class AudioService:
    """Service for text-to-speech audio generation.

    Supports the Birkenbihl method's active listening phase by generating
    audio files from original language text.

    Status: STUB - Implementation planned for Phase 2
    """

    def __init__(self, audio_provider: IAudioProvider):
        """Initialize service with audio provider.

        Args:
            audio_provider: Provider for TTS operations
        """
        super().__init__()
        self._audio = audio_provider

    def generate_sentence_audio(self, sentence: Sentence, language: str, output_dir: Path) -> Path:
        """Generate audio file for a sentence.

        Args:
            sentence: Sentence to convert to audio
            language: Language code for TTS voice
            output_dir: Directory to save audio file

        Returns:
            Path to generated audio file

        Raises:
            AudioError: If generation fails
            NotImplementedError: Currently not implemented (Phase 2)
        """
        raise NotImplementedError("Audio generation will be implemented in Phase 2")

    def play_sentence(self, sentence: Sentence, language: str) -> None:
        """Play sentence audio directly.

        Args:
            sentence: Sentence to play
            language: Language code for TTS voice

        Raises:
            AudioError: If playback fails
            NotImplementedError: Currently not implemented (Phase 2)
        """
        raise NotImplementedError("Audio playback will be implemented in Phase 2")

    def batch_generate_audio(self, sentences: list[Sentence], language: str, output_dir: Path) -> list[Path]:
        """Generate audio files for multiple sentences.

        Args:
            sentences: List of sentences to convert
            language: Language code for TTS voice
            output_dir: Directory to save audio files

        Returns:
            List of paths to generated audio files

        Raises:
            AudioError: If generation fails
            NotImplementedError: Currently not implemented (Phase 2)
        """
        raise NotImplementedError("Batch audio generation will be implemented in Phase 2")
