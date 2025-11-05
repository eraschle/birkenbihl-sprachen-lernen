"""Display models for presentation layer.

Separates domain models from display concerns (Separation of Concerns).
"""

from dataclasses import dataclass


@dataclass
class AlignmentDisplayModel:
    """Display model for word alignment."""

    source_word: str
    target_word: str
    position: int


@dataclass
class SentenceDisplayModel:
    """Display model for sentence with formatting."""

    index: int
    source_text: str
    natural_translation: str
    word_by_word: str
    alignments: list[AlignmentDisplayModel]


@dataclass
class TranslationDisplayModel:
    """Display model for translation with formatting."""

    title: str
    short_id: str
    source_language: str
    target_language: str
    language_pair: str
    sentences: list[SentenceDisplayModel]
