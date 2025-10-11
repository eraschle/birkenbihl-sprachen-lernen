"""Button components for reusable action groups.

Provides standardized button groups for common UI actions.
"""

from dataclasses import dataclass
from typing import Callable

import streamlit as st


@dataclass
class ButtonConfig:
    """Configuration for a single button.

    Attributes:
        label: Button text
        type: Button type ("primary", "secondary")
        icon: Optional emoji icon to prepend
        use_container_width: Whether button should fill container width
    """

    label: str
    type: str = "secondary"
    icon: str = ""
    use_container_width: bool = True


class ActionButtonGroup:
    """Reusable action button group component.

    Renders a set of buttons (Save/Cancel/Back/Delete) in columns
    and returns which button was clicked.

    Examples:
        >>> buttons = {
        ...     "save": ButtonConfig("Speichern", type="primary", icon="💾"),
        ...     "cancel": ButtonConfig("Abbrechen", icon="✗")
        ... }
        >>> group = ActionButtonGroup(buttons, key="my_form")
        >>> clicked = group.render()
        >>> if clicked == "save":
        ...     # Handle save
    """

    def __init__(self, buttons: dict[str, ButtonConfig], key: str = "") -> None:
        """Initialize action button group.

        Args:
            buttons: Dictionary mapping button keys to ButtonConfig
            key: Unique key prefix for button widgets
        """
        self.buttons = buttons
        self.key = key

    def render(self) -> str | None:
        """Render button group and return clicked button key.

        Returns:
            Key of clicked button or None if no button was clicked
        """
        if not self.buttons:
            return None

        # Create columns for buttons
        cols = st.columns(len(self.buttons))

        clicked_button = None

        for idx, (button_key, config) in enumerate(self.buttons.items()):
            with cols[idx]:
                button_label = f"{config.icon} {config.label}" if config.icon else config.label
                button_widget_key = f"{self.key}_{button_key}" if self.key else button_key

                if st.button(
                    button_label,
                    key=button_widget_key,
                    type=config.type,
                    use_container_width=config.use_container_width,
                ):
                    clicked_button = button_key

        return clicked_button


class SaveCancelButtons(ActionButtonGroup):
    """Pre-configured Save/Cancel button group.

    Convenience class for the common Save/Cancel pattern.
    """

    def __init__(self, key: str = "", save_disabled: bool = False) -> None:
        """Initialize Save/Cancel buttons.

        Args:
            key: Unique key prefix for button widgets
            save_disabled: Whether save button should be disabled
        """
        buttons = {
            "save": ButtonConfig("Speichern", type="primary", icon="💾"),
            "cancel": ButtonConfig("Abbrechen", icon="✗"),
        }
        super().__init__(buttons, key)
        self.save_disabled = save_disabled

    def render(self) -> str | None:
        """Render Save/Cancel buttons.

        Returns:
            "save" if Save clicked, "cancel" if Cancel clicked, None otherwise
        """
        if not self.buttons:
            return None

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "💾 Speichern",
                key=f"{self.key}_save" if self.key else "save",
                type="primary",
                disabled=self.save_disabled,
                use_container_width=True,
            ):
                return "save"

        with col2:
            if st.button(
                "✗ Abbrechen", key=f"{self.key}_cancel" if self.key else "cancel", use_container_width=True
            ):
                return "cancel"

        return None


class BackButton:
    """Simple back button component.

    Renders a single back button, commonly used in headers.
    """

    def __init__(self, key: str = "back_button") -> None:
        """Initialize back button.

        Args:
            key: Unique key for button widget
        """
        self.key = key

    def render(self) -> bool:
        """Render back button.

        Returns:
            True if button was clicked, False otherwise
        """
        return st.button("← Zurück", key=self.key, use_container_width=True)
