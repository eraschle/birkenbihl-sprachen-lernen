"""Comprehensive tests for EdgeTTSAudioService."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from pydub import AudioSegment

from birkenbihl.models.audio import AudioData, AudioFormat, AudioQuality
from birkenbihl.protocols.audio import (
    AudioConversionError,
    AudioMixingError,
    AudioPlaybackError,
    TTSError,
    UnsupportedFormatError,
    UnsupportedLanguageError,
)
from birkenbihl.services.audio_service import EdgeTTSAudioService


# ===== Test Fixtures =====

@pytest.fixture
def audio_service():
    """Create EdgeTTSAudioService instance for testing."""
    return EdgeTTSAudioService()


@pytest.fixture
def sample_audio_data():
    """Create sample AudioData for testing."""
    return AudioData(
        id=uuid4(),
        file_path="/tmp/test_audio.wav",
        file_name="test_audio.wav",
        file_size=1024000,
        file_format=AudioFormat.WAV,
        duration=30.5,
        sample_rate=44100,
        bit_rate=128,
        channels=2,
        quality=AudioQuality.MEDIUM,
        language_id=uuid4(),
        is_generated=True,
        tts_engine="edge-tts",
        voice_name="de-DE-KatjaNeural",
        speech_rate=1.0,
    )


@pytest.fixture
def mock_temp_file(tmp_path):
    """Create a mock temporary audio file."""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_bytes(b"fake audio data for testing")
    return audio_file


@pytest.fixture
def mock_audio_segment():
    """Create a mock AudioSegment."""
    segment = Mock(spec=AudioSegment)
    segment.frame_rate = 44100
    segment.channels = 2
    segment.__len__.return_value = 30500  # 30.5 seconds in milliseconds
    segment.export = Mock()
    segment.overlay = Mock(return_value=segment)
    return segment


# ===== Test EdgeTTSAudioService.generate_speech() =====

class TestGenerateSpeech:
    """Test the generate_speech() method."""

    @pytest.mark.asyncio
    async def test_generate_speech_success(self, audio_service, mock_temp_file):
        """Test successful speech generation."""
        mock_voices = ["de-DE-KatjaNeural", "de-DE-ConradNeural"]
        mock_communicate = Mock()
        mock_communicate.save = AsyncMock()
        
        with patch("edge_tts.list_voices", return_value=[
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
            {"Name": "de-DE-ConradNeural", "Locale": "de-DE"},
        ]), \
        patch("edge_tts.Communicate", return_value=mock_communicate), \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat, \
        patch("pydub.AudioSegment.from_file") as mock_from_file:
            
            # Setup mocks
            mock_stat.return_value.st_size = 1024000
            mock_audio_segment = Mock()
            mock_audio_segment.frame_rate = 44100
            mock_audio_segment.channels = 2
            mock_audio_segment.__len__.return_value = 30500  # milliseconds
            mock_from_file.return_value = mock_audio_segment
            
            # Test
            result = await audio_service.generate_speech(
                text="Hallo Welt",
                language_code="de",
                voice_name="de-DE-KatjaNeural",
                speech_rate=1.0,
                quality=AudioQuality.HIGH
            )
            
            # Assertions
            assert isinstance(result, AudioData)
            assert result.file_name == mock_temp_file.name
            assert result.duration == 30.5  # 30500ms converted to seconds
            assert result.sample_rate == 44100
            assert result.channels == 2
            assert result.quality == AudioQuality.HIGH
            assert result.is_generated is True
            assert result.tts_engine == "edge-tts"
            assert result.voice_name == "de-DE-KatjaNeural"
            assert result.speech_rate == 1.0
            
            # Verify edge-tts calls
            mock_communicate.save.assert_called_once_with(str(mock_temp_file))

    @pytest.mark.asyncio
    async def test_generate_speech_default_voice(self, audio_service, mock_temp_file):
        """Test speech generation with default voice selection."""
        mock_communicate = Mock()
        mock_communicate.save = AsyncMock()
        
        with patch("edge_tts.list_voices", return_value=[
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
        ]), \
        patch("edge_tts.Communicate", return_value=mock_communicate), \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat, \
        patch("pydub.AudioSegment.from_file") as mock_from_file:
            
            mock_stat.return_value.st_size = 1024000
            mock_audio_segment = Mock()
            mock_audio_segment.frame_rate = 44100
            mock_audio_segment.channels = 2
            mock_audio_segment.__len__.return_value = 15000
            mock_from_file.return_value = mock_audio_segment
            
            result = await audio_service.generate_speech(
                text="Test",
                language_code="de",
                # voice_name not provided - should use first available
            )
            
            assert result.voice_name == "de-DE-KatjaNeural"

    @pytest.mark.asyncio
    async def test_generate_speech_invalid_speech_rate(self, audio_service):
        """Test speech generation with invalid speech rate."""
        with pytest.raises(TTSError, match="Invalid speech rate"):
            await audio_service.generate_speech(
                text="Test",
                language_code="de",
                speech_rate=5.0  # Invalid: > 3.0
            )

    @pytest.mark.asyncio  
    async def test_generate_speech_unsupported_language(self, audio_service):
        """Test speech generation with unsupported language."""
        with patch("edge_tts.list_voices", return_value=[]):
            with pytest.raises(UnsupportedLanguageError, match="Language 'xx' not supported"):
                await audio_service.generate_speech(
                    text="Test",
                    language_code="xx",  # Unsupported language
                )

    @pytest.mark.asyncio
    async def test_generate_speech_tts_failure(self, audio_service):
        """Test speech generation when TTS fails."""
        with patch("edge_tts.list_voices", return_value=[
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
        ]), \
        patch("edge_tts.Communicate") as mock_communicate_cls:
            
            mock_communicate = Mock()
            mock_communicate.save = AsyncMock(side_effect=Exception("TTS failed"))
            mock_communicate_cls.return_value = mock_communicate
            
            with pytest.raises(TTSError, match="Failed to generate speech"):
                await audio_service.generate_speech(
                    text="Test",
                    language_code="de",
                )

    @pytest.mark.parametrize("speech_rate,expected_format", [
        (0.5, "-50%"),
        (1.0, "+0%"),
        (1.5, "+50%"),
        (2.0, "+100%"),
    ])
    @pytest.mark.asyncio
    async def test_generate_speech_rate_formatting(
        self, audio_service, mock_temp_file, speech_rate, expected_format
    ):
        """Test speech rate formatting for edge-tts."""
        mock_communicate = Mock()
        mock_communicate.save = AsyncMock()
        
        with patch("edge_tts.list_voices", return_value=[
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
        ]), \
        patch("edge_tts.Communicate", return_value=mock_communicate) as mock_communicate_cls, \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat, \
        patch("pydub.AudioSegment.from_file") as mock_from_file:
            
            mock_stat.return_value.st_size = 1024000
            mock_from_file.return_value = Mock(
                frame_rate=44100, channels=2, __len__=Mock(return_value=15000)
            )
            
            await audio_service.generate_speech(
                text="Test",
                language_code="de",
                speech_rate=speech_rate
            )
            
            # Verify rate formatting
            mock_communicate_cls.assert_called_once()
            args, kwargs = mock_communicate_cls.call_args
            assert args[2] == expected_format  # rate parameter


# ===== Test EdgeTTSAudioService.play_audio() =====

class TestPlayAudio:
    """Test the play_audio() methods."""

    def test_play_audio_success(self, audio_service, sample_audio_data, mock_temp_file):
        """Test successful audio playback."""
        sample_audio_data.file_path = str(mock_temp_file)
        
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("pydub.playback.play") as mock_play:
            
            mock_segment = Mock()
            mock_from_file.return_value = mock_segment
            
            audio_service.play_audio(sample_audio_data)
            
            mock_from_file.assert_called_once_with(mock_temp_file)
            mock_play.assert_called_once_with(mock_segment)

    def test_play_audio_file_not_found(self, audio_service, sample_audio_data):
        """Test audio playback with non-existent file."""
        sample_audio_data.file_path = "/nonexistent/file.wav"
        
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            audio_service.play_audio(sample_audio_data)

    def test_play_audio_file_directly_success(self, audio_service, mock_temp_file):
        """Test direct file playback."""
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("pydub.playback.play") as mock_play:
            
            mock_segment = Mock()
            mock_from_file.return_value = mock_segment
            
            audio_service.play_audio_file(mock_temp_file)
            
            mock_from_file.assert_called_once_with(mock_temp_file)
            mock_play.assert_called_once_with(mock_segment)

    def test_play_audio_file_playback_error(self, audio_service, mock_temp_file):
        """Test audio playback failure."""
        with patch("pydub.AudioSegment.from_file", side_effect=Exception("Playback failed")):
            with pytest.raises(AudioPlaybackError, match="Failed to play audio"):
                audio_service.play_audio_file(mock_temp_file)

    def test_stop_playback(self, audio_service):
        """Test stopping audio playback."""
        # Set up a mock current playback
        mock_playback = Mock()
        audio_service._current_playback = mock_playback
        
        audio_service.stop_playback()
        
        mock_playback.terminate.assert_called_once()
        assert audio_service._current_playback is None

    def test_stop_playback_with_error(self, audio_service):
        """Test stopping playback when terminate fails."""
        mock_playback = Mock()
        mock_playback.terminate.side_effect = Exception("Termination failed")
        audio_service._current_playback = mock_playback
        
        # Should not raise exception
        audio_service.stop_playback()
        assert audio_service._current_playback is None

    def test_stop_playback_no_current(self, audio_service):
        """Test stopping playback when nothing is playing."""
        audio_service._current_playback = None
        
        # Should not raise exception
        audio_service.stop_playback()
        assert audio_service._current_playback is None


# ===== Test EdgeTTSAudioService.convert_audio_format() =====

class TestConvertAudioFormat:
    """Test the convert_audio_format() method."""

    def test_convert_audio_format_success(self, audio_service, sample_audio_data, mock_temp_file):
        """Test successful audio format conversion."""
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat:
            
            # Setup mocks
            mock_segment = Mock()
            mock_segment.frame_rate = 44100
            mock_segment.channels = 2
            mock_segment.__len__.return_value = 30500
            mock_segment.export = Mock()
            mock_from_file.return_value = mock_segment
            mock_stat.return_value.st_size = 2048000
            
            result = audio_service.convert_audio_format(
                sample_audio_data,
                AudioFormat.MP3,
                AudioQuality.HIGH
            )
            
            assert isinstance(result, AudioData)
            assert result.file_format == AudioFormat.MP3
            assert result.quality == AudioQuality.HIGH
            assert result.duration == 30.5
            assert result.file_name.endswith(".mp3")
            
            # Verify export was called with quality params
            mock_segment.export.assert_called_once()
            args, kwargs = mock_segment.export.call_args
            assert args[0] == str(mock_temp_file)
            assert kwargs["format"] == "mp3"
            assert "bitrate" in kwargs

    def test_convert_audio_format_unsupported(self, audio_service, sample_audio_data):
        """Test conversion to unsupported format."""
        # M4A is not in the supported formats list
        with pytest.raises(UnsupportedFormatError, match="Format 'm4a' not supported"):
            audio_service.convert_audio_format(
                sample_audio_data,
                AudioFormat.M4A
            )

    def test_convert_audio_format_conversion_error(self, audio_service, sample_audio_data):
        """Test conversion failure."""
        with patch("pydub.AudioSegment.from_file", side_effect=Exception("Conversion failed")):
            with pytest.raises(AudioConversionError, match="Failed to convert audio"):
                audio_service.convert_audio_format(
                    sample_audio_data,
                    AudioFormat.MP3
                )

    @pytest.mark.parametrize("quality,expected_bitrate", [
        (AudioQuality.LOW, "64k"),
        (AudioQuality.MEDIUM, "128k"),
        (AudioQuality.HIGH, "192k"),
        (AudioQuality.LOSSLESS, "320k"),
    ])
    def test_convert_quality_params(self, audio_service, sample_audio_data, mock_temp_file, quality, expected_bitrate):
        """Test quality parameter mapping."""
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat:
            
            mock_segment = Mock()
            mock_segment.frame_rate = 44100
            mock_segment.channels = 2
            mock_segment.__len__.return_value = 30500
            mock_from_file.return_value = mock_segment
            mock_stat.return_value.st_size = 1024000
            
            audio_service.convert_audio_format(
                sample_audio_data,
                AudioFormat.MP3,
                quality
            )
            
            # Verify quality parameters
            mock_segment.export.assert_called_once()
            args, kwargs = mock_segment.export.call_args
            assert kwargs["bitrate"] == expected_bitrate


# ===== Test EdgeTTSAudioService.create_background_audio() =====

class TestCreateBackgroundAudio:
    """Test the create_background_audio() method."""

    def test_create_background_audio_without_music(self, audio_service, sample_audio_data, mock_temp_file):
        """Test creating background audio without background music."""
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat:
            
            mock_segment = Mock()
            mock_segment.frame_rate = 44100
            mock_segment.channels = 2
            mock_segment.__len__.return_value = 30500
            mock_segment.export = Mock()
            mock_from_file.return_value = mock_segment
            mock_stat.return_value.st_size = 1024000
            
            result = audio_service.create_background_audio(sample_audio_data)
            
            assert isinstance(result, AudioData)
            assert result.is_background_music is True
            assert result.quality == sample_audio_data.quality
            assert result.tts_engine == sample_audio_data.tts_engine
            assert result.voice_name == sample_audio_data.voice_name
            
            mock_segment.export.assert_called_once_with(str(mock_temp_file), format="wav")

    def test_create_background_audio_with_music(self, audio_service, sample_audio_data, mock_temp_file, tmp_path):
        """Test creating background audio with background music."""
        bg_music_file = tmp_path / "background.mp3"
        bg_music_file.write_bytes(b"fake background music")
        
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat:
            
            # Primary audio segment
            primary_segment = Mock()
            primary_segment.frame_rate = 44100
            primary_segment.channels = 2
            primary_segment.__len__.return_value = 30500
            primary_segment.export = Mock()
            
            # Background music segment
            bg_segment = Mock()
            bg_segment.__len__.return_value = 15000  # Shorter than primary
            bg_segment.__sub__ = Mock(return_value=bg_segment)  # Volume adjustment
            bg_segment.__mul__ = Mock(return_value=bg_segment)  # Looping
            bg_segment.__getitem__ = Mock(return_value=bg_segment)  # Trimming
            
            # Mixed segment
            mixed_segment = Mock()
            mixed_segment.frame_rate = 44100
            mixed_segment.channels = 2
            mixed_segment.__len__.return_value = 30500
            mixed_segment.export = Mock()
            primary_segment.overlay = Mock(return_value=mixed_segment)
            
            # Configure mock to return different segments based on file
            def from_file_side_effect(path):
                if str(path) == sample_audio_data.file_path:
                    return primary_segment
                elif str(path) == str(bg_music_file):
                    return bg_segment
                else:
                    return Mock()
            
            mock_from_file.side_effect = from_file_side_effect
            mock_stat.return_value.st_size = 1024000
            
            result = audio_service.create_background_audio(
                sample_audio_data, 
                bg_music_file, 
                volume_ratio=0.4
            )
            
            assert isinstance(result, AudioData)
            assert result.is_background_music is True
            
            # Verify background music processing
            primary_segment.overlay.assert_called_once_with(bg_segment)

    def test_create_background_audio_mixing_error(self, audio_service, sample_audio_data):
        """Test background audio creation failure."""
        with patch("pydub.AudioSegment.from_file", side_effect=Exception("Mixing failed")):
            with pytest.raises(AudioMixingError, match="Failed to create background audio"):
                audio_service.create_background_audio(sample_audio_data)


# ===== Test EdgeTTSAudioService.get_available_voices() =====

class TestGetAvailableVoices:
    """Test the get_available_voices() method."""

    @pytest.mark.asyncio
    async def test_get_available_voices_all(self, audio_service):
        """Test getting all available voices."""
        mock_voices = [
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
            {"Name": "de-DE-ConradNeural", "Locale": "de-DE"},
            {"Name": "en-US-JennyNeural", "Locale": "en-US"},
            {"Name": "es-ES-ElviraNeural", "Locale": "es-ES"},
        ]
        
        with patch("edge_tts.list_voices", return_value=mock_voices):
            voices = await audio_service.get_available_voices()
            
            expected = ["de-DE-KatjaNeural", "de-DE-ConradNeural", "en-US-JennyNeural", "es-ES-ElviraNeural"]
            assert voices == expected

    @pytest.mark.asyncio
    async def test_get_available_voices_filtered(self, audio_service):
        """Test getting voices filtered by language."""
        mock_voices = [
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
            {"Name": "de-DE-ConradNeural", "Locale": "de-DE"}, 
            {"Name": "en-US-JennyNeural", "Locale": "en-US"},
            {"Name": "es-ES-ElviraNeural", "Locale": "es-ES"},
        ]
        
        with patch("edge_tts.list_voices", return_value=mock_voices):
            voices = await audio_service.get_available_voices("de")
            
            expected = ["de-DE-KatjaNeural", "de-DE-ConradNeural"]
            assert voices == expected

    @pytest.mark.asyncio
    async def test_get_available_voices_error(self, audio_service):
        """Test get available voices with API error."""
        with patch("edge_tts.list_voices", side_effect=Exception("API error")):
            voices = await audio_service.get_available_voices()
            
            assert voices == []


# ===== Test EdgeTTSAudioService utility methods =====

class TestUtilityMethods:
    """Test utility methods."""

    @pytest.mark.parametrize("rate,expected", [
        (0.1, True),
        (1.0, True),
        (3.0, True),
        (0.05, False),
        (3.5, False),
        (-1.0, False),
    ])
    def test_validate_speech_rate(self, audio_service, rate, expected):
        """Test speech rate validation."""
        assert audio_service.validate_speech_rate(rate) == expected

    @pytest.mark.parametrize("format_type,expected", [
        (AudioFormat.MP3, True),
        (AudioFormat.WAV, True),
        (AudioFormat.OGG, True),
        (AudioFormat.FLAC, True),
        (AudioFormat.M4A, False),
    ])
    def test_is_format_supported(self, audio_service, format_type, expected):
        """Test format support checking."""
        assert audio_service.is_format_supported(format_type) == expected

    def test_get_audio_info_success(self, audio_service, mock_temp_file):
        """Test getting audio file information."""
        with patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("pathlib.Path.stat") as mock_stat:
            
            mock_segment = Mock()
            mock_segment.frame_rate = 44100
            mock_segment.channels = 2
            mock_segment.__len__.return_value = 30500
            mock_from_file.return_value = mock_segment
            mock_stat.return_value.st_size = 1024000
            
            result = audio_service.get_audio_info(mock_temp_file)
            
            assert isinstance(result, AudioData)
            assert result.file_path == str(mock_temp_file)
            assert result.file_name == mock_temp_file.name
            assert result.duration == 30.5
            assert result.sample_rate == 44100
            assert result.channels == 2

    def test_get_audio_info_file_not_found(self, audio_service):
        """Test getting info for non-existent file."""
        non_existent = Path("/nonexistent/file.wav")
        
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            audio_service.get_audio_info(non_existent)

    def test_get_audio_info_unsupported_format(self, audio_service, mock_temp_file):
        """Test getting info for unsupported format."""
        with patch("pydub.AudioSegment.from_file", side_effect=Exception("Unsupported format")):
            with pytest.raises(UnsupportedFormatError, match="Failed to read audio file"):
                audio_service.get_audio_info(mock_temp_file)

    def test_cleanup_temp_files(self, audio_service, tmp_path):
        """Test cleaning up temporary files."""
        # Create some temp files
        temp_files = [
            tmp_path / "temp1.wav",
            tmp_path / "temp2.mp3",
            tmp_path / "temp3.ogg"
        ]
        
        for temp_file in temp_files:
            temp_file.write_bytes(b"test data")
            audio_service._temp_files.append(temp_file)
        
        # Verify files exist
        for temp_file in temp_files:
            assert temp_file.exists()
        
        # Clean up
        audio_service.cleanup_temp_files()
        
        # Verify cleanup
        for temp_file in temp_files:
            assert not temp_file.exists()
        assert audio_service._temp_files == []

    def test_cleanup_temp_files_with_errors(self, audio_service):
        """Test cleanup with file deletion errors."""
        # Add non-existent file to temp files list
        non_existent = Path("/nonexistent/file.wav")
        audio_service._temp_files.append(non_existent)
        
        # Should not raise exception
        audio_service.cleanup_temp_files()
        assert audio_service._temp_files == []

    def test_destructor_calls_cleanup(self, audio_service, tmp_path):
        """Test that __del__ calls cleanup_temp_files."""
        temp_file = tmp_path / "temp.wav"
        temp_file.write_bytes(b"test")
        audio_service._temp_files.append(temp_file)
        
        with patch.object(audio_service, 'cleanup_temp_files') as mock_cleanup:
            audio_service.__del__()
            mock_cleanup.assert_called_once()


# ===== Test private methods =====

class TestPrivateMethods:
    """Test private utility methods."""

    @pytest.mark.parametrize("rate,expected", [
        (0.5, "-50%"),
        (1.0, "+0%"),
        (1.5, "+50%"),
        (2.0, "+100%"),
        (0.75, "-25%"),
        (1.25, "+25%"),
    ])
    def test_format_rate(self, audio_service, rate, expected):
        """Test speech rate formatting for edge-tts."""
        assert audio_service._format_rate(rate) == expected

    @pytest.mark.parametrize("quality,expected_bitrate", [
        (AudioQuality.LOW, "64k"),
        (AudioQuality.MEDIUM, "128k"),
        (AudioQuality.HIGH, "192k"),
        (AudioQuality.LOSSLESS, "320k"),
    ])
    def test_get_quality_params(self, audio_service, quality, expected_bitrate):
        """Test quality parameter mapping."""
        params = audio_service._get_quality_params(quality)
        assert params["bitrate"] == expected_bitrate

    def test_get_quality_params_unknown(self, audio_service):
        """Test quality parameter mapping for unknown quality."""
        # Create a mock quality that's not in the enum
        class UnknownQuality:
            pass
        
        unknown_quality = UnknownQuality()
        params = audio_service._get_quality_params(unknown_quality)
        
        # Should default to MEDIUM quality
        assert params["bitrate"] == "128k"


# ===== Integration Tests =====

class TestIntegration:
    """Integration tests combining multiple methods."""

    @pytest.mark.asyncio
    async def test_generate_and_play_workflow(self, audio_service, mock_temp_file):
        """Test complete generate -> play workflow."""
        mock_communicate = Mock()
        mock_communicate.save = AsyncMock()
        
        with patch("edge_tts.list_voices", return_value=[
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
        ]), \
        patch("edge_tts.Communicate", return_value=mock_communicate), \
        patch("tempfile.mktemp", return_value=str(mock_temp_file)), \
        patch("pathlib.Path.stat") as mock_stat, \
        patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("pydub.playback.play") as mock_play:
            
            # Setup mocks for generation
            mock_stat.return_value.st_size = 1024000
            mock_audio_segment = Mock()
            mock_audio_segment.frame_rate = 44100
            mock_audio_segment.channels = 2
            mock_audio_segment.__len__.return_value = 15000
            mock_from_file.return_value = mock_audio_segment
            
            # Generate speech
            audio_data = await audio_service.generate_speech(
                text="Test audio",
                language_code="de"
            )
            
            # Play generated audio
            audio_service.play_audio(audio_data)
            
            # Verify workflow
            assert isinstance(audio_data, AudioData)
            mock_play.assert_called_once_with(mock_audio_segment)

    @pytest.mark.asyncio
    async def test_generate_convert_play_workflow(self, audio_service, mock_temp_file, tmp_path):
        """Test complete generate -> convert -> play workflow."""
        mock_communicate = Mock()
        mock_communicate.save = AsyncMock()
        converted_file = tmp_path / "converted.mp3"
        
        with patch("edge_tts.list_voices", return_value=[
            {"Name": "de-DE-KatjaNeural", "Locale": "de-DE"},
        ]), \
        patch("edge_tts.Communicate", return_value=mock_communicate), \
        patch("tempfile.mktemp", side_effect=[str(mock_temp_file), str(converted_file)]), \
        patch("pathlib.Path.stat") as mock_stat, \
        patch("pydub.AudioSegment.from_file") as mock_from_file, \
        patch("pydub.playback.play") as mock_play:
            
            # Setup mocks
            mock_stat.return_value.st_size = 1024000
            mock_segment = Mock()
            mock_segment.frame_rate = 44100
            mock_segment.channels = 2
            mock_segment.__len__.return_value = 15000
            mock_segment.export = Mock()
            mock_from_file.return_value = mock_segment
            
            # Generate speech
            original_audio = await audio_service.generate_speech(
                text="Test audio",
                language_code="de"
            )
            
            # Convert format
            converted_audio = audio_service.convert_audio_format(
                original_audio,
                AudioFormat.MP3,
                AudioQuality.HIGH
            )
            
            # Play converted audio
            audio_service.play_audio(converted_audio)
            
            # Verify workflow
            assert original_audio.file_format == AudioFormat.WAV
            assert converted_audio.file_format == AudioFormat.MP3
            assert converted_audio.quality == AudioQuality.HIGH
            mock_play.assert_called_once()

    def test_error_handling_chain(self, audio_service, sample_audio_data):
        """Test error handling across method calls."""
        # First method fails
        with patch("pydub.AudioSegment.from_file", side_effect=Exception("Load failed")):
            with pytest.raises(AudioConversionError):
                audio_service.convert_audio_format(
                    sample_audio_data,
                    AudioFormat.MP3
                )
        
        # Should still be able to use service for other operations
        with patch("edge_tts.list_voices", return_value=[]):
            voices = asyncio.run(audio_service.get_available_voices())
            assert voices == []