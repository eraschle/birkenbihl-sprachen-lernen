"""Database models (DAOs) for SQLModel persistence layer."""

import warnings
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import SAWarning
from sqlmodel import Field, Relationship, SQLModel

from birkenbihl.models import dateutils

# Suppress SQLAlchemy warnings about re-defining tables
# This is expected behavior with Streamlit reruns
warnings.filterwarnings("ignore", category=SAWarning, message=".*already contains a class.*")


class WordAlignmentDAO(SQLModel, table=True):
    """Database representation of word alignment."""

    __tablename__ = "word_alignments"  # type: ignore[reportAssignmentType]
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    sentence_id: UUID = Field(foreign_key="sentences.id", index=True)
    source_word: str
    target_word: str
    position: int

    sentence: "SentenceDAO" = Relationship(back_populates="word_alignments")


class SentenceDAO(SQLModel, table=True):
    """Database representation of a sentence."""

    __tablename__ = "sentences"  # type: ignore[reportAssignmentType]
    __table_args__ = {"extend_existing": True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    translation_id: UUID = Field(foreign_key="translations.id", index=True)
    source_text: str
    natural_translation: str
    created_at: datetime = Field(default_factory=dateutils.create_now)

    translation: "TranslationDAO" = Relationship(back_populates="sentences")
    word_alignments: list[WordAlignmentDAO] = Relationship(
        back_populates="sentence", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class TranslationDAO(SQLModel, table=True):
    """Database representation of a translation document."""

    __tablename__ = "translations"  # type: ignore[reportAssignmentType]
    __table_args__ = {"extend_existing": True}

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    source_language: str
    target_language: str
    created_at: datetime = Field(default_factory=dateutils.create_now)
    updated_at: datetime = Field(default_factory=dateutils.create_now)

    sentences: list[SentenceDAO] = Relationship(
        back_populates="translation", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
