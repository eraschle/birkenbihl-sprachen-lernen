"""State management interfaces.

Defines protocols for session state and cache management.
"""

from typing import Any, Protocol
from uuid import UUID


class StateManager(Protocol):
    """Protocol for session state management.

    Encapsulates all st.session_state accesses to provide type safety
    and prevent direct state manipulation in UI code.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from session state.

        Args:
            key: Session state key
            default: Default value if key doesn't exist

        Returns:
            Value from session state or default
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """Set value in session state.

        Args:
            key: Session state key
            value: Value to store
        """
        ...

    def delete(self, key: str) -> None:
        """Delete key from session state.

        Args:
            key: Session state key to delete
        """
        ...

    def exists(self, key: str) -> bool:
        """Check if key exists in session state.

        Args:
            key: Session state key to check

        Returns:
            True if key exists, False otherwise
        """
        ...


class CacheManager(Protocol):
    """Protocol for cache management.

    Manages temporary cached data like translation suggestions.
    """

    def get_suggestions(self, sentence_uuid: UUID) -> list[str] | None:
        """Get cached suggestions for sentence.

        Args:
            sentence_uuid: Sentence UUID to look up

        Returns:
            List of suggestion strings or None if not cached
        """
        ...

    def set_suggestions(self, sentence_uuid: UUID, suggestions: list[str]) -> None:
        """Cache suggestions for sentence.

        Args:
            sentence_uuid: Sentence UUID
            suggestions: List of suggestion strings
        """
        ...

    def clear_suggestions(self, sentence_uuid: UUID) -> None:
        """Clear cached suggestions for sentence.

        Args:
            sentence_uuid: Sentence UUID
        """
        ...
