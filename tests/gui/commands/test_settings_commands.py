"""Tests for settings commands."""

from unittest.mock import Mock

import pytest

from birkenbihl.gui.commands.settings_commands import (
    AddProviderCommand,
    DeleteProviderCommand,
    SaveSettingsCommand,
)
from birkenbihl.models.settings import ProviderConfig, Settings


@pytest.fixture
def mock_service():
    """Create mock SettingsService."""
    service = Mock()
    service.validate_provider_config.return_value = None
    return service


@pytest.fixture
def provider():
    """Create test provider."""
    return ProviderConfig(
        name="TestProvider",
        provider_type="openai",
        model="gpt-4",
        api_key="test-key",
    )


@pytest.fixture
def providers():
    """Create test providers list."""
    return [
        ProviderConfig(
            name="Provider1",
            provider_type="openai",
            model="gpt-4",
            api_key="key1",
        ),
        ProviderConfig(
            name="Provider2",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
        ),
    ]


def test_add_provider_can_execute_success(mock_service, provider):
    """Test can execute with valid provider."""
    cmd = AddProviderCommand(mock_service, provider)
    assert cmd.can_execute()


def test_add_provider_can_execute_no_name(mock_service):
    """Test can execute with no name."""
    provider = ProviderConfig(
        name="",
        provider_type="openai",
        model="gpt-4",
        api_key="key",
    )
    cmd = AddProviderCommand(mock_service, provider)
    assert not cmd.can_execute()


def test_add_provider_can_execute_no_model(mock_service):
    """Test can execute with no model."""
    provider = ProviderConfig(
        name="Test",
        provider_type="openai",
        model="",
        api_key="key",
    )
    cmd = AddProviderCommand(mock_service, provider)
    assert not cmd.can_execute()


def test_add_provider_execute_success(mock_service, provider):
    """Test successful provider addition."""
    cmd = AddProviderCommand(mock_service, provider)
    result = cmd.execute()

    assert result.success
    assert result.data == provider
    assert "added" in result.message.lower()
    mock_service.validate_provider_config.assert_called_once_with(provider)


def test_add_provider_execute_cannot_execute(mock_service):
    """Test execute when cannot execute."""
    provider = ProviderConfig(
        name="",
        provider_type="openai",
        model="gpt-4",
        api_key="key",
    )
    cmd = AddProviderCommand(mock_service, provider)
    result = cmd.execute()

    assert not result.success
    assert "required" in result.message.lower()


def test_add_provider_execute_validation_error(mock_service, provider):
    """Test execute with validation error."""
    mock_service.validate_provider_config.return_value = "Invalid config"

    cmd = AddProviderCommand(mock_service, provider)
    result = cmd.execute()

    assert not result.success
    assert result.message == "Invalid config"


def test_delete_provider_can_execute_success(providers):
    """Test can execute with valid index."""
    cmd = DeleteProviderCommand(providers, 0)
    assert cmd.can_execute()


def test_delete_provider_can_execute_invalid_index_negative(providers):
    """Test can execute with negative index."""
    cmd = DeleteProviderCommand(providers, -1)
    assert not cmd.can_execute()


def test_delete_provider_can_execute_invalid_index_too_large(providers):
    """Test can execute with index too large."""
    cmd = DeleteProviderCommand(providers, 99)
    assert not cmd.can_execute()


def test_delete_provider_execute_success(providers):
    """Test successful provider deletion."""
    cmd = DeleteProviderCommand(providers, 0)
    result = cmd.execute()

    assert result.success
    assert "deleted" in result.message.lower()
    assert "Provider1" in result.message


def test_delete_provider_execute_cannot_execute(providers):
    """Test execute when cannot execute."""
    cmd = DeleteProviderCommand(providers, 99)
    result = cmd.execute()

    assert not result.success
    assert "invalid" in result.message.lower()


def test_save_settings_can_execute(mock_service):
    """Test can execute always returns True."""
    settings = Settings(providers=[], target_language="de")
    cmd = SaveSettingsCommand(mock_service, settings)
    assert cmd.can_execute()


def test_save_settings_execute_success(mock_service):
    """Test successful settings save."""
    settings = Settings(providers=[], target_language="de")
    cmd = SaveSettingsCommand(mock_service, settings)
    result = cmd.execute()

    assert result.success
    assert "saved" in result.message.lower()
    mock_service.save_settings.assert_called_once_with(settings)


def test_save_settings_execute_error(mock_service):
    """Test execute with error."""
    mock_service.save_settings.side_effect = Exception("Save failed")
    settings = Settings(providers=[], target_language="de")

    cmd = SaveSettingsCommand(mock_service, settings)
    result = cmd.execute()

    assert not result.success
    assert "Save failed" in result.message
