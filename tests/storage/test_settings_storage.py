"""Tests for settings storage provider."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.storage.exceptions import NotFoundError
from birkenbihl.storage.settings_storage import SettingsStorageProvider


@pytest.fixture
def temp_db() -> Generator[Path, None, None]:
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def storage(temp_db: Path) -> SettingsStorageProvider:
    """Create settings storage provider with temporary database."""
    return SettingsStorageProvider(temp_db)


@pytest.fixture
def sample_settings() -> Settings:
    """Create sample settings for testing."""
    return Settings(
        target_language="de",
        providers=[
            ProviderConfig(
                name="OpenAI GPT-4",
                provider_type="openai",
                model="gpt-4o",
                api_key="sk-test-key",
                is_default=True,
            ),
            ProviderConfig(
                name="Claude Sonnet",
                provider_type="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test-key",
            ),
        ],
    )


class TestSettingsStorageProvider:
    """Tests for SettingsStorageProvider."""

    def test_save_new_settings(self, storage: SettingsStorageProvider, sample_settings: Settings) -> None:
        """Test saving new settings to database."""
        saved = storage.save(sample_settings)

        assert saved.target_language == sample_settings.target_language
        assert len(saved.providers) == len(sample_settings.providers)
        assert saved.providers[0].name == "OpenAI GPT-4"
        assert saved.providers[0].is_default is True
        assert saved.providers[1].name == "Claude Sonnet"

    def test_load_settings(self, storage: SettingsStorageProvider, sample_settings: Settings) -> None:
        """Test loading settings from database."""
        storage.save(sample_settings)
        loaded = storage.load()

        assert loaded.target_language == "de"
        assert len(loaded.providers) == 2
        assert loaded.providers[0].name == "OpenAI GPT-4"
        assert loaded.providers[0].api_key == "sk-test-key"

    def test_load_nonexistent_settings(self, storage: SettingsStorageProvider) -> None:
        """Test loading when no settings exist."""
        with pytest.raises(NotFoundError):
            storage.load()

    def test_update_settings(self, storage: SettingsStorageProvider, sample_settings: Settings) -> None:
        """Test updating existing settings."""
        storage.save(sample_settings)

        updated_settings = Settings(
            target_language="es",
            providers=[
                ProviderConfig(
                    name="Gemini Flash",
                    provider_type="gemini",
                    model="gemini-2.0-flash",
                    api_key="gemini-test-key",
                    is_default=True,
                )
            ],
        )

        result = storage.update(updated_settings)

        assert result.target_language == "es"
        assert len(result.providers) == 1
        assert result.providers[0].name == "Gemini Flash"

    def test_update_nonexistent_settings(self, storage: SettingsStorageProvider, sample_settings: Settings) -> None:
        """Test updating when no settings exist."""
        with pytest.raises(NotFoundError):
            storage.update(sample_settings)

    def test_delete_all_settings(self, storage: SettingsStorageProvider, sample_settings: Settings) -> None:
        """Test deleting all settings."""
        storage.save(sample_settings)
        deleted = storage.delete_all()

        assert deleted is True

        with pytest.raises(NotFoundError):
            storage.load()

    def test_delete_all_no_settings(self, storage: SettingsStorageProvider) -> None:
        """Test deleting when no settings exist."""
        deleted = storage.delete_all()
        assert deleted is False

    def test_save_overwrites_existing(self, storage: SettingsStorageProvider, sample_settings: Settings) -> None:
        """Test that save overwrites existing settings."""
        storage.save(sample_settings)

        new_settings = Settings(
            target_language="fr",
            providers=[
                ProviderConfig(
                    name="Groq Llama",
                    provider_type="groq",
                    model="llama-3.3-70b-versatile",
                    api_key="gsk-test-key",
                )
            ],
        )

        result = storage.save(new_settings)

        assert result.target_language == "fr"
        assert len(result.providers) == 1

        loaded = storage.load()
        assert loaded.target_language == "fr"

    def test_provider_with_base_url(self, storage: SettingsStorageProvider) -> None:
        """Test saving and loading provider with base_url."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="PublicAI",
                    provider_type="publicai",
                    model="swiss-ai/apertus-8b-instruct",
                    api_key="publicai-key",
                    api_url="https://api.publicai.co/v1",
                )
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].api_url == "https://api.publicai.co/v1"

    def test_provider_streaming_flag(self, storage: SettingsStorageProvider) -> None:
        """Test saving and loading provider with supports_streaming flag."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Bedrock Claude",
                    provider_type="bedrock",
                    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                    api_key="aws-credentials",
                    supports_streaming=False,
                )
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].supports_streaming is False

    def test_context_manager(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test storage provider as context manager."""
        with SettingsStorageProvider(temp_db) as storage:
            storage.save(sample_settings)
            loaded = storage.load()
            assert loaded.target_language == "de"

    def test_multiple_providers_order(self, storage: SettingsStorageProvider) -> None:
        """Test that provider order is preserved."""
        settings = Settings(
            providers=[
                ProviderConfig(name="Provider1", provider_type="openai", model="gpt-4o", api_key="key1"),
                ProviderConfig(name="Provider2", provider_type="anthropic", model="claude", api_key="key2"),
                ProviderConfig(name="Provider3", provider_type="gemini", model="gemini", api_key="key3"),
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].name == "Provider1"
        assert loaded.providers[1].name == "Provider2"
        assert loaded.providers[2].name == "Provider3"
