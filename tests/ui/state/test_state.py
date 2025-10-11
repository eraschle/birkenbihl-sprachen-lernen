"""Tests for state management."""

from uuid import uuid4

import pytest
import streamlit as st

from birkenbihl.ui.state.cache import SessionCacheManager
from birkenbihl.ui.state.session import SessionStateManager


@pytest.fixture(autouse=True)
def reset_session_state():
    """Reset session state before each test."""
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    yield
    # Cleanup after test
    for key in list(st.session_state.keys()):
        del st.session_state[key]


class TestSessionStateManager:
    """Tests for SessionStateManager."""

    def test_get_nonexistent_key_returns_default(self):
        """Test that getting a nonexistent key returns the default value."""
        manager = SessionStateManager()
        result = manager.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_get_nonexistent_key_without_default_returns_none(self):
        """Test that getting a nonexistent key without default returns None."""
        manager = SessionStateManager()
        result = manager.get("nonexistent_key")
        assert result is None

    def test_set_and_get(self):
        """Test setting and getting values."""
        manager = SessionStateManager()
        manager.set("test_key", "test_value")
        result = manager.get("test_key")
        assert result == "test_value"

    def test_exists_returns_true_for_existing_key(self):
        """Test that exists returns True for existing keys."""
        manager = SessionStateManager()
        manager.set("existing_key", "value")
        assert manager.exists("existing_key") is True

    def test_exists_returns_false_for_nonexistent_key(self):
        """Test that exists returns False for nonexistent keys."""
        manager = SessionStateManager()
        assert manager.exists("nonexistent_key") is False

    def test_delete_existing_key(self):
        """Test deleting an existing key."""
        manager = SessionStateManager()
        manager.set("test_key", "test_value")
        assert manager.exists("test_key") is True

        manager.delete("test_key")
        assert manager.exists("test_key") is False

    def test_delete_nonexistent_key_does_not_raise(self):
        """Test that deleting a nonexistent key doesn't raise an error."""
        manager = SessionStateManager()
        # Should not raise
        manager.delete("nonexistent_key")

    def test_current_view_property(self):
        """Test current_view property getter and setter."""
        manager = SessionStateManager()
        # Default value
        assert manager.current_view == "Übersetzen"

        # Set value
        manager.current_view = "Einstellungen"
        assert manager.current_view == "Einstellungen"

    def test_is_translating_property(self):
        """Test is_translating property getter and setter."""
        manager = SessionStateManager()
        # Default value
        assert manager.is_translating is False

        # Set value
        manager.is_translating = True
        assert manager.is_translating is True

    def test_translation_result_property(self):
        """Test translation_result property getter and setter."""
        manager = SessionStateManager()
        # Default value (None)
        assert manager.translation_result is None

        # Set value
        test_result = {"text": "test"}
        manager.translation_result = test_result
        assert manager.translation_result == test_result

    def test_is_new_translation_property(self):
        """Test is_new_translation property getter and setter."""
        manager = SessionStateManager()
        # Default value
        assert manager.is_new_translation is False

        # Set value
        manager.is_new_translation = True
        assert manager.is_new_translation is True

    def test_selected_translation_id_property(self):
        """Test selected_translation_id property getter and setter."""
        manager = SessionStateManager()
        # Default value (None)
        assert manager.selected_translation_id is None

        # Set value
        test_id = uuid4()
        manager.selected_translation_id = test_id
        assert manager.selected_translation_id == test_id

    def test_initialize_sets_defaults(self):
        """Test that initialize sets all default values."""
        SessionStateManager.initialize()

        assert st.session_state["current_view"] == "Übersetzen"
        assert st.session_state["is_translating"] is False
        assert st.session_state["translation_result"] is None
        assert st.session_state["is_new_translation"] is False
        assert st.session_state["selected_translation_id"] is None
        assert st.session_state["translation_pending"] is None
        assert st.session_state["detected_language_info"] is None
        assert st.session_state["uploaded_text_content"] == ""
        assert st.session_state["last_uploaded_file"] is None

    def test_initialize_does_not_overwrite_existing_values(self):
        """Test that initialize doesn't overwrite existing session state values."""
        # Set a value
        st.session_state["current_view"] = "Custom View"

        # Initialize
        SessionStateManager.initialize()

        # Value should not be overwritten
        assert st.session_state["current_view"] == "Custom View"


