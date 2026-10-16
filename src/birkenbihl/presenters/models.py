"""Presentation models for view-agnostic data structures.

These immutable models contain pre-computed, display-ready data:
- Formatted dates/times
- Display indices (1-based for user display)
- Computed fields (title with fallback)
- Structured alignment data
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SentencePresentation:
    """Presentation data for a single sentence.

    Args:
        uuid: Unique identifier of the sentence
        index: Display index (1-based)
        source_text: Original text in source language
        natural_translation: Natural translation in target language
        alignment_count: Number of word alignments
        has_alignments: Whether alignments exist
        alignments: List of (source_word, target_word) tuples
    """

    uuid: UUID
    index: int
    source_text: str
    natural_translation: str
    alignment_count: int
    has_alignments: bool
    alignments: list[tuple[str, str]]


@dataclass(frozen=True)
class TranslationPresentation:
    """Presentation data for a complete translation.

    Contains pre-computed, display-ready data for rendering in any view (CLI, GUI).

    Args:
        uuid: Unique identifier of the translation
        title: Title with fallback (never empty)
        source_language_name: Source language display name
        target_language_name: Target language display name
        sentence_count: Number of sentences in translation
        created_at: Formatted creation timestamp
        updated_at: Formatted update timestamp
        sentences: List of sentence presentations
    """

    uuid: UUID
    title: str
    source_language_name: str
    target_language_name: str
    sentence_count: int
    created_at: str
    updated_at: str
    sentences: list[SentencePresentation]
