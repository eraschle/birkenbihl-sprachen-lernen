"""Domain models for translation data."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from birkenbihl.models import dateutils
from birkenbihl.models.languages import Language


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

    uuid: UUID = Field(default_factory=uuid4)
    source_text: str
    natural_translation: str
    word_alignments: list[WordAlignment]

    created_at: datetime = Field(default_factory=dateutils.create_now)


class Translation(BaseModel):
    """Complete translation document with metadata.

    Root aggregate representing a translation session. Can contain multiple
    sentences, each with natural and word-by-word translations.

    Uses UUIDs for cross-storage compatibility (JSON, DB, Excel, etc.).
    """

    uuid: UUID = Field(default_factory=uuid4)
    title: str  # Document name for organization
    source_language: Language
    target_language: Language
    sentences: list[Sentence]

    created_at: datetime = Field(default_factory=dateutils.create_now)
    updated_at: datetime = Field(default_factory=dateutils.create_now)

    def updated_str(self, format_str: str = "%d.%m.%Y %H:%M") -> str:
        return self.updated_at.strftime(format=format_str)

    def created_str(self, format_str: str = "%d.%m.%Y %H:%M") -> str:
        return self.created_at.strftime(format=format_str)
