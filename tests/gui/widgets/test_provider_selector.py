"""Tests for ProviderSelector widget."""

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from birkenbihl.gui.widgets.provider_selector import ProviderSelector
from birkenbihl.models.settings import ProviderConfig


class TestProviderSelector:
    """Test ProviderSelector widget."""

    @pytest.fixture
    def providers(self, qapp: QApplication):
        """Provide test providers."""
        return [
            ProviderConfig(
                name="OpenAI - gpt-4",
                provider_type="openai",
                model="gpt-4",
                api_key="test-key-1",
                is_default=True,
            ),
            ProviderConfig(
                name="Anthropic - claude-3",
                provider_type="anthropic",
                model="claude-3",
                api_key="test-key-2",
            ),
        ]

    def test_widget_creation(self, providers: list[ProviderConfig]):
        """Test widget creation."""
        widget = ProviderSelector(providers)
        assert widget is not None
        assert widget._providers == providers

    def test_provider_selection(self, qtbot: QtBot, providers: list[ProviderConfig]):
        """Test provider selection signal."""
        widget = ProviderSelector(providers)
        selected = []
        widget.provider_selected.connect(lambda p: selected.append(p))

        with qtbot.waitSignal(widget.provider_selected, timeout=1000):
            widget._combo.setCurrentIndex(1)

        assert len(selected) == 1
        assert selected[0] == providers[1]

    def test_get_selected_provider(self, providers: list[ProviderConfig]):
        """Test getting selected provider."""
        widget = ProviderSelector(providers)
        widget._combo.setCurrentIndex(0)

        selected = widget.get_selected_provider()
        assert selected == providers[0]

    def test_update_data(self, providers: list[ProviderConfig]):
        """Test updating providers list."""
        widget = ProviderSelector(providers[:1])
        assert widget._combo.count() == 1

        widget.update_data(providers)
        assert widget._combo.count() == 2

    def test_format_provider_text(self, providers: list[ProviderConfig]):
        """Test provider text formatting."""
        widget = ProviderSelector(providers)

        text = widget._format_provider_text(providers[0])
        assert "OpenAI" in text
        assert "gpt-4" in text
        assert "[default]" in text

        text = widget._format_provider_text(providers[1])
        assert "Anthropic" in text
        assert "[default]" not in text
