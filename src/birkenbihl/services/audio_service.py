"""Audio service for text-to-speech operations.

Supports the Birkenbihl method's active listening phase by generating
audio files from original language text.
"""

from pathlib import Path
from uuid import UUID

from birkenbihl.models.translation import Sentence
from birkenbihl.protocols import IAudioProvider


class AudioService:
    """Service for text-to-speech audio generation.

    Coordinates audio provider to generate speech files for sentences.
    Follows SOLID principles with dependency injection via IAudioProvider.
    """

    def __init__(self, audio_provider: IAudioProvider):
        """Initialize service with audio provider.

        Args:
            audio_provider: Provider for TTS operations
        """
        self._audio = audio_provider

    def generate_sentence_audio(self, sentence: Sentence, language: str, output_dir: Path) -> Path:
        """Generate audio file for a sentence.

        Audio filename format: {sentence_uuid}.mp3

        Args:
            sentence: Sentence to convert to audio
            language: Language code for TTS voice (en, es, de, etc.)
            output_dir: Directory to save audio file

        Returns:
            Path to generated audio file

        Raises:
            ValueError: If language not supported
            RuntimeError: If audio generation fails
        """
        filename = self._get_audio_filename(sentence.uuid)
        output_path = output_dir / filename

        return self._audio.save_audio_file(sentence.source_text, language, output_path)

    def batch_generate_audio(self, sentences: list[Sentence], language: str, output_dir: Path) -> list[Path]:
        """Generate audio files for multiple sentences.

        Args:
            sentences: List of sentences to convert
            language: Language code for TTS voice
            output_dir: Directory to save audio files

        Returns:
            List of paths to generated audio files

        Raises:
            ValueError: If language not supported
            RuntimeError: If audio generation fails for any sentence
        """
        paths: list[Path] = []

        for sentence in sentences:
            audio_path = self.generate_sentence_audio(sentence, language, output_dir)
            paths.append(audio_path)

        return paths

    def get_audio_path(self, sentence_uuid: UUID, audio_dir: Path) -> Path:
        """Get expected audio file path for a sentence.

        Args:
            sentence_uuid: UUID of sentence
            audio_dir: Directory containing audio files

        Returns:
            Expected path to audio file
        """
        filename = self._get_audio_filename(sentence_uuid)
        return audio_dir / filename

    def audio_exists(self, sentence_uuid: UUID, audio_dir: Path) -> bool:
        """Check if audio file exists for sentence.

        Args:
            sentence_uuid: UUID of sentence
            audio_dir: Directory containing audio files

        Returns:
            True if audio file exists
        """
        audio_path = self.get_audio_path(sentence_uuid, audio_dir)
        return audio_path.exists()

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes.

        Returns:
            List of ISO 639-1 language codes
        """
        return self._audio.get_supported_languages()

    def _get_audio_filename(self, sentence_uuid: UUID) -> str:
        """Generate audio filename from sentence UUID.

        Args:
            sentence_uuid: Sentence UUID

        Returns:
            Filename string (e.g., "a1b2c3d4.mp3")
        """
        return f"{sentence_uuid}.mp3"
