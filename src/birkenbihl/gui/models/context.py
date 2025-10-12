"""Context objects for passing data to components (Parameter Object pattern)."""

from dataclasses import dataclass

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation


@dataclass(frozen=True)
class ProviderSelectorContext:
    """Context for provider selector component."""

    providers: list[ProviderConfig]
    default_provider: ProviderConfig | None
    disabled: bool = False


@dataclass(frozen=True)
class AlignmentContext:
    """Context for alignment preview/editor."""

    sentence: Sentence
    translation: Translation


@dataclass(frozen=True)
class TranslationEditorContext:
    """Context for translation editor view."""

    translation: Translation
    is_new: bool = False
