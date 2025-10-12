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


@pytest.fixture(autouse=True)
def reset_singleton() -> Generator[None, None, None]:
    """Reset SettingsService singleton state before each test."""
    SettingsService._instance = None
    SettingsService._settings = None
    SettingsService._current_provider = None
    SettingsService._storage = None
    yield
    SettingsService._instance = None
    SettingsService._settings = None
    SettingsService._current_provider = None
    SettingsService._storage = None


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
        # Initialize storage manually for testing
        SettingsService._storage = SettingsStorageProvider(temp_db)

        SettingsService.save_settings(sample_settings, use_database=True)

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

        # Set storage in service
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Load settings via service
        loaded = SettingsService.load_settings(use_database=True)

        assert loaded.target_language == "de"
        assert len(loaded.providers) == 2
        assert loaded.providers[0].name == "OpenAI GPT-4"

    def test_load_from_empty_database_raises_error(self, temp_db: Path) -> None:
        """Test loading from empty database raises NotFoundError."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        with pytest.raises(NotFoundError):
            SettingsService.load_settings(use_database=True)

    def test_save_and_load_roundtrip(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test full roundtrip: save to database and load back."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Save settings
        SettingsService.save_settings(sample_settings, use_database=True)

        # Clear in-memory cache
        SettingsService._settings = None

        # Load settings back
        loaded = SettingsService.load_settings(use_database=True)

        assert loaded.target_language == sample_settings.target_language
        assert len(loaded.providers) == len(sample_settings.providers)
        assert loaded.providers[0].name == sample_settings.providers[0].name
        assert loaded.providers[0].api_key == sample_settings.providers[0].api_key

    def test_update_settings_in_database(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test updating settings in database."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Save initial settings
        SettingsService.save_settings(sample_settings, use_database=True)

        # Update settings
        updated_settings = Settings(
            target_language="es",
            providers=[
                ProviderConfig(
                    name="Gemini Flash",
                    provider_type="gemini",
                    model="gemini-2.0-flash",
                    api_key="gemini-key",
                    is_default=True,
                )
            ],
        )

        SettingsService.save_settings(updated_settings, use_database=True)

        # Load and verify
        loaded = SettingsService.load_settings(use_database=True)

        assert loaded.target_language == "es"
        assert len(loaded.providers) == 1
        assert loaded.providers[0].name == "Gemini Flash"

    def test_current_provider_updated_after_database_load(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test that current provider is updated after loading from database."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Save settings with default provider
        SettingsService.save_settings(sample_settings, use_database=True)

        # Clear current provider
        SettingsService._current_provider = None

        # Load settings
        SettingsService.load_settings(use_database=True)

        # Verify current provider is set to default
        current = SettingsService.get_current_provider()
        assert current is not None
        assert current.name == "OpenAI GPT-4"
        assert current.is_default is True

    def test_validate_provider_before_database_save(self, temp_db: Path) -> None:
        """Test that provider validation occurs before database save."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Create settings with invalid provider (unsupported type)
        invalid_settings = Settings(
            providers=[
                ProviderConfig(
                    name="Invalid Provider",
                    provider_type="invalid_type",
                    model="invalid-model",
                    api_key="test-key",
                )
            ]
        )

        # Should raise ValueError due to validation
        with pytest.raises(ValueError, match="wird nicht unterstützt"):
            SettingsService.save_settings(invalid_settings, use_database=True)

        # Verify nothing was saved to database
        with pytest.raises(NotFoundError):
            storage = SettingsStorageProvider(temp_db)
            storage.load()

    def test_database_persistence_across_service_resets(self, temp_db: Path, sample_settings: Settings) -> None:
        """Test that database persists settings across service resets."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Save settings
        SettingsService.save_settings(sample_settings, use_database=True)

        # Reset service completely
        SettingsService._instance = None
        SettingsService._settings = None
        SettingsService._current_provider = None
        SettingsService._storage = None

        # Create new storage connection
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Load settings - should still be there
        loaded = SettingsService.load_settings(use_database=True)

        assert loaded.target_language == "de"
        assert len(loaded.providers) == 2

    def test_yaml_and_database_independent(self, temp_db: Path, sample_settings: Settings, tmp_path: Path) -> None:
        """Test that YAML and database storage are independent."""
        yaml_file = tmp_path / "settings.yaml"
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Save to YAML
        SettingsService.save_settings(sample_settings, settings_file=yaml_file, use_database=False)

        # Modify and save to database
        db_settings = Settings(
            target_language="fr",
            providers=[
                ProviderConfig(
                    name="Different Provider",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="different-key",
                )
            ],
        )
        SettingsService.save_settings(db_settings, use_database=True)

        # Load from YAML
        yaml_loaded = SettingsService.load_settings(settings_file=yaml_file, use_database=False)
        assert yaml_loaded.target_language == "de"
        assert len(yaml_loaded.providers) == 2

        # Load from database
        db_loaded = SettingsService.load_settings(use_database=True)
        assert db_loaded.target_language == "fr"
        assert len(db_loaded.providers) == 1
