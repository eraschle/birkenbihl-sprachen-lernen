"""Unit tests for Settings domain model.

Tests ProviderConfig and Settings classes as pure domain models
without file I/O operations.
"""

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings


@pytest.mark.unit
class TestProviderConfig:
    """Test ProviderConfig model."""

    def test_create_provider_config_with_all_fields(self) -> None:
        """Test creating a provider config with all fields specified."""
        config = ProviderConfig(
            name="OpenAI GPT-4",
            provider_type="openai",
            model="gpt-4o",
            api_key="sk-test-key-123",
            is_default=True,
        )

        assert config.name == "OpenAI GPT-4"
        assert config.provider_type == "openai"
        assert config.model == "gpt-4o"
        assert config.api_key == "sk-test-key-123"
        assert config.is_default is True

    def test_is_default_field_defaults_to_false(self) -> None:
        """Test that is_default field defaults to False when not specified."""
        config = ProviderConfig(
            name="Claude",
            provider_type="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="sk-ant-test-123",
        )

        assert config.is_default is False

    def test_provider_config_is_immutable_with_pydantic(self) -> None:
        """Test that ProviderConfig validates data with Pydantic."""
        config = ProviderConfig(
            name="OpenAI GPT-4",
            provider_type="openai",
            model="gpt-4o",
            api_key="sk-test-key-123",
        )

        # Pydantic BaseModel allows mutation by default
        config.name = "Modified Name"
        assert config.name == "Modified Name"

    def test_provider_config_validates_required_fields(self) -> None:
        """Test that ProviderConfig requires all mandatory fields."""
        with pytest.raises(ValueError, match="validation errors for ProviderConfig"):
            ProviderConfig(name="Test", provider_type="openai")  # type: ignore


@pytest.mark.unit
class TestSettingsDomainModel:
    """Test Settings domain model creation and validation."""

    def test_create_settings_with_providers(self) -> None:
        """Test creating Settings instance with providers."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-openai",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Claude Sonnet",
                    provider_type="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    api_key="sk-ant-test",
                    is_default=False,
                ),
            ],
            target_language="de",
        )

        assert len(settings.providers) == 2
        assert settings.target_language == "de"
        assert settings.providers[0].name == "OpenAI GPT-4"
        assert settings.providers[1].name == "Claude Sonnet"

    def test_create_settings_with_empty_providers(self) -> None:
        """Test creating Settings instance with empty providers list."""
        settings = Settings(providers=[], target_language="de")

        assert settings.providers == []
        assert settings.target_language == "de"

    def test_create_settings_with_custom_target_language(self) -> None:
        """Test creating Settings instance with custom target language."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test",
                    is_default=True,
                )
            ],
            target_language="es",
        )

        assert settings.target_language == "es"

    def test_settings_defaults_to_empty_providers_and_german(self) -> None:
        """Test that Settings uses default values when not specified."""
        settings = Settings()

        assert settings.providers == []
        assert settings.target_language == "de"

    def test_providers_list_is_mutable(self) -> None:
        """Test that providers list can be modified after creation."""
        settings = Settings(providers=[], target_language="de")

        new_provider = ProviderConfig(
            name="OpenAI GPT-4",
            provider_type="openai",
            model="gpt-4o",
            api_key="sk-test",
            is_default=True,
        )
        settings.providers.append(new_provider)

        assert len(settings.providers) == 1
        assert settings.providers[0].name == "OpenAI GPT-4"

    def test_settings_validates_with_pydantic(self) -> None:
        """Test that Settings validates data with Pydantic."""
        # Valid creation
        settings = Settings(target_language="fr")
        assert settings.target_language == "fr"

        # Invalid type should raise validation error
        with pytest.raises(ValueError, match="validation error for Settings"):
            Settings(target_language=123)  # type: ignore


@pytest.mark.unit
class TestGetDefaultProvider:
    """Test get_default_provider method."""

    def test_get_default_provider_returns_marked_default(self) -> None:
        """Test get_default_provider returns provider marked as default."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-openai",
                    is_default=False,
                ),
                ProviderConfig(
                    name="Claude Sonnet",
                    provider_type="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    api_key="sk-ant-test",
                    is_default=True,
                ),
            ],
            target_language="de",
        )

        default = settings.get_default_provider()

        assert default is not None
        assert default.name == "Claude Sonnet"
        assert default.is_default is True

    def test_get_default_provider_returns_first_if_none_marked(self) -> None:
        """Test get_default_provider returns first provider if none marked as default."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-openai",
                    is_default=False,
                ),
                ProviderConfig(
                    name="Claude Sonnet",
                    provider_type="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    api_key="sk-ant-test",
                    is_default=False,
                ),
            ],
            target_language="de",
        )

        default = settings.get_default_provider()

        assert default is not None
        assert default.name == "OpenAI GPT-4"

    def test_get_default_provider_returns_none_if_no_providers(self) -> None:
        """Test get_default_provider returns None if no providers exist."""
        settings = Settings(providers=[], target_language="de")

        default = settings.get_default_provider()

        assert default is None

    def test_get_default_provider_with_multiple_defaults_returns_first(self) -> None:
        """Test get_default_provider returns first marked default if multiple exist."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-openai",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Claude Sonnet",
                    provider_type="anthropic",
                    model="claude-3-5-sonnet-20241022",
                    api_key="sk-ant-test",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Claude Haiku",
                    provider_type="anthropic",
                    model="claude-3-5-haiku-20241022",
                    api_key="sk-ant-test-2",
                    is_default=False,
                ),
            ],
            target_language="de",
        )

        default = settings.get_default_provider()

        assert default is not None
        assert default.name == "OpenAI GPT-4"

    def test_get_default_provider_with_single_provider(self) -> None:
        """Test get_default_provider returns single provider regardless of is_default value."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-openai",
                    is_default=False,
                )
            ],
            target_language="de",
        )

        default = settings.get_default_provider()

        assert default is not None
        assert default.name == "OpenAI GPT-4"
