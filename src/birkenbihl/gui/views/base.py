"""Base protocol for Views in MVVM architecture."""

from typing import Protocol


class View(Protocol):
    """Protocol for MVVM Views.

    Views are responsible for UI rendering only. Business logic is
    delegated to ViewModels. Views communicate with ViewModels via
    Qt Signals/Slots.

    Views:
    - Create UI widgets and layouts
    - Bind ViewModel signals to View slots
    - Update UI based on ViewModel state
    - NO business logic (only UI state)

    Examples:
        TranslationView, TranslationEditorView, SettingsView
    """

    def setup_ui(self) -> None:
        """Setup UI components (widgets, layouts).

        Called during construction to create all UI elements.
        Should be idempotent (safe to call multiple times).
        """
        ...

    def bind_viewmodel(self) -> None:
        """Connect ViewModel signals to View slots.

        Establishes bidirectional communication:
        - ViewModel signals → View slots (state updates)
        - View signals → ViewModel slots (user actions)
        """
        ...
