"""UI state models for MVVM pattern."""

from dataclasses import dataclass, field

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig


@dataclass
class SettingsViewState:
    """State for settings view."""

    providers: list[ProviderConfig] = field(default_factory=list)
    selected_provider_index: int = -1
    target_language: Language | None = None
    is_editing: bool = False
    has_unsaved_changes: bool = False
