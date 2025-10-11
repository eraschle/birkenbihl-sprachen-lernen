"""Base protocol for all UI components.

Defines the contract that all UI components must follow.
"""

from typing import Protocol


class UIComponent(Protocol):
    """Protocol for reusable UI components.

    All UI components should implement this protocol to ensure consistency
    and testability across the application.
    """

    def render(self) -> None:
        """Render the component to Streamlit.

        This method should contain all the UI rendering logic for the component.
        It should be side-effect free except for Streamlit rendering calls.
        """
        ...
