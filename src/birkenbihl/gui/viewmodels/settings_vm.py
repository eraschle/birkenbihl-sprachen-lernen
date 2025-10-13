"""SettingsViewModel for managing application settings in MVVM pattern."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from birkenbihl.gui.viewmodels.base import BaseViewModel
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService


class SettingsViewModel(BaseViewModel):
    """ViewModel for settings management.

    Orchestrates SettingsService operations and emits signals for UI updates.
    Follows MVVM pattern with clean separation of concerns.
    """

    settings_loaded = Signal()
    settings_saved = Signal()
    provider_added = Signal(ProviderConfig)
    provider_updated = Signal(int)
    provider_deleted = Signal(int)
    default_provider_changed = Signal(int)
    target_language_changed = Signal(str)

    def __init__(self, service: SettingsService, parent: QWidget | None = None):
        from PySide6.QtCore import QObject

        super().__init__(parent if isinstance(parent, QObject) else None)
        self._service = service
        self._settings: Settings | None = None

    @property
    def providers(self) -> list[ProviderConfig]:
        return self._settings.providers if self._settings else []

    @property
    def target_language(self) -> str:
        return self._settings.target_language if self._settings else "de"

    def load_settings(self) -> None:
        try:
            self._set_loading(True)
            self._settings = self._service.get_settings()
            self.settings_loaded.emit()
        except Exception as e:
            self._emit_error(f"Failed to load settings: {e}")
        finally:
            self._set_loading(False)

    def save_settings(self) -> None:
        if not self._settings:
            return

        try:
            self._set_loading(True)
            self._service.save_settings(self._settings)
            self.settings_saved.emit()
        except ValueError as e:
            self._emit_error(str(e))
        except Exception as e:
            self._emit_error(f"Failed to save settings: {e}")
        finally:
            self._set_loading(False)

    def add_provider(self, provider: ProviderConfig) -> None:
        if not self._settings:
            return

        error = self._service.validate_provider_config(provider)
        if error:
            self._emit_error(error)
            return

        assert self._settings is not None
        self._settings.providers.append(provider)
        self.provider_added.emit(provider)

    def update_provider(self, index: int, provider: ProviderConfig) -> None:
        if not self._validate_index(index):
            return

        error = self._service.validate_provider_config(provider)
        if error:
            self._emit_error(error)
            return

        assert self._settings is not None
        self._settings.providers[index] = provider
        self.provider_updated.emit(index)

    def delete_provider(self, index: int) -> None:
        if not self._validate_index(index):
            return

        assert self._settings is not None
        del self._settings.providers[index]
        self.provider_deleted.emit(index)

    def set_default_provider(self, index: int) -> None:
        if not self._validate_index(index):
            return

        assert self._settings is not None
        self._clear_all_defaults()
        self._settings.providers[index].is_default = True
        self.default_provider_changed.emit(index)

    def update_target_language(self, language: str) -> None:
        if not self._settings:
            return

        self._settings.target_language = language
        self.target_language_changed.emit(language)

    def _validate_index(self, index: int) -> bool:
        if not self._settings:
            return False
        if index < 0 or index >= len(self._settings.providers):
            self._emit_error(f"Invalid provider index: {index}")
            return False
        return True

    def _clear_all_defaults(self) -> None:
        if not self._settings:
            return
        for provider in self._settings.providers:
            provider.is_default = False
