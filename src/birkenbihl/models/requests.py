"""Request models for the Birkenbihl application.

This module defines parameter objects that encapsulate multiple parameters
into single objects, improving API clarity and reducing parameter count.
"""

from dataclasses import dataclass
from uuid import UUID

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig


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
