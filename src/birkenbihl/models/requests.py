"""Request models for the Birkenbihl application.

This module defines parameter objects that encapsulate multiple parameters
into single objects, improving API clarity and reducing parameter count.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig

if TYPE_CHECKING:
    from birkenbihl.models.translation import WordAlignment


@dataclass
class TranslationRequest:
    """Request for translating text using Birkenbihl method.

    Args:
        text: Text to translate
        source_lang: Source language
        target_lang: Target language
        title: Optional title for the translation (empty string if not provided)
    """

    text: str
    source_lang: Language
    target_lang: Language
    title: str = ""


@dataclass
class SentenceUpdateRequest:
    """Request for updating sentence translation.

    Args:
        translation_id: UUID of the translation
        sentence_idx: Index of sentence to update (0-based)
        new_text: New natural translation text
        provider: Provider config for regenerating alignments
    """

    translation_id: UUID
    sentence_idx: int
    new_text: str
    provider: ProviderConfig


@dataclass
class AutoDetectRequest:
    """Request for auto-detecting language and translating.

    Args:
        text: Text to translate
        target_lang: Target language
        title: Optional title for the translation (empty string if not provided)
    """

    text: str
    target_lang: Language
    title: str = ""


@dataclass
class SuggestionRequest:
    """Request for getting alternative translation suggestions.

    Args:
        translation_id: UUID of the translation
        sentence_uuid: UUID of the sentence
        provider: Provider config for generating suggestions
        count: Number of suggestions to generate (default: 3)
    """

    translation_id: UUID
    sentence_uuid: UUID
    provider: ProviderConfig
    count: int = 3


@dataclass
class AlignmentUpdateRequest:
    """Request for updating sentence word alignment.

    Args:
        translation_id: UUID of the translation
        sentence_uuid: UUID of the sentence
        alignments: New word-by-word alignments
    """

    translation_id: UUID
    sentence_uuid: UUID
    alignments: list["WordAlignment"]
