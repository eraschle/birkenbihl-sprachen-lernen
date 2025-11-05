"""Request parameter objects for reducing function argument counts.

Following Clean Code principle: Functions should have ≤2 parameters.
Parameter objects group related data and provide meaningful names.
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, WordAlignment


@dataclass(frozen=True)
class TranslationRequest:
    """Request for translating text using Birkenbihl method.

    Groups translation parameters to reduce function argument count
    from 4-5 to 1.
    """

    text: str
    source_lang: Language
    target_lang: Language
    title: str | None = None
    provider: ProviderConfig | None = None


@dataclass(frozen=True)
class SentenceUpdateRequest:
    """Request for updating a sentence's natural translation or alignment.

    Groups sentence update parameters to reduce function argument count
    from 3-4 to 1.
    """

    translation_id: UUID
    sentence_uuid: UUID
    new_natural: str | None = None
    alignments: list[WordAlignment] | None = None
    provider: ProviderConfig | None = None


@dataclass(frozen=True)
class AlternativesRequest:
    """Request for generating alternative translations.

    Groups alternative generation parameters to reduce function argument
    count from 4 to 1.
    """

    source_text: str
    source_lang: Language
    target_lang: Language
    count: int = 3


@dataclass(frozen=True)
class AlignmentRegenerationRequest:
    """Request for regenerating word-by-word alignment.

    Groups alignment regeneration parameters to reduce function argument
    count from 4 to 1.
    """

    source_text: str
    natural_translation: str
    source_lang: Language
    target_lang: Language


@dataclass(frozen=True)
class AudioGenerationRequest:
    """Request for generating audio from text/sentences.

    Groups audio generation parameters to reduce function argument count
    from 3 to 1.
    """

    text: str | None = None
    sentence: Sentence | None = None
    sentences: list[Sentence] | None = None
    language: str | None = None
    output_dir: Path | None = None
    output_path: Path | None = None
