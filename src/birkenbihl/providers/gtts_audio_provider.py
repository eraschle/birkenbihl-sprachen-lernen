"""Google Text-to-Speech audio provider implementation."""

from pathlib import Path

from gtts import gTTS

from birkenbihl.exceptions import AudioError


class GTTSAudioProvider:
    """Audio provider using Google Text-to-Speech (gTTS).

    Provides free, high-quality text-to-speech generation without API keys.
    Requires internet connection for audio generation.

    Supported Languages:
        - en: English
        - es: Spanish
        - de: German
        - fr: French
        - it: Italian
        - And 50+ more languages
    """

    SUPPORTED_LANGS = ["en", "es", "de", "fr", "it", "pt", "nl", "ru", "ja", "zh", "ar", "hi"]

    def __init__(self, slow: bool = False):
        """Initialize gTTS provider.

        Args:
            slow: If True, uses slower speech rate for learning
        """
        self._slow = slow

    def generate_audio(self, text: str, language: str) -> bytes:
        """Generate audio data from text.

        Args:
            text: Text to convert to speech
            language: Language code (en, es, de, etc.)

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            AudioError: If language not supported or generation fails
        """
        if language not in self.SUPPORTED_LANGS:
            raise AudioError(
                f"Language '{language}' not supported. Supported: {', '.join(self.SUPPORTED_LANGS)}"
            )

        try:
            tts = gTTS(text=text, lang=language, slow=self._slow)

            # Save to temporary buffer
            import io

            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            return audio_buffer.read()

        except Exception as e:
            raise AudioError(f"Audio generation failed: {e}") from e

    def save_audio_file(self, text: str, language: str, output_path: Path) -> Path:
        """Generate and save audio to file.

        Args:
            text: Text to convert to speech
            language: Language code (en, es, de, etc.)
            output_path: Path where audio file should be saved

        Returns:
            Path to saved audio file

        Raises:
            AudioError: If language not supported or save fails
        """
        if language not in self.SUPPORTED_LANGS:
            raise AudioError(
                f"Language '{language}' not supported. Supported: {', '.join(self.SUPPORTED_LANGS)}"
            )

        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate and save
            tts = gTTS(text=text, lang=language, slow=self._slow)
            tts.save(str(output_path))

            return output_path

        except Exception as e:
            raise AudioError(f"Audio save failed: {e}") from e

    def get_supported_languages(self) -> list[str]:
        """Get list of supported language codes.

        Returns:
            List of ISO 639-1 language codes
        """
        return self.SUPPORTED_LANGS.copy()
