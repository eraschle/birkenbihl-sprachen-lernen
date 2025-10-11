"""Context objects for passing data to components (Parameter Object pattern).

These immutable context objects replace multiple function parameters,
improving code readability and maintainability.
"""

from dataclasses import dataclass

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.services.translation_service import TranslationService


@dataclass(frozen=True)
class SentenceEditorContext:
    """Context for sentence editor component.

    Encapsulates all data needed to edit a sentence, reducing function parameters
    from 5 to 1 (Parameter Object pattern).
    """

    translation: Translation
    sentence: Sentence
    sentence_index: int
    service: TranslationService
    is_new_translation: bool


@dataclass(frozen=True)
class ProviderSelectorContext:
    """Context for provider selector component.

    Encapsulates provider selection configuration.
    """

    providers: list[ProviderConfig]
    default_provider: ProviderConfig | None
    disabled: bool = False
    key_suffix: str = ""


@dataclass(frozen=True)
class AlignmentContext:
    """Context for alignment preview/editor.

    Reduces parameters from 4 to 1 for alignment editing operations.
    """

    sentence: Sentence
    translation: Translation
    service: TranslationService
    is_new_translation: bool
