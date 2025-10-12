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


class ProviderConfigDAO(SQLModel, table=True):
    """Database representation of provider configuration."""

    __tablename__ = "provider_configs"  # type: ignore[reportAssignmentType]
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    settings_id: int = Field(foreign_key="settings.id", index=True)
    name: str
    provider_type: str
    model: str
    api_key: str
    base_url: str | None = None
    is_default: bool = False
    supports_streaming: bool = True

    settings: "SettingsDAO" = Relationship(back_populates="providers")


class SettingsDAO(SQLModel, table=True):
    """Database representation of application settings."""

    __tablename__ = "settings"  # type: ignore[reportAssignmentType]
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    target_language: str = "de"
    created_at: datetime = Field(default_factory=dateutils.create_now)
    updated_at: datetime = Field(default_factory=dateutils.create_now)

    providers: list[ProviderConfigDAO] = Relationship(
        back_populates="settings", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


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
