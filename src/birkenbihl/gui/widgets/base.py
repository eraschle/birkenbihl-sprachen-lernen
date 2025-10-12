"""Base protocol for reusable widgets."""

from typing import Protocol


class ReusableWidget(Protocol):
    """Protocol for reusable UI widgets.

    Widgets are self-contained UI components that can be used across
    multiple views. They encapsulate UI logic but delegate business
    logic to parent views/ViewModels.

    Widgets:
    - Emit signals for user interactions
    - Accept data via constructor/properties
    - NO direct service calls (parent handles)
    - Small, focused responsibility

    Examples:
        ProviderSelector, LanguageSelector, AlignmentEditor
    """

    def update_data(self, data: object) -> None:
        """Update widget with new data.

        Args:
            data: New data to display (type depends on widget)
        """
        ...
