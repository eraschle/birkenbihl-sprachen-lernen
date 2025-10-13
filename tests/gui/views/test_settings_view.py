"""Tests for SettingsView and ProviderDialog."""

import pytest
from PySide6.QtWidgets import QDialog

from birkenbihl.gui.views.settings_view import ProviderDialog
from birkenbihl.models.settings import ProviderConfig


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create test provider config."""
    return ProviderConfig(
        name="Test Provider",
        provider_type="openai",
        model="gpt-4",
        api_key="test-key",
        api_url="https://api.openai.com/v1",
        is_default=False,
        supports_streaming=True,
    )


class TestProviderDialog:
    """Tests for ProviderDialog."""

    def test_auto_name_generation_on_init(self, qtbot):
        """Test that name is auto-generated on initialization."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        assert dialog.name_edit.text() in ["AWS Bedrock", "Anthropic Claude", "OpenAI"]

    def test_auto_name_updates_when_model_changes(self, qtbot):
        """Test that name updates automatically when model changes."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        initial_provider = dialog.type_combo.currentText()
        dialog.model_combo.setCurrentText("test-model")

        assert dialog.name_edit.text() == f"{initial_provider} - test-model"

    def test_auto_name_updates_when_provider_type_changes(self, qtbot):
        """Test that name updates automatically when provider type changes."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        dialog.model_combo.setCurrentText("test-model")
        dialog.type_combo.setCurrentIndex(1)
        new_provider = dialog.type_combo.currentText()

        assert dialog.name_edit.text() == f"{new_provider} - test-model" or dialog.name_edit.text() == new_provider

    def test_manual_name_disables_auto_generation(self, qtbot):
        """Test that manual name entry disables auto-generation."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        dialog.model_combo.setCurrentText("test-model")
        initial_name = dialog.name_edit.text()

        dialog.name_edit.setText("My Custom Name")
        assert dialog._is_auto_generated_name is False

        dialog.type_combo.setCurrentIndex(1)
        assert dialog.name_edit.text() == "My Custom Name"

    def test_clearing_name_enables_auto_generation(self, qtbot):
        """Test that clearing name field re-enables auto-generation."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        dialog.name_edit.setText("My Custom Name")
        assert dialog._is_auto_generated_name is False

        dialog.name_edit.clear()
        dialog.model_combo.setCurrentText("test-model")

        initial_provider = dialog.type_combo.currentText()
        assert dialog.name_edit.text() == f"{initial_provider} - test-model"
        assert dialog._is_auto_generated_name is True

    def test_setting_name_to_auto_generated_value_enables_auto_generation(self, qtbot):
        """Test that setting name to auto-generated value enables auto-generation."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        initial_provider = dialog.type_combo.currentText()
        dialog.model_combo.setCurrentText("test-model")
        dialog.name_edit.setText("My Custom Name")
        assert dialog._is_auto_generated_name is False

        expected_name = f"{initial_provider} - test-model"
        dialog.name_edit.setText(expected_name)
        assert dialog._is_auto_generated_name is True

        dialog.type_combo.setCurrentIndex(1)
        new_provider = dialog.type_combo.currentText()
        expected_new_name = f"{new_provider} - test-model" if dialog.model_combo.count() > 0 else new_provider
        assert dialog._is_auto_generated_name is True

    def test_base_url_visibility_changes_with_provider(self, qtbot):
        """Test that base URL field visibility changes based on provider type."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitForWindowShown(dialog)

        for i in range(dialog.type_combo.count()):
            provider_type = dialog.type_combo.itemData(i)
            dialog.type_combo.setCurrentIndex(i)

            if provider_type in ["openai", "groq", "ollama", "litellm"]:
                assert dialog.base_url_label.isVisible() is True
                assert dialog.base_url_edit.isVisible() is True
            else:
                assert dialog.base_url_label.isVisible() is False
                assert dialog.base_url_edit.isVisible() is False

    def test_editing_existing_provider_disables_auto_name(self, qtbot, provider_config):
        """Test that editing existing provider disables auto-name generation."""
        dialog = ProviderDialog(provider_config=provider_config)
        qtbot.addWidget(dialog)

        assert dialog.name_edit.text() == "Test Provider"
        assert dialog._is_auto_generated_name is False

        dialog.model_combo.setCurrentText("gpt-4-turbo")
        assert dialog.name_edit.text() == "Test Provider"

    def test_get_provider_returns_correct_config(self, qtbot):
        """Test that get_provider returns correct configuration."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        for i in range(dialog.type_combo.count()):
            if dialog.type_combo.itemData(i) == "openai":
                dialog.type_combo.setCurrentIndex(i)
                break

        dialog.model_combo.setCurrentText("gpt-4")
        dialog.api_key_edit.setText("test-key")
        dialog.base_url_edit.setText("https://api.openai.com/v1")
        dialog.is_default_check.setChecked(True)
        dialog.supports_streaming_check.setChecked(False)

        provider = dialog.get_provider()

        assert provider is not None
        assert "gpt-4" in provider.name
        assert provider.provider_type == "openai"
        assert provider.model == "gpt-4"
        assert provider.api_key == "test-key"
        assert provider.api_url == "https://api.openai.com/v1"
        assert provider.is_default is True
        assert provider.supports_streaming is False

    def test_auto_generated_name_used_in_provider(self, qtbot):
        """Test that auto-generated name is used when name field is not manually set."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        dialog.model_combo.setCurrentText("test-model")
        dialog.api_key_edit.setText("test-key")

        provider = dialog.get_provider()
        assert provider is not None
        assert "test-model" in provider.name

    def test_validation_fails_when_model_empty(self, qtbot):
        """Test that validation fails when model is empty."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        dialog.name_edit.setText("Test")
        dialog.model_combo.clearEditText()
        dialog.api_key_edit.setText("test-key")

        provider = dialog.get_provider()
        assert provider is None

    def test_validation_fails_when_api_key_empty(self, qtbot):
        """Test that validation fails when API key is empty."""
        dialog = ProviderDialog()
        qtbot.addWidget(dialog)

        dialog.name_edit.setText("Test")
        dialog.model_combo.setCurrentText("test-model")

        provider = dialog.get_provider()
        assert provider is None
