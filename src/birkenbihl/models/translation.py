"""Translation models for the Birkenbihl Learning App."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Column, Field, SQLModel
from sqlalchemy import JSON


class TranslationResult(SQLModel):
    """Ergebnis einer Textübersetzung."""
    
    natural_translation: str = Field(description="Natürliche Übersetzung")
    word_by_word_translation: str = Field(description="Wort-für-Wort Übersetzung")
    formatted_decoding: str = Field(description="Formatierte Dekodierung mit Alignment")


class TranslationType(str, Enum):
    """Types of translations available."""

    NATURAL = "natural"  # Natürliche Übersetzung
    WORD_FOR_WORD = "word_for_word"  # Wort-für-Wort Dekodierung


class Language(SQLModel, table=True):
    """Language model for supported languages."""

    __tablename__ = "languages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(max_length=10, unique=True, index=True)  # e.g., "en", "de", "fr"
    name: str = Field(max_length=100)  # e.g., "English", "Deutsch", "Français"
    native_name: str = Field(max_length=100)  # e.g., "English", "Deutsch", "Français"
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Translation(SQLModel, table=True):
    """Translation model for storing text translations."""

    __tablename__ = "translations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Source text and language
    source_text: str = Field(max_length=5000)
    source_language_id: UUID = Field(foreign_key="languages.id")

    # Target language and translation
    target_language_id: UUID = Field(foreign_key="languages.id")
    translation_type: TranslationType
    translated_text: str = Field(max_length=5000)

    # Optional word-for-word breakdown for dekodierung
    word_breakdown: dict[str, str] | None = Field(default=None, sa_column=Column(JSON))

    # Metadata
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    ai_provider: str | None = Field(default=None, max_length=50)  # e.g., "openai", "anthropic"
    model_used: str | None = Field(default=None, max_length=100)  # e.g., "gpt-4", "claude-3"

    # Birkenbihl specific fields
    learning_phase: int = Field(default=1, ge=1, le=4)  # Birkenbihl learning phases
    is_reviewed: bool = Field(default=False)
    review_count: int = Field(default=0, ge=0)
    difficulty_rating: int | None = Field(default=None, ge=1, le=5)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_reviewed_at: datetime | None = Field(default=None)

    def __str__(self) -> str:
        return f"Translation({self.source_text[:50]}... -> {self.translated_text[:50]}...)"

    @property
    def is_dekodierung(self) -> bool:
        """Check if this is a word-for-word dekodierung."""
        return self.translation_type == TranslationType.WORD_FOR_WORD

    def get_word_count(self) -> int:
        """Get approximate word count of source text."""
        return len(self.source_text.split())
