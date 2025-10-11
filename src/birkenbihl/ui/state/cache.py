"""Cache manager implementation.

Manages temporary cached data for the UI.
"""

from uuid import UUID

import streamlit as st


class SessionCacheManager:
    """Manages UI-specific caches using Streamlit session state.

    Handles caching of data like translation suggestions that should
    persist during a session but don't need to be saved.
    """

    SUGGESTIONS_CACHE_KEY = "suggestions_cache"

    @classmethod
    def _ensure_cache_exists(cls) -> None:
        """Ensure the suggestions cache exists in session state."""
        if cls.SUGGESTIONS_CACHE_KEY not in st.session_state:
            st.session_state[cls.SUGGESTIONS_CACHE_KEY] = {}

    @classmethod
    def get_suggestions(cls, sentence_uuid: UUID) -> list[str] | None:
        """Get cached suggestions for sentence.

        Args:
            sentence_uuid: Sentence UUID to look up

        Returns:
            List of suggestion strings or None if not cached
        """
        cls._ensure_cache_exists()
        cache = st.session_state[cls.SUGGESTIONS_CACHE_KEY]
        key = f"suggestions_{sentence_uuid}"
        return cache.get(key)

    @classmethod
    def set_suggestions(cls, sentence_uuid: UUID, suggestions: list[str]) -> None:
        """Cache suggestions for sentence.

        Args:
            sentence_uuid: Sentence UUID
            suggestions: List of suggestion strings
        """
        cls._ensure_cache_exists()
        cache = st.session_state[cls.SUGGESTIONS_CACHE_KEY]
        key = f"suggestions_{sentence_uuid}"
        cache[key] = suggestions

    @classmethod
    def clear_suggestions(cls, sentence_uuid: UUID) -> None:
        """Clear cached suggestions for sentence.

        Args:
            sentence_uuid: Sentence UUID
        """
        cls._ensure_cache_exists()
        cache = st.session_state[cls.SUGGESTIONS_CACHE_KEY]
        key = f"suggestions_{sentence_uuid}"
        if key in cache:
            del cache[key]

    @classmethod
    def clear_all_suggestions(cls) -> None:
        """Clear all cached suggestions."""
        if cls.SUGGESTIONS_CACHE_KEY in st.session_state:
            st.session_state[cls.SUGGESTIONS_CACHE_KEY] = {}
