"""Base protocol for ViewModels in MVVM architecture."""

from typing import Protocol


class ViewModel(Protocol):
    """Protocol for MVVM ViewModels.

    ViewModels orchestrate business logic, hold UI state, and communicate
    with Views via Qt Signals/Slots (Observer pattern).

    Note: Implementations should inherit from QObject to use Qt signals.

    ViewModels:
    - Coordinate Services (TranslationService, SettingsService)
    - Execute Commands
    - Emit signals for state changes
    - NO direct UI code (Views handle rendering)

    Examples:
        TranslationCreationViewModel, TranslationEditorViewModel, SettingsViewModel
    """

    def initialize(self) -> None:
        """Initialize ViewModel.

        Called after construction to load data, setup state, etc.
        Separate from __init__ to allow proper signal/slot connections.
        """
        ...

    def cleanup(self) -> None:
        """Cleanup resources before destruction.

        Called before ViewModel is destroyed to release resources,
        cancel async operations, etc.
        """
        ...
