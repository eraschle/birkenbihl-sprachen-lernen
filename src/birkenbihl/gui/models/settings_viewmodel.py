"""ViewModel for settings management."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from birkenbihl.gui.models.ui_state import SettingsViewState
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.services import language_service as ls
from birkenbihl.services.settings_service import SettingsService


class SettingsViewModel(QObject):
    """ViewModel for settings management.

    Manages provider configurations and application settings.
    Coordinates SettingsService for persistence.
    """

    state_changed = Signal(object)  # SettingsViewState
    settings_saved = Signal()
    provider_added = Signal()
    provider_deleted = Signal(int)  # index
    error_occurred = Signal(str)  # error message

    def __init__(self, service: SettingsService, parent: QWidget | None = None):
        """Initialize ViewModel.

        Args:
            service: SettingsService instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = service
        self._state = SettingsViewState()

    def initialize(self) -> None:
        """Initialize ViewModel and load settings."""
        self.load_settings()

    def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    @property
    def state(self) -> SettingsViewState:
        """Get current state."""
        return self._state

    def load_settings(self) -> None:
        """Load settings from service."""
        settings = self._service.get_settings()
        try:
            self._state.providers = settings.providers.copy()
            self._state.target_language = ls.get_language_by(settings.target_language)
            self._state.has_unsaved_changes = False
            self._emit_state()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def add_provider(self, provider: ProviderConfig) -> None:
        """Add new provider.

        Args:
            provider: Provider configuration
        """
        error = self._service.validate_provider_config(provider)
        if error:
            self.error_occurred.emit(error)
            return

        # Add to service immediately
        self._service.add_provider(provider)
        # Update state from service to stay in sync
        self._state.providers = self._service.get_settings().providers.copy()
        self._state.has_unsaved_changes = True
        self._emit_state()
        self.provider_added.emit()

    def update_provider(self, index: int, provider: ProviderConfig) -> None:
        """Update existing provider.

        Args:
            index: Provider index
            provider: Updated provider configuration
        """
        if 0 <= index < len(self._state.providers):
            error = self._service.validate_provider_config(provider)
            if error:
                self.error_occurred.emit(error)
                return

            # Update in service immediately
            self._service.update_provider(index, provider)
            # Update state from service to stay in sync
            self._state.providers = self._service.get_settings().providers.copy()
            self._state.has_unsaved_changes = True
            self._emit_state()

    def delete_provider(self, index: int) -> None:
        """Delete provider.

        Args:
            index: Provider index
        """
        if 0 <= index < len(self._state.providers):
            # Delete from service immediately
            self._service.delete_provider(index)
            # Update state from service to stay in sync
            self._state.providers = self._service.get_settings().providers.copy()
            self._state.has_unsaved_changes = True
            self._emit_state()
            self.provider_deleted.emit(index)

    def set_target_language(self, lang: str) -> None:
        """Set target language.

        Args:
            lang: Language code
        """
        # Update in service immediately
        settings = self._service.get_settings()
        settings.target_language = lang
        # Update state
        self._state.target_language = ls.get_language_by(lang)
        self._state.has_unsaved_changes = True
        self._emit_state()

    def set_editing(self, editing: bool) -> None:
        """Set editing state.

        Args:
            editing: Editing flag
        """
        self._state.is_editing = editing
        self._emit_state()

    def select_provider(self, index: int) -> None:
        """Select provider for editing.

        Args:
            index: Provider index
        """
        self._state.selected_provider_index = index
        self._emit_state()

    def save_settings(self) -> None:
        """Save settings to persistence."""
        try:
            # Service already has current settings in its internal state
            # Just need to call save
            self._service.save_settings()
            self._state.has_unsaved_changes = False
            self._emit_state()
            self.settings_saved.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _emit_state(self) -> None:
        """Emit state changed signal."""
        self.state_changed.emit(self._state)