class TestSessionCacheManager:
    """Tests for SessionCacheManager."""

    def test_get_suggestions_nonexistent_returns_none(self):
        """Test that getting nonexistent suggestions returns None."""
        sentence_uuid = uuid4()
        result = SessionCacheManager.get_suggestions(sentence_uuid)
        assert result is None

    def test_set_and_get_suggestions(self):
        """Test setting and getting suggestions."""
        sentence_uuid = uuid4()
        suggestions = ["suggestion 1", "suggestion 2", "suggestion 3"]

        SessionCacheManager.set_suggestions(sentence_uuid, suggestions)
        result = SessionCacheManager.get_suggestions(sentence_uuid)

        assert result == suggestions

    def test_clear_suggestions(self):
        """Test clearing suggestions for a specific sentence."""
        sentence_uuid = uuid4()
        suggestions = ["suggestion 1", "suggestion 2"]

        SessionCacheManager.set_suggestions(sentence_uuid, suggestions)
        assert SessionCacheManager.get_suggestions(sentence_uuid) == suggestions

        SessionCacheManager.clear_suggestions(sentence_uuid)
        assert SessionCacheManager.get_suggestions(sentence_uuid) is None

    def test_clear_nonexistent_suggestions_does_not_raise(self):
        """Test that clearing nonexistent suggestions doesn't raise an error."""
        sentence_uuid = uuid4()
        # Should not raise
        SessionCacheManager.clear_suggestions(sentence_uuid)

    def test_clear_all_suggestions(self):
        """Test clearing all suggestions."""
        uuid1 = uuid4()
        uuid2 = uuid4()

        SessionCacheManager.set_suggestions(uuid1, ["suggestion 1"])
        SessionCacheManager.set_suggestions(uuid2, ["suggestion 2"])

        # Both should exist
        assert SessionCacheManager.get_suggestions(uuid1) is not None
        assert SessionCacheManager.get_suggestions(uuid2) is not None

        # Clear all
        SessionCacheManager.clear_all_suggestions()

        # Both should be gone
        assert SessionCacheManager.get_suggestions(uuid1) is None
        assert SessionCacheManager.get_suggestions(uuid2) is None

    def test_multiple_sentences_independent(self):
        """Test that suggestions for different sentences are independent."""
        uuid1 = uuid4()
        uuid2 = uuid4()

        suggestions1 = ["suggestion 1A", "suggestion 1B"]
        suggestions2 = ["suggestion 2A", "suggestion 2B"]

        SessionCacheManager.set_suggestions(uuid1, suggestions1)
        SessionCacheManager.set_suggestions(uuid2, suggestions2)

        # Each should have its own suggestions
        assert SessionCacheManager.get_suggestions(uuid1) == suggestions1
        assert SessionCacheManager.get_suggestions(uuid2) == suggestions2

        # Clearing one should not affect the other
        SessionCacheManager.clear_suggestions(uuid1)
        assert SessionCacheManager.get_suggestions(uuid1) is None
        assert SessionCacheManager.get_suggestions(uuid2) == suggestions2

    def test_suggestions_cache_persists_in_session_state(self):
        """Test that suggestions cache is stored in session state."""
        sentence_uuid = uuid4()
        suggestions = ["test suggestion"]

        SessionCacheManager.set_suggestions(sentence_uuid, suggestions)

        # Cache should be in session state
        assert SessionCacheManager.SUGGESTIONS_CACHE_KEY in st.session_state
        cache = st.session_state[SessionCacheManager.SUGGESTIONS_CACHE_KEY]
        assert f"suggestions_{sentence_uuid}" in cache
