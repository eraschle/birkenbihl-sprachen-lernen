"""Tests for provider components."""

from unittest.mock import Mock, patch

import pytest
import streamlit as st

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.ui.components.provider import ProviderSelector, get_current_provider, get_providers_from_settings
from birkenbihl.ui.models.context import ProviderSelectorContext


@pytest.fixture
def sample_providers() -> list[ProviderConfig]:
    """Create sample provider configs for testing."""
    return [
        ProviderConfig(
            name="OpenAI GPT-4",
            provider_type="openai",
            model="gpt-4",
            api_key="test-key-1",
        ),
        ProviderConfig(
            name="Anthropic Claude",
            provider_type="anthropic",
            model="claude-3-opus",
            api_key="test-key-2",
        ),
        ProviderConfig(
            name="OpenAI GPT-3.5",
            provider_type="openai",
            model="gpt-3.5-turbo",
            api_key="test-key-3",
        ),
    ]


@pytest.fixture
def context_with_providers(sample_providers: list[ProviderConfig]) -> ProviderSelectorContext:
    """Create a ProviderSelectorContext with providers."""
    return ProviderSelectorContext(
        providers=sample_providers,
        default_provider=sample_providers[0],
        disabled=False,
        key_suffix="test",
    )


@pytest.fixture
def context_no_providers() -> ProviderSelectorContext:
    """Create a ProviderSelectorContext with no providers."""
    return ProviderSelectorContext(
        providers=[],
        default_provider=None,
        disabled=False,
        key_suffix="test",
    )


class TestProviderSelector:
    """Tests for ProviderSelector component."""

    def test_initialization(self, context_with_providers: ProviderSelectorContext) -> None:
        """Test that ProviderSelector initializes correctly."""
        selector = ProviderSelector(context_with_providers)
        assert selector.context == context_with_providers

    def test_get_provider_names(self, context_with_providers: ProviderSelectorContext) -> None:
        """Test extracting provider names."""
        selector = ProviderSelector(context_with_providers)
        names = selector._get_provider_names()

        assert len(names) == 3
        assert "OpenAI GPT-4" in names
        assert "Anthropic Claude" in names
        assert "OpenAI GPT-3.5" in names

    def test_get_default_index_with_default_provider(self, context_with_providers: ProviderSelectorContext) -> None:
        """Test getting default index when default provider is set."""
        selector = ProviderSelector(context_with_providers)
        index = selector._get_default_index()

        # Default provider is first in list (OpenAI GPT-4)
        assert index == 0

    def test_get_default_index_no_default_provider(self) -> None:
        """Test getting default index when no default provider is set."""
        context = ProviderSelectorContext(
            providers=[
                ProviderConfig(name="Test", provider_type="openai", model="gpt-4", api_key="key"),
            ],
            default_provider=None,
        )
        selector = ProviderSelector(context)
        index = selector._get_default_index()

        # Should default to 0
        assert index == 0

    def test_get_default_index_different_default(self, sample_providers: list[ProviderConfig]) -> None:
        """Test getting default index when default is not first provider."""
        context = ProviderSelectorContext(
            providers=sample_providers,
            default_provider=sample_providers[1],  # Anthropic Claude
        )
        selector = ProviderSelector(context)
        index = selector._get_default_index()

        # Should be index 1
        assert index == 1

    def test_generate_key_with_suffix(self, context_with_providers: ProviderSelectorContext) -> None:
        """Test key generation with suffix."""
        selector = ProviderSelector(context_with_providers)
        key = selector._generate_key()

        assert key == "provider_select_test"

    def test_generate_key_without_suffix(self) -> None:
        """Test key generation without suffix."""
        context = ProviderSelectorContext(
            providers=[],
            default_provider=None,
            key_suffix="",
        )
        selector = ProviderSelector(context)
        key = selector._generate_key()

        assert key == "provider_select"

    def test_find_provider_by_name(self, context_with_providers: ProviderSelectorContext) -> None:
        """Test finding provider by name."""
        selector = ProviderSelector(context_with_providers)
        provider = selector._find_provider_by_name("Anthropic Claude")

        assert provider.name == "Anthropic Claude"
        assert provider.model == "claude-3-opus"

    def test_render_returns_none_for_empty_providers(self, context_no_providers: ProviderSelectorContext) -> None:
        """Test that render returns None when no providers available."""
        selector = ProviderSelector(context_no_providers)

        # Mock streamlit warning
        with patch("streamlit.warning") as mock_warning:
            result = selector.render()

            # Should show warning
            mock_warning.assert_called_once()
            # Should return None
            assert result is None


class TestProviderHelperFunctions:
    """Tests for provider helper functions."""

    def test_get_providers_from_settings(self, sample_providers: list[ProviderConfig]) -> None:
        """Test getting providers from session state settings."""
        # Mock session state
        st.session_state.settings = Mock()
        st.session_state.settings.providers = sample_providers

        providers = get_providers_from_settings()

        assert providers == sample_providers
        assert len(providers) == 3

    @patch("birkenbihl.ui.components.provider.SettingsService.get_current_provider")
    def test_get_current_provider(self, mock_get_current: Mock, sample_providers: list[ProviderConfig]) -> None:
        """Test getting current provider."""
        mock_get_current.return_value = sample_providers[0]

        provider = get_current_provider()

        assert provider == sample_providers[0]
        mock_get_current.assert_called_once()

    @patch("birkenbihl.ui.components.provider.SettingsService.get_current_provider")
    def test_get_current_provider_none(self, mock_get_current: Mock) -> None:
        """Test getting current provider when none is set."""
        mock_get_current.return_value = None

        provider = get_current_provider()

        assert provider is None
        mock_get_current.assert_called_once()
