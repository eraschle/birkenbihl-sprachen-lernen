"""Base ViewModel for MVVM pattern."""

from PySide6.QtCore import QObject, Signal


class BaseViewModel(QObject):
    """Base class for all ViewModels.

    Provides common functionality:
    - Qt Signal/Slot mechanism
    - Error handling
    - State management
    """

    error_occurred = Signal(str)
    loading_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._is_loading = False

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    def _set_loading(self, loading: bool) -> None:
        if self._is_loading != loading:
            self._is_loading = loading
            self.loading_changed.emit(loading)

    def _emit_error(self, message: str) -> None:
        self.error_occurred.emit(message)
