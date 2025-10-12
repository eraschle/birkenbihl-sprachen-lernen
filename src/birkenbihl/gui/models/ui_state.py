"""UI State objects (Parameter Object pattern)."""

from dataclasses import dataclass, field
from uuid import UUID

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation


@dataclass
class TranslationCreationState:
    """State for translation creation view."""

    title: str = ""
    source_text: str = ""
    source_language: str | None = None  # None = auto-detect
    target_language: str = "de"
    selected_provider: ProviderConfig | None = None
    is_translating: bool = False
    progress: float = 0.0


@dataclass
class TranslationEditorState:
    """State for translation editor view."""

    translation: Translation | None = None
    selected_sentence_uuid: UUID | None = None
    edit_mode: str = "view"  # view, edit_natural, edit_alignment
    is_saving: bool = False
    has_unsaved_changes: bool = False


@dataclass
class SettingsViewState:
    """State for settings view."""

    providers: list[ProviderConfig] = field(default_factory=list)
    selected_provider_index: int = -1
    target_language: str = "de"
    is_editing: bool = False
    has_unsaved_changes: bool = False
