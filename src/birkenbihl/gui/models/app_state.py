"""Application state management for translation UI."""

from enum import Enum
from uuid import UUID

from PySide6.QtCore import QObject, Signal

from birkenbihl.models.translation import Translation


class AppMode(str, Enum):
    """Application modes for translation UI."""

    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"


class AppState(QObject):
    """Global application state with change notifications.

    Manages current mode, selected translation, and selected sentence.
    Emits signals when state changes to allow UI components to react.
    """

    mode_changed = Signal(AppMode)
    translation_selected = Signal(object)  # Translation | None
    sentence_selected = Signal(int)  # sentence index

    def __init__(self, parent: QObject | None = None):
        """Initialize application state.

        Args:
            parent: Parent QObject for memory management
        """
        super().__init__(parent)
        self._mode = AppMode.VIEW
        self._selected_translation: Translation | None = None
        self._selected_sentence_index = 0

    @property
    def mode(self) -> AppMode:
        """Current application mode."""
        return self._mode

    def set_mode(self, mode: AppMode) -> None:
        """Set application mode and emit signal.

        Args:
            mode: New application mode
        """
        if self._mode != mode:
            self._mode = mode
            self.mode_changed.emit(mode)

    @property
    def selected_translation(self) -> Translation | None:
        """Currently selected translation."""
        return self._selected_translation

    def select_translation(self, translation: Translation | None) -> None:
        """Select translation and emit signal.

        Args:
            translation: Translation to select (None to deselect)
        """
        self._selected_translation = translation
        self._selected_sentence_index = 0
        self.translation_selected.emit(translation)

    @property
    def selected_sentence_index(self) -> int:
        """Index of currently selected sentence."""
        return self._selected_sentence_index

    def select_sentence(self, index: int) -> None:
        """Select sentence by index and emit signal.

        Args:
            index: Sentence index (0-based)
        """
        if index >= 0:
            self._selected_sentence_index = index
            self.sentence_selected.emit(index)

    @property
    def selected_sentence_id(self) -> UUID | None:
        """UUID of currently selected sentence."""
        if not self._selected_translation:
            return None
        if self._selected_sentence_index >= len(self._selected_translation.sentences):
            return None
        return self._selected_translation.sentences[self._selected_sentence_index].uuid

    def is_edit_enabled(self) -> bool:
        """Check if edit mode can be enabled."""
        return self._mode == AppMode.VIEW and self._selected_translation is not None
