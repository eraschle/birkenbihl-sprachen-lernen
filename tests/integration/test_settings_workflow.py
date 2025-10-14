"""Integration tests for complete settings workflows."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.services.settings_service import SettingsService


@pytest.fixture
def temp_db() -> Generator[Path, None, None]:
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_yaml(tmp_path: Path) -> Path:
    """Create temporary YAML file for testing."""
    yaml_file = tmp_path / "test_settings.yaml"
    return yaml_file


@pytest.mark.integration
class TestSettingsWorkflowIntegration:
    """Integration tests for complete settings workflows."""

    def test_yaml_to_database_migration(self, temp_yaml: Path, temp_db: Path) -> None:
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
        service1 = SettingsService(file_path=temp_yaml)
        settings = service1.load_settings(use_database=False)

        # Migrate to database
        service2 = SettingsService(file_path=temp_db)
        service2._settings = settings  # Transfer settings to new service
        service2.save_settings(use_database=True)

        # Load from database and verify
        service3 = SettingsService(file_path=temp_db)
        loaded_from_db = service3.load_settings(use_database=True)

        assert loaded_from_db.target_language == "de"
        assert len(loaded_from_db.providers) == 2
        assert loaded_from_db.providers[0].name == "OpenAI GPT-4"
        assert loaded_from_db.providers[1].name == "Claude Sonnet"

    def test_database_to_yaml_export(self, temp_db: Path, temp_yaml: Path) -> None:
        """Test exporting settings from database to YAML."""
        # Create settings in database
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="Gemini Flash",
                provider_type="gemini",
                model="gemini-2.0-flash",
                api_key="gemini-key",
                is_default=True,
            )
        )
        service1.get_settings().target_language = "es"
        service1.save_settings(use_database=True)

        # Load from database
        service2 = SettingsService(file_path=temp_db)
        settings = service2.load_settings(use_database=True)

        # Export to YAML
        service3 = SettingsService(file_path=temp_yaml)
        service3._settings = settings  # Transfer settings to new service
        service3.save_settings(use_database=False)

        # Verify YAML file contents
        with temp_yaml.open("r") as f:
            yaml_data = yaml.safe_load(f)

        assert yaml_data["target_language"] == "es"
        assert len(yaml_data["providers"]) == 1
        assert yaml_data["providers"][0]["name"] == "Gemini Flash"

    def test_complete_user_workflow_add_provider(self, temp_db: Path) -> None:
        """Test complete workflow: load settings, add provider, save back."""
        # Initial settings
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="OpenAI GPT-4",
                provider_type="openai",
                model="gpt-4o",
                api_key="openai-key",
                is_default=True,
            )
        )
        service1.save_settings(use_database=True)

        # Load settings
        service2 = SettingsService(file_path=temp_db)
        service2.load_settings(use_database=True)

        # Add new provider
        service2.add_provider(
            ProviderConfig(
                name="Claude Sonnet",
                provider_type="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key="claude-key",
            )
        )

        # Save updated settings
        service2.save_settings(use_database=True)

        # Verify changes
        service3 = SettingsService(file_path=temp_db)
        final = service3.load_settings(use_database=True)

        assert len(final.providers) == 2
        assert final.providers[0].name == "OpenAI GPT-4"
        assert final.providers[1].name == "Claude Sonnet"

    def test_complete_user_workflow_change_default_provider(self, temp_db: Path) -> None:
        """Test workflow: change default provider."""
        # Initial settings with two providers
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="Provider A",
                provider_type="openai",
                model="gpt-4o",
                api_key="key-a",
                is_default=True,
            )
        )
        service1.add_provider(
            ProviderConfig(
                name="Provider B",
                provider_type="anthropic",
                model="claude",
                api_key="key-b",
                is_default=False,
            )
        )
        service1.save_settings(use_database=True)

        # Change default to Provider B
        service2 = SettingsService(file_path=temp_db)
        service2.load_settings(use_database=True)

        # Update provider at index 1 to be default
        updated_provider = ProviderConfig(
            name="Provider B",
            provider_type="anthropic",
            model="claude",
            api_key="key-b",
            is_default=True,
        )
        service2.update_provider(1, updated_provider)
        service2.save_settings(use_database=True)

        # Verify default provider changed
        service3 = SettingsService(file_path=temp_db)
        final = service3.load_settings(use_database=True)

        assert final.providers[0].is_default is False
        assert final.providers[1].is_default is True

        # Verify SettingsService recognizes new default
        default_provider = service3.get_default_provider()
        assert default_provider is not None
        assert default_provider.name == "Provider B"

    def test_complete_user_workflow_remove_provider(self, temp_db: Path) -> None:
        """Test workflow: remove a provider."""
        # Initial settings with three providers
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(ProviderConfig(name="Provider 1", provider_type="openai", model="gpt-4o", api_key="key1"))
        service1.add_provider(
            ProviderConfig(name="Provider 2", provider_type="anthropic", model="claude", api_key="key2")
        )
        service1.add_provider(ProviderConfig(name="Provider 3", provider_type="gemini", model="gemini", api_key="key3"))
        service1.save_settings(use_database=True)

        # Remove Provider 2
        service2 = SettingsService(file_path=temp_db)
        service2.load_settings(use_database=True)

        # Find and delete Provider 2
        service2.delete_provider(1)  # Provider 2 is at index 1
        service2.save_settings(use_database=True)

        # Verify provider removed
        service3 = SettingsService(file_path=temp_db)
        final = service3.load_settings(use_database=True)

        assert len(final.providers) == 2
        assert final.providers[0].name == "Provider 1"
        assert final.providers[1].name == "Provider 3"

    def test_complete_user_workflow_change_language(self, temp_db: Path) -> None:
        """Test workflow: change target language."""
        # Initial settings
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="Test Provider",
                provider_type="openai",
                model="gpt-4o",
                api_key="test-key",
            )
        )
        service1.save_settings(use_database=True)

        # Change language to Spanish
        service2 = SettingsService(file_path=temp_db)
        loaded = service2.load_settings(use_database=True)

        loaded.target_language = "es"
        service2.save_settings(use_database=True)

        # Verify language changed
        service3 = SettingsService(file_path=temp_db)
        final = service3.load_settings(use_database=True)

        assert final.target_language == "es"
        assert len(final.providers) == 1

    def test_complete_user_workflow_update_api_key(self, temp_db: Path) -> None:
        """Test workflow: update API key for a provider."""
        # Initial settings
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="OpenAI GPT-4",
                provider_type="openai",
                model="gpt-4o",
                api_key="old-key",
                is_default=True,
            )
        )
        service1.save_settings(use_database=True)

        # Update API key
        service2 = SettingsService(file_path=temp_db)
        loaded = service2.load_settings(use_database=True)

        updated_provider = ProviderConfig(
            name=loaded.providers[0].name,
            provider_type=loaded.providers[0].provider_type,
            model=loaded.providers[0].model,
            api_key="new-key",
            is_default=loaded.providers[0].is_default,
            supports_streaming=loaded.providers[0].supports_streaming,
        )

        service2.update_provider(0, updated_provider)
        service2.save_settings(use_database=True)

        # Verify API key updated
        service3 = SettingsService(file_path=temp_db)
        final = service3.load_settings(use_database=True)

        assert final.providers[0].api_key == "new-key"

    def test_multi_step_configuration_workflow(self, temp_db: Path) -> None:
        """Test multi-step configuration workflow."""
        # Step 1: Initialize with basic settings
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()  # Defaults (no providers)
        service1.save_settings(use_database=True)

        # Step 2: Add first provider
        service2 = SettingsService(file_path=temp_db)
        service2.load_settings(use_database=True)
        service2.add_provider(
            ProviderConfig(
                name="Provider 1",
                provider_type="openai",
                model="gpt-4o",
                api_key="key1",
                is_default=True,
            )
        )
        service2.save_settings(use_database=True)

        # Step 3: Add second provider
        service3 = SettingsService(file_path=temp_db)
        service3.load_settings(use_database=True)
        service3.add_provider(
            ProviderConfig(
                name="Provider 2",
                provider_type="anthropic",
                model="claude",
                api_key="key2",
            )
        )
        service3.save_settings(use_database=True)

        # Step 4: Change target language
        service4 = SettingsService(file_path=temp_db)
        loaded3 = service4.load_settings(use_database=True)
        loaded3.target_language = "es"
        service4.save_settings(use_database=True)

        # Verify final state
        service5 = SettingsService(file_path=temp_db)
        final = service5.load_settings(use_database=True)

        assert final.target_language == "es"
        assert len(final.providers) == 2
        assert final.providers[0].name == "Provider 1"
        assert final.providers[1].name == "Provider 2"

    def test_settings_persistence_across_sessions(self, temp_db: Path) -> None:
        """Test that settings persist across different 'sessions'."""
        # Session 1: Create and save settings
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="Persistent Provider",
                provider_type="openai",
                model="gpt-4o",
                api_key="persistent-key",
                is_default=True,
            )
        )
        service1.save_settings(use_database=True)

        # Session 2: Load settings (simulate new session with new service instance)
        service2 = SettingsService(file_path=temp_db)
        loaded = service2.load_settings(use_database=True)

        assert loaded.target_language == "de"
        assert loaded.providers[0].name == "Persistent Provider"
        assert loaded.providers[0].api_key == "persistent-key"

    def test_error_recovery_workflow(self, temp_db: Path) -> None:
        """Test recovery from errors during workflow."""
        # Save valid settings
        service1 = SettingsService(file_path=temp_db)
        service1.load_settings()
        service1.add_provider(
            ProviderConfig(
                name="Valid Provider",
                provider_type="openai",
                model="gpt-4o",
                api_key="valid-key",
            )
        )
        service1.save_settings(use_database=True)

        # Attempt to save invalid settings (should fail validation)
        service2 = SettingsService(file_path=temp_db)
        service2.load_settings()
        service2.add_provider(
            ProviderConfig(
                name="Invalid Provider",
                provider_type="invalid_type",
                model="invalid-model",
                api_key="invalid-key",
            )
        )

        with pytest.raises(ValueError):
            service2.save_settings(use_database=True)

        # Verify original settings still intact
        service3 = SettingsService(file_path=temp_db)
        recovered = service3.load_settings(use_database=True)

        assert recovered.target_language == "de"
        assert recovered.providers[0].name == "Valid Provider"
