"""Tests for UI State dataclasses."""

from uuid import uuid4
import pytest

from birkenbihl.gui.models.ui_state import (
    TranslationCreationState,
    TranslationEditorState,
    SettingsViewState,
)
from birkenbihl.models.settings import ProviderConfig


class TestTranslationCreationState:
    """Test TranslationCreationState dataclass."""

    def test_default_values(self):
        """Test default state values."""
        state = TranslationCreationState()

        assert state.title == ""
        assert state.source_text == ""
        assert state.source_language is None
        assert state.target_language == "de"
        assert state.selected_provider is None
        assert state.is_translating is False
        assert state.progress == 0.0

    def test_custom_values(self):
        """Test state with custom values."""
        provider = ProviderConfig(
            name="Test", provider_type="openai", model="gpt-4", api_key="test"
        )

        state = TranslationCreationState(
            title="Test Title",
            source_text="Hello World",
            source_language="en",
            target_language="de",
            selected_provider=provider,
            is_translating=True,
            progress=0.5,
        )

        assert state.title == "Test Title"
        assert state.source_text == "Hello World"
        assert state.source_language == "en"
        assert state.target_language == "de"
        assert state.selected_provider == provider
        assert state.is_translating is True
        assert state.progress == 0.5


class TestTranslationEditorState:
    """Test TranslationEditorState dataclass."""

    def test_default_values(self):
        """Test default state values."""
        state = TranslationEditorState()

        assert state.translation is None
        assert state.selected_sentence_uuid is None
        assert state.edit_mode == "view"
        assert state.is_saving is False
        assert state.has_unsaved_changes is False

    def test_custom_values(self):
        """Test state with custom values."""
        sentence_uuid = uuid4()

        state = TranslationEditorState(
            translation=None,  # Would be Translation object
            selected_sentence_uuid=sentence_uuid,
            edit_mode="edit_natural",
            is_saving=True,
            has_unsaved_changes=True,
        )

        assert state.selected_sentence_uuid == sentence_uuid
        assert state.edit_mode == "edit_natural"
        assert state.is_saving is True
        assert state.has_unsaved_changes is True


class TestSettingsViewState:
    """Test SettingsViewState dataclass."""

    def test_default_values(self):
        """Test default state values."""
        state = SettingsViewState()

        assert state.providers == []
        assert state.selected_provider_index == -1
        assert state.target_language == "de"
        assert state.is_editing is False
        assert state.has_unsaved_changes is False

    def test_custom_values(self):
        """Test state with custom values."""
        providers = [
            ProviderConfig(
                name="Provider1", provider_type="openai", model="gpt-4", api_key="key1"
            ),
            ProviderConfig(
                name="Provider2", provider_type="anthropic", model="claude-3", api_key="key2"
            ),
        ]

        state = SettingsViewState(
            providers=providers,
            selected_provider_index=0,
            target_language="en",
            is_editing=True,
            has_unsaved_changes=True,
        )

        assert len(state.providers) == 2
        assert state.selected_provider_index == 0
        assert state.target_language == "en"
        assert state.is_editing is True
        assert state.has_unsaved_changes is True
