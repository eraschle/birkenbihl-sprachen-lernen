"""Tests for SettingsViewModel."""

from unittest.mock import MagicMock, Mock

import pytest
from pytestqt.qtbot import QtBot

from birkenbihl.gui.models.settings_viewmodel import SettingsViewModel
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService


@pytest.fixture
def mock_service():
    """Create mock SettingsService."""
    service = Mock()
    settings = Settings(
        providers=[
            ProviderConfig(
                name="Provider1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            ),
            ProviderConfig(
                name="Provider2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
            ),
        ],
        target_language="de",
    )
    service.get_settings.return_value = settings
    service.validate_provider_config.return_value = None
    return service


@pytest.fixture
def viewmodel(mock_service: SettingsService):
    """Create SettingsViewModel."""
    vm = SettingsViewModel(mock_service)
    return vm


def test_initial_state(viewmodel: SettingsViewModel):
    """Test initial state."""
    state = viewmodel.state
    assert state.providers == []
    assert state.selected_provider_index == -1
    assert state.target_language.code == "de"
    assert not state.is_editing
    assert not state.has_unsaved_changes


def test_load_settings(qtbot: QtBot, viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test load settings."""
    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.load_settings()

    assert len(viewmodel.state.providers) == 2
    assert viewmodel.state.target_language.code == "de"
    assert not viewmodel.state.has_unsaved_changes
    mock_service.get_settings.assert_called_once()


def test_add_provider(qtbot: QtBot, viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test add provider."""
    viewmodel.load_settings()
    new_provider = ProviderConfig(
        name="NewProvider",
        provider_type="openai",
        model="gpt-4",
        api_key="new-key",
    )

    # Mock service to return updated settings after add
    updated_settings = Settings(
        providers=[
            ProviderConfig(
                name="Provider1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            ),
            ProviderConfig(
                name="Provider2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
            ),
            new_provider,
        ],
        target_language="de",
    )
    mock_service.get_settings.return_value = updated_settings

    with qtbot.waitSignal(viewmodel.provider_added, timeout=1000):
        viewmodel.add_provider(new_provider)

    assert len(viewmodel.state.providers) == 3
    assert viewmodel.state.has_unsaved_changes
    mock_service.validate_provider_config.assert_called_once_with(new_provider)
    mock_service.add_provider.assert_called_once_with(new_provider)


def test_add_provider_validation_error(qtbot: QtBot, viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test add provider with validation error."""
    viewmodel.load_settings()
    mock_service.validate_provider_config.return_value = "Invalid config"
    new_provider = ProviderConfig(
        name="Bad",
        provider_type="openai",
        model="gpt-4",
        api_key="key",
    )

    with qtbot.waitSignal(viewmodel.error_occurred, timeout=1000):
        viewmodel.add_provider(new_provider)

    assert len(viewmodel.state.providers) == 2  # Not added


def test_update_provider(viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test update provider."""
    viewmodel.load_settings()
    updated = ProviderConfig(
        name="Updated",
        provider_type="openai",
        model="gpt-4",
        api_key="new-key",
    )

    # Mock service to return updated settings
    updated_settings = Settings(
        providers=[
            updated,
            ProviderConfig(
                name="Provider2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
            ),
        ],
        target_language="de",
    )
    mock_service.get_settings.return_value = updated_settings

    viewmodel.update_provider(0, updated)

    assert viewmodel.state.providers[0].name == "Updated"
    assert viewmodel.state.has_unsaved_changes
    mock_service.update_provider.assert_called_once_with(0, updated)


def test_update_provider_invalid_index(viewmodel: SettingsViewModel):
    """Test update provider with invalid index."""
    viewmodel.load_settings()
    updated = ProviderConfig(
        name="Test",
        provider_type="openai",
        model="gpt-4",
        api_key="key",
    )

    viewmodel.update_provider(99, updated)

    # Should not update anything
    assert viewmodel.state.providers[0].name == "Provider1"


def test_delete_provider(qtbot: QtBot, viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test delete provider."""
    viewmodel.load_settings()

    # Mock service to return updated settings after delete
    updated_settings = Settings(
        providers=[
            ProviderConfig(
                name="Provider2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
            ),
        ],
        target_language="de",
    )
    mock_service.get_settings.return_value = updated_settings

    with qtbot.waitSignal(viewmodel.provider_deleted, timeout=1000):
        viewmodel.delete_provider(0)

    assert len(viewmodel.state.providers) == 1
    assert viewmodel.state.has_unsaved_changes
    mock_service.delete_provider.assert_called_once_with(0)


def test_delete_provider_invalid_index(viewmodel: SettingsViewModel):
    """Test delete provider with invalid index."""
    viewmodel.load_settings()

    viewmodel.delete_provider(99)

    assert len(viewmodel.state.providers) == 2


def test_set_target_language(qtbot: QtBot, viewmodel: SettingsViewModel):
    """Test set target language."""
    viewmodel.load_settings()

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_target_language("es")

    assert viewmodel.state.target_language.code == "es"
    assert viewmodel.state.has_unsaved_changes


def test_set_editing(qtbot: QtBot, viewmodel: SettingsViewModel):
    """Test set editing state."""
    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_editing(True)

    assert viewmodel.state.is_editing


def test_select_provider(qtbot: QtBot, viewmodel: SettingsViewModel):
    """Test select provider."""
    viewmodel.load_settings()

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.select_provider(0)

    assert viewmodel.state.selected_provider_index == 0


def test_save_settings(qtbot: QtBot, viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test save settings."""
    viewmodel.load_settings()
    viewmodel.set_target_language("es")

    with qtbot.waitSignal(viewmodel.settings_saved, timeout=1000):
        viewmodel.save_settings()

    assert not viewmodel.state.has_unsaved_changes
    # Should call save_settings without parameters
    mock_service.save_settings.assert_called_once_with()


def test_save_settings_error(qtbot: QtBot, viewmodel: SettingsViewModel, mock_service: MagicMock):
    """Test save settings with error."""
    viewmodel.load_settings()
    mock_service.save_settings.side_effect = Exception("Save failed")

    with qtbot.waitSignal(viewmodel.error_occurred, timeout=1000):
        viewmodel.save_settings()


def test_cleanup(viewmodel: SettingsViewModel):
    """Test cleanup."""
    viewmodel.cleanup()
    # Should not raise any errors
