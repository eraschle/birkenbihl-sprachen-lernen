"""Integration tests for complete settings workflows."""

import tempfile
from pathlib import Path

import pytest
import yaml

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.storage.settings_storage import SettingsStorageProvider


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_yaml(tmp_path):
    """Create temporary YAML file for testing."""
    yaml_file = tmp_path / "test_settings.yaml"
    return yaml_file


@pytest.fixture(autouse=True)
def reset_singleton():
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


@pytest.mark.integration
class TestSettingsWorkflowIntegration:
    """Integration tests for complete settings workflows."""

    def test_yaml_to_database_migration(self, temp_yaml, temp_db):
        """Test migrating settings from YAML to database."""
        # Create YAML settings
        yaml_settings = {
            "target_language": "de",
            "providers": [
                {
                    "name": "OpenAI GPT-4",
                    "provider_type": "openai",
                    "model": "gpt-4o",
                    "api_key": "sk-test-key",
                    "is_default": True,
                    "supports_streaming": True,
                },
                {
                    "name": "Claude Sonnet",
                    "provider_type": "anthropic",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "sk-ant-test-key",
                    "is_default": False,
                    "supports_streaming": True,
                },
            ],
        }

        # Write YAML file
        with temp_yaml.open("w") as f:
            yaml.safe_dump(yaml_settings, f)

        # Load from YAML via service
        loaded_from_yaml = SettingsService.load_settings(settings_file=temp_yaml, use_database=False)

        # Migrate to database
        SettingsService._storage = SettingsStorageProvider(temp_db)
        SettingsService.save_settings(loaded_from_yaml, use_database=True)

        # Load from database and verify
        loaded_from_db = SettingsService.load_settings(use_database=True)

        assert loaded_from_db.target_language == "de"
        assert len(loaded_from_db.providers) == 2
        assert loaded_from_db.providers[0].name == "OpenAI GPT-4"
        assert loaded_from_db.providers[1].name == "Claude Sonnet"

    def test_database_to_yaml_export(self, temp_db, temp_yaml):
        """Test exporting settings from database to YAML."""
        # Create settings in database
        SettingsService._storage = SettingsStorageProvider(temp_db)

        settings = Settings(
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

        SettingsService.save_settings(settings, use_database=True)

        # Load from database
        loaded = SettingsService.load_settings(use_database=True)

        # Export to YAML
        SettingsService.save_settings(loaded, settings_file=temp_yaml, use_database=False)

        # Verify YAML file contents
        with temp_yaml.open("r") as f:
            yaml_data = yaml.safe_load(f)

        assert yaml_data["target_language"] == "es"
        assert len(yaml_data["providers"]) == 1
        assert yaml_data["providers"][0]["name"] == "Gemini Flash"

    def test_complete_user_workflow_add_provider(self, temp_db):
        """Test complete workflow: load settings, add provider, save back."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Initial settings
        initial_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="openai-key",
                    is_default=True,
                )
            ],
        )

        SettingsService.save_settings(initial_settings, use_database=True)

        # Load settings
        loaded = SettingsService.load_settings(use_database=True)

        # Add new provider
        new_provider = ProviderConfig(
            name="Claude Sonnet",
            provider_type="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="claude-key",
        )

        updated_settings = Settings(
            target_language=loaded.target_language,
            providers=loaded.providers + [new_provider],
        )

        # Save updated settings
        SettingsService.save_settings(updated_settings, use_database=True)

        # Verify changes
        final = SettingsService.load_settings(use_database=True)

        assert len(final.providers) == 2
        assert final.providers[0].name == "OpenAI GPT-4"
        assert final.providers[1].name == "Claude Sonnet"

    def test_complete_user_workflow_change_default_provider(self, temp_db):
        """Test workflow: change default provider."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Initial settings with two providers
        initial_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="Provider A",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="key-a",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Provider B",
                    provider_type="anthropic",
                    model="claude",
                    api_key="key-b",
                    is_default=False,
                ),
            ],
        )

        SettingsService.save_settings(initial_settings, use_database=True)

        # Change default to Provider B
        loaded = SettingsService.load_settings(use_database=True)

        updated_providers = [
            ProviderConfig(
                name="Provider A",
                provider_type="openai",
                model="gpt-4o",
                api_key="key-a",
                is_default=False,
            ),
            ProviderConfig(
                name="Provider B",
                provider_type="anthropic",
                model="claude",
                api_key="key-b",
                is_default=True,
            ),
        ]

        updated_settings = Settings(target_language=loaded.target_language, providers=updated_providers)

        SettingsService.save_settings(updated_settings, use_database=True)

        # Verify default provider changed
        final = SettingsService.load_settings(use_database=True)

        assert final.providers[0].is_default is False
        assert final.providers[1].is_default is True

        # Verify SettingsService recognizes new default
        default_provider = SettingsService.get_default_provider()
        assert default_provider.name == "Provider B"

    def test_complete_user_workflow_remove_provider(self, temp_db):
        """Test workflow: remove a provider."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Initial settings with three providers
        initial_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(name="Provider 1", provider_type="openai", model="gpt-4o", api_key="key1"),
                ProviderConfig(name="Provider 2", provider_type="anthropic", model="claude", api_key="key2"),
                ProviderConfig(name="Provider 3", provider_type="gemini", model="gemini", api_key="key3"),
            ],
        )

        SettingsService.save_settings(initial_settings, use_database=True)

        # Remove Provider 2
        loaded = SettingsService.load_settings(use_database=True)

        updated_providers = [p for p in loaded.providers if p.name != "Provider 2"]

        updated_settings = Settings(target_language=loaded.target_language, providers=updated_providers)

        SettingsService.save_settings(updated_settings, use_database=True)

        # Verify provider removed
        final = SettingsService.load_settings(use_database=True)

        assert len(final.providers) == 2
        assert final.providers[0].name == "Provider 1"
        assert final.providers[1].name == "Provider 3"

    def test_complete_user_workflow_change_language(self, temp_db):
        """Test workflow: change target language."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Initial settings
        initial_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="Test Provider",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ],
        )

        SettingsService.save_settings(initial_settings, use_database=True)

        # Change language to Spanish
        loaded = SettingsService.load_settings(use_database=True)

        updated_settings = Settings(target_language="es", providers=loaded.providers)

        SettingsService.save_settings(updated_settings, use_database=True)

        # Verify language changed
        final = SettingsService.load_settings(use_database=True)

        assert final.target_language == "es"
        assert len(final.providers) == 1

    def test_complete_user_workflow_update_api_key(self, temp_db):
        """Test workflow: update API key for a provider."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Initial settings
        initial_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="old-key",
                    is_default=True,
                )
            ],
        )

        SettingsService.save_settings(initial_settings, use_database=True)

        # Update API key
        loaded = SettingsService.load_settings(use_database=True)

        updated_providers = [
            ProviderConfig(
                name=p.name,
                provider_type=p.provider_type,
                model=p.model,
                api_key="new-key" if p.name == "OpenAI GPT-4" else p.api_key,
                is_default=p.is_default,
                supports_streaming=p.supports_streaming,
            )
            for p in loaded.providers
        ]

        updated_settings = Settings(target_language=loaded.target_language, providers=updated_providers)

        SettingsService.save_settings(updated_settings, use_database=True)

        # Verify API key updated
        final = SettingsService.load_settings(use_database=True)

        assert final.providers[0].api_key == "new-key"

    def test_multi_step_configuration_workflow(self, temp_db):
        """Test multi-step configuration workflow."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Step 1: Initialize with basic settings
        step1 = Settings(target_language="de", providers=[])
        SettingsService.save_settings(step1, use_database=True)

        # Step 2: Add first provider
        loaded1 = SettingsService.load_settings(use_database=True)
        step2 = Settings(
            target_language=loaded1.target_language,
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="key1",
                    is_default=True,
                )
            ],
        )
        SettingsService.save_settings(step2, use_database=True)

        # Step 3: Add second provider
        loaded2 = SettingsService.load_settings(use_database=True)
        step3 = Settings(
            target_language=loaded2.target_language,
            providers=loaded2.providers
            + [
                ProviderConfig(
                    name="Provider 2",
                    provider_type="anthropic",
                    model="claude",
                    api_key="key2",
                )
            ],
        )
        SettingsService.save_settings(step3, use_database=True)

        # Step 4: Change target language
        loaded3 = SettingsService.load_settings(use_database=True)
        step4 = Settings(target_language="es", providers=loaded3.providers)
        SettingsService.save_settings(step4, use_database=True)

        # Verify final state
        final = SettingsService.load_settings(use_database=True)

        assert final.target_language == "es"
        assert len(final.providers) == 2
        assert final.providers[0].name == "Provider 1"
        assert final.providers[1].name == "Provider 2"

    def test_settings_persistence_across_sessions(self, temp_db):
        """Test that settings persist across different 'sessions'."""
        # Session 1: Create and save settings
        SettingsService._storage = SettingsStorageProvider(temp_db)

        settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="Persistent Provider",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="persistent-key",
                    is_default=True,
                )
            ],
        )

        SettingsService.save_settings(settings, use_database=True)

        # Simulate session end
        SettingsService._instance = None
        SettingsService._settings = None
        SettingsService._current_provider = None
        SettingsService._storage = None

        # Session 2: Load settings
        SettingsService._storage = SettingsStorageProvider(temp_db)
        loaded = SettingsService.load_settings(use_database=True)

        assert loaded.target_language == "de"
        assert loaded.providers[0].name == "Persistent Provider"
        assert loaded.providers[0].api_key == "persistent-key"

    def test_error_recovery_workflow(self, temp_db):
        """Test recovery from errors during workflow."""
        SettingsService._storage = SettingsStorageProvider(temp_db)

        # Save valid settings
        valid_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="Valid Provider",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="valid-key",
                )
            ],
        )

        SettingsService.save_settings(valid_settings, use_database=True)

        # Attempt to save invalid settings (should fail validation)
        invalid_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="Invalid Provider",
                    provider_type="invalid_type",
                    model="invalid-model",
                    api_key="invalid-key",
                )
            ],
        )

        with pytest.raises(ValueError):
            SettingsService.save_settings(invalid_settings, use_database=True)

        # Verify original settings still intact
        recovered = SettingsService.load_settings(use_database=True)

        assert recovered.target_language == "de"
        assert recovered.providers[0].name == "Valid Provider"
