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
        provider: Provider to translate with; None uses the service's default translator
    """

    text: str
    source_lang: Language
    target_lang: Language
    title: str = ""
    provider: ProviderConfig | None = None


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


@dataclass
class AlignmentRequest:
    """Request for an AI word-by-word alignment of one sentence (preview, not saved).

    Args:
        source_text: Original sentence
        natural_translation: Natural translation the alignment has to use
        source_lang: Source language
        target_lang: Target language
        provider: Provider to generate the alignment with
    """

    source_text: str
    natural_translation: str
    source_lang: Language
    target_lang: Language
    provider: ProviderConfig
