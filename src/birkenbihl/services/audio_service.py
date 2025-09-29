"""Audio Service mit edge-tts für Text-to-Speech."""

import tempfile
from pathlib import Path
from typing import Any

import edge_tts
from pydub import AudioSegment
from pydub.playback import play

from ..models.audio import AudioData, AudioFormat, AudioQuality
from ..protocols.audio import (
    AudioConversionError,
    AudioMixingError,
    AudioPlaybackError,
    AudioServiceError,
    TTSError,
    UnsupportedFormatError,
    UnsupportedLanguageError,
)


class EdgeTTSAudioService:
    """Audio Service mit edge-tts für Text-to-Speech und Playback."""

    def __init__(self) -> None:
        """Initialize the EdgeTTS Audio Service."""
        self._current_playback: Any = None
        self._temp_files: list[Path] = []

    async def generate_speech(
        self,
        text: str,
        language_code: str,
        voice_name: str | None = None,
        speech_rate: float = 1.0,
        quality: AudioQuality = AudioQuality.MEDIUM,
    ) -> AudioData:
        """Generate speech from text using edge-tts.

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
        if not self.validate_speech_rate(speech_rate):
            raise TTSError(f"Invalid speech rate: {speech_rate}. Must be between 0.1 and 3.0")

        try:
            # Get available voices for language
            voices = await self.get_available_voices(language_code)
            if not voices:
                raise UnsupportedLanguageError(f"Language '{language_code}' not supported")

            # Use provided voice or default to first available
            selected_voice = voice_name if voice_name in voices else voices[0]

            # Create TTS instance
            communicate = edge_tts.Communicate(text, selected_voice, rate=self._format_rate(speech_rate))

            # Generate audio to temporary file
            temp_file = Path(tempfile.mktemp(suffix=".wav"))
            self._temp_files.append(temp_file)

            await communicate.save(str(temp_file))

            # Get audio info using pydub
            audio_segment = AudioSegment.from_file(temp_file)
            duration = len(audio_segment) / 1000.0  # Convert ms to seconds

            # Create AudioData object
            audio_data = AudioData(
                file_path=str(temp_file),
                file_name=temp_file.name,
                file_size=temp_file.stat().st_size,
                file_format=AudioFormat.WAV,
                duration=duration,
                sample_rate=audio_segment.frame_rate,
                channels=audio_segment.channels,
                quality=quality,
                is_generated=True,
                tts_engine="edge-tts",
                voice_name=selected_voice,
                speech_rate=speech_rate,
            )

            return audio_data

        except Exception as e:
            raise TTSError(f"Failed to generate speech: {e}") from e

    def play_audio(self, audio_data: AudioData) -> None:
        """Play audio from AudioData object.

        Args:
            audio_data: Audio data to play

        Raises:
            AudioPlaybackError: If playback fails
            FileNotFoundError: If audio file doesn't exist
        """
        self.play_audio_file(audio_data.file_path_obj)

    def play_audio_file(self, file_path: Path) -> None:
        """Play audio file directly.

        Args:
            file_path: Path to audio file

        Raises:
            AudioPlaybackError: If playback fails
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            audio_segment = AudioSegment.from_file(file_path)
            self.stop_playback()  # Stop any current playback
            play(audio_segment)
        except Exception as e:
            raise AudioPlaybackError(f"Failed to play audio: {e}") from e

    def stop_playback(self) -> None:
        """Stop current audio playback."""
        if self._current_playback:
            try:
                self._current_playback.terminate()
            except Exception:
                pass  # Ignore errors when stopping
            finally:
                self._current_playback = None

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
        if not self.is_format_supported(target_format):
            raise UnsupportedFormatError(f"Format '{target_format}' not supported")

        try:
            # Load audio
            audio_segment = AudioSegment.from_file(input_data.file_path)

            # Create output file
            output_path = Path(tempfile.mktemp(suffix=f".{target_format.value}"))
            self._temp_files.append(output_path)

            # Set quality parameters
            quality_params = self._get_quality_params(target_quality or input_data.quality)

            # Export with quality settings
            audio_segment.export(str(output_path), format=target_format.value, **quality_params)

            # Create new AudioData
            converted_data = AudioData(
                file_path=str(output_path),
                file_name=output_path.name,
                file_size=output_path.stat().st_size,
                file_format=target_format,
                duration=len(audio_segment) / 1000.0,
                sample_rate=audio_segment.frame_rate,
                channels=audio_segment.channels,
                quality=target_quality or input_data.quality,
                is_generated=input_data.is_generated,
                tts_engine=input_data.tts_engine,
                voice_name=input_data.voice_name,
                speech_rate=input_data.speech_rate,
            )

            return converted_data

        except Exception as e:
            raise AudioConversionError(f"Failed to convert audio: {e}") from e

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
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            audio_segment = AudioSegment.from_file(file_path)
            file_format = AudioFormat(file_path.suffix.lower().lstrip("."))

            audio_data = AudioData(
                file_path=str(file_path),
                file_name=file_path.name,
                file_size=file_path.stat().st_size,
                file_format=file_format,
                duration=len(audio_segment) / 1000.0,
                sample_rate=audio_segment.frame_rate,
                channels=audio_segment.channels,
                quality=AudioQuality.MEDIUM,  # Default quality
            )

            return audio_data

        except Exception as e:
            raise UnsupportedFormatError(f"Failed to read audio file: {e}") from e

    def is_format_supported(self, format_type: AudioFormat) -> bool:
        """Check if audio format is supported.

        Args:
            format_type: Audio format to check

        Returns:
            True if format is supported, False otherwise
        """
        supported_formats = {AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OGG, AudioFormat.FLAC}
        return format_type in supported_formats

    async def get_available_voices(self, language_code: str | None = None) -> list[str]:
        """Get available TTS voices.

        Args:
            language_code: Optional language to filter voices

        Returns:
            List of available voice names
        """
        try:
            voices = await edge_tts.list_voices()
            if language_code:
                # Filter by language code
                filtered_voices = [
                    voice["Name"] for voice in voices if voice["Locale"].startswith(language_code.lower())
                ]
                return filtered_voices
            else:
                return [voice["Name"] for voice in voices]
        except Exception:
            return []

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

        Args:
            primary_audio: Main audio (speech)
            background_music_path: Optional background music file
            volume_ratio: Background music volume relative to speech

        Returns:
            AudioData with mixed audio

        Raises:
            AudioMixingError: If audio mixing fails
        """
        try:
            # Load primary audio
            primary_segment = AudioSegment.from_file(primary_audio.file_path)

            if background_music_path and background_music_path.exists():
                # Load background music
                background_segment = AudioSegment.from_file(background_music_path)

                # Adjust volumes
                background_volume = volume_ratio
                background_segment = background_segment - (20 * (1 - background_volume))

                # Loop background music to match primary audio length
                if len(background_segment) < len(primary_segment):
                    loops_needed = (len(primary_segment) // len(background_segment)) + 1
                    background_segment = background_segment * loops_needed

                # Trim to match primary length
                background_segment = background_segment[: len(primary_segment)]

                # Mix audio
                mixed_audio = primary_segment.overlay(background_segment)
            else:
                # No background music, return primary audio
                mixed_audio = primary_segment

            # Save mixed audio
            output_path = Path(tempfile.mktemp(suffix=".wav"))
            self._temp_files.append(output_path)
            mixed_audio.export(str(output_path), format="wav")

            # Create AudioData
            mixed_data = AudioData(
                file_path=str(output_path),
                file_name=output_path.name,
                file_size=output_path.stat().st_size,
                file_format=AudioFormat.WAV,
                duration=len(mixed_audio) / 1000.0,
                sample_rate=mixed_audio.frame_rate,
                channels=mixed_audio.channels,
                quality=primary_audio.quality,
                is_generated=True,
                tts_engine=primary_audio.tts_engine,
                voice_name=primary_audio.voice_name,
                speech_rate=primary_audio.speech_rate,
                is_background_music=True,
            )

            return mixed_data

        except Exception as e:
            raise AudioMixingError(f"Failed to create background audio: {e}") from e

    def cleanup_temp_files(self) -> None:
        """Clean up temporary audio files."""
        for temp_file in self._temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors
        self._temp_files.clear()

    def _format_rate(self, rate: float) -> str:
        """Format speech rate for edge-tts."""
        if rate == 1.0:
            return "+0%"
        elif rate > 1.0:
            percentage = int((rate - 1.0) * 100)
            return f"+{percentage}%"
        else:
            percentage = int((1.0 - rate) * 100)
            return f"-{percentage}%"

    def _get_quality_params(self, quality: AudioQuality) -> dict[str, Any]:
        """Get quality parameters for audio export."""
        quality_map = {
            AudioQuality.LOW: {"bitrate": "64k"},
            AudioQuality.MEDIUM: {"bitrate": "128k"},
            AudioQuality.HIGH: {"bitrate": "192k"},
            AudioQuality.LOSSLESS: {"bitrate": "320k"},
        }
        return quality_map.get(quality, quality_map[AudioQuality.MEDIUM])

    def __del__(self) -> None:
        """Cleanup when service is destroyed."""
        self.cleanup_temp_files()
