"""Tests for button components."""

from birkenbihl.ui.components.buttons import ActionButtonGroup, BackButton, ButtonConfig, SaveCancelButtons


class TestButtonConfig:
    """Tests for ButtonConfig dataclass."""

    def test_button_config_defaults(self) -> None:
        """Test ButtonConfig with default values."""
        config = ButtonConfig(label="Test Button")

        assert config.label == "Test Button"
        assert config.type == "secondary"
        assert config.icon == ""
        assert config.use_container_width is True

    def test_button_config_custom(self) -> None:
        """Test ButtonConfig with custom values."""
        config = ButtonConfig(
            label="Save",
            type="primary",
            icon="💾",
            use_container_width=False,
        )

        assert config.label == "Save"
        assert config.type == "primary"
        assert config.icon == "💾"
        assert config.use_container_width is False


class TestActionButtonGroup:
    """Tests for ActionButtonGroup component."""

    def test_initialization(self) -> None:
        """Test ActionButtonGroup initialization."""
        buttons = {
            "save": ButtonConfig("Speichern", type="primary"),
            "cancel": ButtonConfig("Abbrechen"),
        }
        group = ActionButtonGroup(buttons, key="test")

        assert group.buttons == buttons
        assert group.key == "test"

    def test_initialization_no_key(self) -> None:
        """Test ActionButtonGroup initialization without key."""
        buttons = {"save": ButtonConfig("Speichern")}
        group = ActionButtonGroup(buttons)

        assert group.buttons == buttons
        assert group.key == ""

    def test_empty_buttons(self) -> None:
        """Test ActionButtonGroup with empty buttons dict."""
        group = ActionButtonGroup({}, key="test")

        assert group.buttons == {}
        # render() should return None for empty buttons
        # (Would need Streamlit mocking to test render fully)


class TestSaveCancelButtons:
    """Tests for SaveCancelButtons component."""

    def test_initialization(self) -> None:
        """Test SaveCancelButtons initialization."""
        buttons = SaveCancelButtons(key="test", save_disabled=False)

        assert buttons.key == "test"
        assert buttons.save_disabled is False
        assert "save" in buttons.buttons
        assert "cancel" in buttons.buttons

    def test_button_configuration(self) -> None:
        """Test that SaveCancelButtons has correct button configs."""
        buttons = SaveCancelButtons()

        # Save button should be primary with icon
        save_config = buttons.buttons["save"]
        assert save_config.type == "primary"
        assert save_config.icon == "💾"
        assert save_config.label == "Speichern"

        # Cancel button should be secondary with icon
        cancel_config = buttons.buttons["cancel"]
        assert cancel_config.type == "secondary"
        assert cancel_config.icon == "✗"
        assert cancel_config.label == "Abbrechen"


class TestBackButton:
    """Tests for BackButton component."""

    def test_initialization(self) -> None:
        """Test BackButton initialization."""
        button = BackButton(key="my_back_button")

        assert button.key == "my_back_button"

    def test_initialization_default_key(self) -> None:
        """Test BackButton initialization with default key."""
        button = BackButton()

        assert button.key == "back_button"
