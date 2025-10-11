"""Session state manager implementation.

Provides type-safe access to Streamlit session state.
"""

from typing import Any

import streamlit as st


class SessionStateManager:
    """Manages Streamlit session state with type safety.

    Encapsulates all st.session_state access to prevent direct manipulation
    and provide a cleaner interface.
    """

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from session state.

        Args:
            key: Session state key
            default: Default value if key doesn't exist

        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set value in session state.

        Args:
            key: Session state key
            value: Value to store
        """
        st.session_state[key] = value

    @staticmethod
    def delete(key: str) -> None:
        """Delete key from session state.

        Args:
            key: Session state key to delete
        """
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def exists(key: str) -> bool:
        """Check if key exists in session state.

        Args:
            key: Session state key to check

        Returns:
            True if key exists, False otherwise
        """
        return key in st.session_state

    # Convenience properties for common state keys

    @property
    def current_view(self) -> str:
        """Get current view name."""
        return self.get("current_view", "Übersetzen")

    @current_view.setter
    def current_view(self, value: str) -> None:
        """Set current view name."""
        self.set("current_view", value)

    @property
    def is_translating(self) -> bool:
        """Check if translation is in progress."""
        return self.get("is_translating", False)

    @is_translating.setter
    def is_translating(self, value: bool) -> None:
        """Set translation in progress flag."""
        self.set("is_translating", value)

    @property
    def translation_result(self) -> Any:
        """Get translation result from session state."""
        return self.get("translation_result")

    @translation_result.setter
    def translation_result(self, value: Any) -> None:
        """Set translation result in session state."""
        self.set("translation_result", value)

    @property
    def is_new_translation(self) -> bool:
        """Check if this is a new translation."""
        return self.get("is_new_translation", False)

    @is_new_translation.setter
    def is_new_translation(self, value: bool) -> None:
        """Set new translation flag."""
        self.set("is_new_translation", value)

    @property
    def selected_translation_id(self) -> Any:
        """Get selected translation ID."""
        return self.get("selected_translation_id")

    @selected_translation_id.setter
    def selected_translation_id(self, value: Any) -> None:
        """Set selected translation ID."""
        self.set("selected_translation_id", value)

    @classmethod
    def initialize(cls) -> None:
        """Initialize session state with default values.

        This should be called once at app startup to ensure all
        required state keys exist with sensible defaults.
        """
        defaults = {
            "current_view": "Übersetzen",
            "is_translating": False,
            "translation_result": None,
            "is_new_translation": False,
            "selected_translation_id": None,
            "translation_pending": None,
            "detected_language_info": None,
            "uploaded_text_content": "",
            "last_uploaded_file": None,
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
