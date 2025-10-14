"""Tests for SettingsService database integration."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService
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


@pytest.mark.unit
class TestSettingsServiceDatabaseIntegration:
    """Test SettingsService integration with database storage."""

    def test_save_to_database(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test saving settings to database via service."""
        service = SettingsService(db_path=temp_db)

        # Load sample settings by adding providers
        service.load_settings()  # Load defaults
        for provider in sample_settings.providers:
            service.add_provider(provider)
        service.get_settings().target_language = sample_settings.target_language

        service.save_settings(use_database=True)

        # Verify settings were saved to database
        storage = SettingsStorageProvider(temp_db)
        loaded = storage.load()

        assert loaded.target_language == "de"
        assert len(loaded.providers) == 2
        assert loaded.providers[0].name == "OpenAI GPT-4"

    def test_load_from_database(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test loading settings from database via service."""
        # Prepare database with settings
        storage = SettingsStorageProvider(temp_db)
        storage.save(sample_settings)

        # Load settings via service
        service = SettingsService(db_path=temp_db)
        loaded = service.load_settings(use_database=True)

        assert loaded.target_language == "de"
        assert len(loaded.providers) == 2
        assert loaded.providers[0].name == "OpenAI GPT-4"

    def test_load_from_empty_database_raises_error(self, temp_db: Path) -> None:
        """Test loading from empty database raises NotFoundError."""
        service = SettingsService(db_path=temp_db)

        with pytest.raises(NotFoundError):
            service.load_settings(use_database=True)

    def test_save_and_load_roundtrip(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test full roundtrip: save to database and load back."""
        service1 = SettingsService(db_path=temp_db)

        # Load and configure settings
        service1.load_settings()
        for provider in sample_settings.providers:
            service1.add_provider(provider)
        service1.get_settings().target_language = sample_settings.target_language

        # Save settings
        service1.save_settings(use_database=True)

        # Load settings back with new service instance
        service2 = SettingsService(db_path=temp_db)
        loaded = service2.load_settings(use_database=True)

        assert loaded.target_language == sample_settings.target_language
        assert len(loaded.providers) == len(sample_settings.providers)
        assert loaded.providers[0].name == sample_settings.providers[0].name
        assert loaded.providers[0].api_key == sample_settings.providers[0].api_key

    def test_update_settings_in_database(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test updating settings in database."""
        service = SettingsService(db_path=temp_db)

        # Load and save initial settings
        service.load_settings()
        for provider in sample_settings.providers:
            service.add_provider(provider)
        service.get_settings().target_language = sample_settings.target_language
        service.save_settings(use_database=True)

        # Update settings
        service2 = SettingsService(db_path=temp_db)
        service2.load_settings()
        service2.add_provider(
            ProviderConfig(
                name="Gemini Flash",
                provider_type="gemini",
                model="gemini-2.0-flash",
                api_key="gemini-key",
                is_default=True,
            )
        )
        service2.get_settings().target_language = "es"
        service2.save_settings(use_database=True)

        # Load and verify
        service3 = SettingsService(db_path=temp_db)
        loaded = service3.load_settings(use_database=True)

        assert loaded.target_language == "es"
        assert len(loaded.providers) == 1
        assert loaded.providers[0].name == "Gemini Flash"

    def test_validate_provider_before_database_save(self, temp_db: Path) -> None:
        """Test that provider validation occurs before database save."""
        service = SettingsService(db_path=temp_db)
        service.load_settings()

        # Add invalid provider (unsupported type)
        service.add_provider(
            ProviderConfig(
                name="Invalid Provider",
                provider_type="invalid_type",
                model="invalid-model",
                api_key="test-key",
            )
        )

        # Should raise ValueError due to validation
        with pytest.raises(ValueError, match="wird nicht unterstützt"):
            service.save_settings(use_database=True)

        # Verify nothing was saved to database
        with pytest.raises(NotFoundError):
            storage = SettingsStorageProvider(temp_db)
            storage.load()

    def test_database_persistence_across_service_resets(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test that database persists settings across service resets."""
        service1 = SettingsService(db_path=temp_db)

        # Save settings
        service1.load_settings()
        for provider in sample_settings.providers:
            service1.add_provider(provider)
        service1.get_settings().target_language = sample_settings.target_language
        service1.save_settings(use_database=True)

        # Create new service instance
        service2 = SettingsService(db_path=temp_db)

        # Load settings - should still be there
        loaded = service2.load_settings(use_database=True)

        assert loaded.target_language == "de"
        assert len(loaded.providers) == 2

    def test_yaml_and_database_independent(self, temp_db: Path, sample_settings: Settings, tmp_path: Path) -> None:
        """Test that YAML and database storage are independent."""
        yaml_file = tmp_path / "settings.yaml"

        # Save to YAML
        service1 = SettingsService()
        service1.load_settings()
        for provider in sample_settings.providers:
            service1.add_provider(provider)
        service1.get_settings().target_language = sample_settings.target_language
        service1.save_settings(settings_file=yaml_file, use_database=False)

        # Modify and save to database
        service2 = SettingsService(db_path=temp_db)
        service2.load_settings()
        service2.add_provider(
            ProviderConfig(
                name="Different Provider",
                provider_type="openai",
                model="gpt-4o",
                api_key="different-key",
            )
        )
        service2.get_settings().target_language = "fr"
        service2.save_settings(use_database=True)

        # Load from YAML
        service3 = SettingsService()
        yaml_loaded = service3.load_settings(settings_file=yaml_file, use_database=False)
        assert yaml_loaded.target_language == "de"
        assert len(yaml_loaded.providers) == 2

        # Load from database
        service4 = SettingsService(db_path=temp_db)
        db_loaded = service4.load_settings(use_database=True)
        assert db_loaded.target_language == "fr"
        assert len(db_loaded.providers) == 1
