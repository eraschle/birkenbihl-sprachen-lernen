"""Integration tests for AudioService with gTTS provider."""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from birkenbihl.models.translation import Sentence
from birkenbihl.providers.gtts_audio_provider import GTTSAudioProvider
from birkenbihl.services.audio_service import AudioService


@pytest.fixture
def audio_provider():
    """Create gTTS audio provider."""
    return GTTSAudioProvider(slow=False)


@pytest.fixture
def audio_service(audio_provider):
    """Create AudioService with gTTS provider."""
    return AudioService(audio_provider)


@pytest.fixture
def temp_audio_dir():
    """Create temporary directory for audio files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_sentence():
    """Create sample English sentence."""
    return Sentence(
        uuid=uuid4(),
        source_text="Hello world",
        natural_translation="Hallo Welt",
        word_alignments=[],
    )


@pytest.mark.integration
@pytest.mark.slow
class TestAudioServiceIntegration:
    """Test AudioService with real gTTS provider."""

    def test_generate_sentence_audio(self, audio_service, sample_sentence, temp_audio_dir):
        """Test generating audio for single sentence."""
        audio_path = audio_service.generate_sentence_audio(sample_sentence, "en", temp_audio_dir)

        assert audio_path.exists()
        assert audio_path.suffix == ".mp3"
        assert audio_path.name == f"{sample_sentence.uuid}.mp3"

        # Check file has content
        assert audio_path.stat().st_size > 0

    def test_batch_generate_audio(self, audio_service, temp_audio_dir):
        """Test generating audio for multiple sentences."""
        sentences = [
            Sentence(uuid=uuid4(), source_text="Good morning", natural_translation="", word_alignments=[]),
            Sentence(uuid=uuid4(), source_text="Good evening", natural_translation="", word_alignments=[]),
            Sentence(uuid=uuid4(), source_text="Good night", natural_translation="", word_alignments=[]),
        ]

        audio_paths = audio_service.batch_generate_audio(sentences, "en", temp_audio_dir)

        assert len(audio_paths) == 3
        for path in audio_paths:
            assert path.exists()
            assert path.suffix == ".mp3"
            assert path.stat().st_size > 0

    def test_audio_exists(self, audio_service, sample_sentence, temp_audio_dir):
        """Test audio existence checking."""
        # Before generation
        assert audio_service.audio_exists(sample_sentence.uuid, temp_audio_dir) is False

        # After generation
        audio_service.generate_sentence_audio(sample_sentence, "en", temp_audio_dir)
        assert audio_service.audio_exists(sample_sentence.uuid, temp_audio_dir) is True

    def test_get_audio_path(self, audio_service, sample_sentence, temp_audio_dir):
        """Test getting audio file path."""
        expected_path = temp_audio_dir / f"{sample_sentence.uuid}.mp3"
        actual_path = audio_service.get_audio_path(sample_sentence.uuid, temp_audio_dir)

        assert actual_path == expected_path

    def test_unsupported_language_raises(self, audio_service, sample_sentence, temp_audio_dir):
        """Test that unsupported language raises ValueError."""
        with pytest.raises(ValueError, match="not supported"):
            audio_service.generate_sentence_audio(sample_sentence, "invalid_lang", temp_audio_dir)

    def test_supported_languages(self, audio_service):
        """Test getting supported languages list."""
        languages = audio_service.get_supported_languages()

        assert isinstance(languages, list)
        assert "en" in languages
        assert "es" in languages
        assert "de" in languages
        assert len(languages) > 0


@pytest.mark.integration
@pytest.mark.slow
class TestGTTSAudioProvider:
    """Test gTTS provider directly."""

    def test_generate_audio_bytes(self, audio_provider):
        """Test generating audio as bytes."""
        audio_data = audio_provider.generate_audio("Hello world", "en")

        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0

    def test_save_audio_file(self, audio_provider, temp_audio_dir):
        """Test saving audio to file."""
        output_path = temp_audio_dir / "test.mp3"

        result_path = audio_provider.save_audio_file("Hello world", "en", output_path)

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_creates_parent_directory(self, audio_provider, temp_audio_dir):
        """Test that parent directories are created."""
        output_path = temp_audio_dir / "nested" / "dir" / "test.mp3"

        audio_provider.save_audio_file("Test", "en", output_path)

        assert output_path.exists()

    def test_spanish_audio(self, audio_provider, temp_audio_dir):
        """Test generating Spanish audio."""
        output_path = temp_audio_dir / "spanish.mp3"

        audio_provider.save_audio_file("Hola mundo", "es", output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_german_audio(self, audio_provider, temp_audio_dir):
        """Test generating German audio."""
        output_path = temp_audio_dir / "german.mp3"

        audio_provider.save_audio_file("Guten Tag", "de", output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_slow_mode(self, temp_audio_dir):
        """Test slow speech mode."""
        slow_provider = GTTSAudioProvider(slow=True)
        fast_provider = GTTSAudioProvider(slow=False)

        slow_path = temp_audio_dir / "slow.mp3"
        fast_path = temp_audio_dir / "fast.mp3"

        text = "This is a test"

        slow_provider.save_audio_file(text, "en", slow_path)
        fast_provider.save_audio_file(text, "en", fast_path)

        # Slow audio should be larger
        assert slow_path.stat().st_size > fast_path.stat().st_size

    def test_unsupported_language(self, audio_provider):
        """Test error handling for unsupported language."""
        with pytest.raises(ValueError, match="not supported"):
            audio_provider.generate_audio("Test", "xyz")

    def test_get_supported_languages(self, audio_provider):
        """Test getting supported languages."""
        languages = audio_provider.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) >= 12
        assert "en" in languages
        assert "es" in languages
        assert "de" in languages
        assert "fr" in languages


@pytest.mark.integration
@pytest.mark.slow
class TestAudioWorkflow:
    """Test complete audio generation workflow."""

    def test_translation_audio_generation(self, audio_service, temp_audio_dir):
        """Test generating audio for complete translation."""
        # Simulate translation with multiple sentences
        sentences = [
            Sentence(uuid=uuid4(), source_text="I am learning Spanish", natural_translation="", word_alignments=[]),
            Sentence(uuid=uuid4(), source_text="This is very interesting", natural_translation="", word_alignments=[]),
            Sentence(uuid=uuid4(), source_text="Thank you very much", natural_translation="", word_alignments=[]),
        ]

        # Generate all audio files
        audio_paths = audio_service.batch_generate_audio(sentences, "en", temp_audio_dir)

        # Verify all files exist
        assert len(audio_paths) == 3
        for sentence, audio_path in zip(sentences, audio_paths, strict=False):
            assert audio_service.audio_exists(sentence.uuid, temp_audio_dir)
            expected_path = audio_service.get_audio_path(sentence.uuid, temp_audio_dir)
            assert audio_path == expected_path

    def test_regenerate_existing_audio(self, audio_service, sample_sentence, temp_audio_dir):
        """Test that regenerating overwrites existing file."""
        # Generate initial audio
        path1 = audio_service.generate_sentence_audio(sample_sentence, "en", temp_audio_dir)
        size1 = path1.stat().st_size

        # Regenerate with different text
        sample_sentence.source_text = "A much longer sentence that will produce a larger audio file"
        path2 = audio_service.generate_sentence_audio(sample_sentence, "en", temp_audio_dir)
        size2 = path2.stat().st_size

        assert path1 == path2  # Same path
        assert size2 > size1  # Different size (longer text)
