"""Domain models for translation data."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WordAlignment(BaseModel):
    """Word-by-word alignment between source and target language.

    Represents the mapping of a single word from source to target language,
    used for the Birkenbihl method's word-by-word translation (Dekodierung).
    """

    source_word: str
    target_word: str
    position: int  # Position in sentence for correct ordering in UI


class Sentence(BaseModel):
    """A single sentence with natural and word-by-word translation.

    Contains both translation types required by the Birkenbihl method:
    1. Natural translation (natürliche Übersetzung)
    2. Word-by-word alignment (Wort-für-Wort Dekodierung)
    """

    id: UUID = Field(default_factory=uuid4)
    source_text: str
    natural_translation: str
    word_alignments: list[WordAlignment]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Translation(BaseModel):
    """Complete translation document with metadata.

    Root aggregate representing a translation session. Can contain multiple
    sentences, each with natural and word-by-word translations.

    Uses UUIDs for cross-storage compatibility (JSON, DB, Excel, etc.).
    """

    id: UUID = Field(default_factory=uuid4)
    title: str | None = None  # Optional document name for organization
    source_language: str  # ISO 639-1 code: en, es, etc.
    target_language: str  # ISO 639-1 code: de
    sentences: list[Sentence]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
