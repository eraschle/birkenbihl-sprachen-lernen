"""Audio models for the Birkenbihl Learning App."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class AudioFormat(str, Enum):
    """Supported audio formats."""

    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"
    M4A = "m4a"


class AudioQuality(str, Enum):
    """Audio quality levels."""

    LOW = "low"  # 64-128 kbps
    MEDIUM = "medium"  # 128-192 kbps
    HIGH = "high"  # 192-320 kbps
    LOSSLESS = "lossless"  # FLAC, uncompressed


class AudioData(SQLModel, table=True):
    """Audio data model for storing audio files and metadata."""

    __tablename__ = "audio_data"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # File information
    file_path: str = Field(max_length=500)  # Path to audio file
    file_name: str = Field(max_length=255)
    file_size: int = Field(ge=0)  # Size in bytes
    file_format: AudioFormat

    # Audio properties
    duration: float = Field(ge=0.0)  # Duration in seconds
    sample_rate: int = Field(ge=0)  # Sample rate in Hz (e.g., 44100, 48000)
    bit_rate: int | None = Field(default=None, ge=0)  # Bitrate in kbps
    channels: int = Field(default=2, ge=1, le=8)  # Number of audio channels
    quality: AudioQuality = Field(default=AudioQuality.MEDIUM)

    # Content information
    language_id: UUID | None = Field(default=None, foreign_key="languages.id")
    translation_id: UUID | None = Field(default=None, foreign_key="translations.id")

    # Text-to-Speech information
    is_generated: bool = Field(default=False)  # True if TTS generated
    tts_engine: str | None = Field(default=None, max_length=100)  # TTS engine used
    voice_name: str | None = Field(default=None, max_length=100)  # Voice used for TTS
    speech_rate: float | None = Field(default=None, ge=0.1, le=3.0)  # Speech speed multiplier

    # Birkenbihl method specific
    is_background_music: bool = Field(default=False)  # For passive listening phase
    volume_level: float = Field(default=1.0, ge=0.0, le=1.0)  # Volume level

    # Metadata
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    tags: list[str] | None = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_played_at: datetime | None = Field(default=None)
    play_count: int = Field(default=0, ge=0)

    def __str__(self) -> str:
        return f"AudioData({self.file_name} - {self.duration:.1f}s)"

    @property
    def file_path_obj(self) -> Path:
        """Get file path as Path object."""
        return Path(self.file_path)

    @property
    def exists(self) -> bool:
        """Check if audio file exists on filesystem."""
        return self.file_path_obj.exists()

    def get_duration_formatted(self) -> str:
        """Get duration formatted as MM:SS."""
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_file_size_formatted(self) -> str:
        """Get file size formatted in human-readable format."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
