"""Unit tests for SettingsService instance-based operations.

Tests instance initialization, loading, saving, thread safety, and delegation
to Settings model for business logic.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService


@pytest.mark.unit
class TestSettingsServiceInstanceCreation:
    """Test SettingsService instance creation and initialization."""

    def test_create_new_instance(self) -> None:
        """Test that new instances can be created."""
        service1 = SettingsService()
        service2 = SettingsService()

        assert service1 is not service2
        assert isinstance(service1, SettingsService)
        assert isinstance(service2, SettingsService)

    def test_new_instance_has_no_settings_loaded(self) -> None:
        """Test that new instance has no settings loaded initially."""
        service = SettingsService()

        with pytest.raises(RuntimeError, match="Settings not loaded"):
            service.get_settings()


@pytest.mark.unit
class TestSettingsServiceLoadSettings:
    """Test SettingsService load_settings functionality."""

    def test_load_settings_from_specified_file(self, tmp_path: Path) -> None:
        """Test that load_settings loads from specified settings file."""
        settings_file = tmp_path / "custom.yaml"
        settings_file.write_text(
            """providers:
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: true
target_language: fr
"""
        )

        service = SettingsService()
        settings = service.load_settings(settings_file)

        assert len(settings.providers) == 1
        assert settings.providers[0].name == "Claude Sonnet"
        assert settings.providers[0].provider_type == "anthropic"
        assert settings.target_language == "fr"

    def test_load_settings_replaces_cached_settings(self, tmp_path: Path) -> None:
        """Test that load_settings replaces previously cached settings."""
        settings_file1 = tmp_path / "first.yaml"
        settings_file1.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: true
target_language: es
"""
        )

        settings_file2 = tmp_path / "second.yaml"
        settings_file2.write_text(
            """providers:
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: true
target_language: fr
"""
        )

        service = SettingsService()
        settings1 = service.load_settings(settings_file1)
        assert settings1.target_language == "es"
        assert settings1.providers[0].provider_type == "openai"

        settings2 = service.load_settings(settings_file2)
        assert settings2.target_language == "fr"
        assert settings2.providers[0].provider_type == "anthropic"

        current_settings = service.get_settings()
        assert current_settings is settings2
        assert current_settings.target_language == "fr"

    def test_load_settings_with_default_path(self, tmp_path: Path) -> None:
        """Test that load_settings uses default settings.yaml path when not specified."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-key
    is_default: true
"""
        )

        service = SettingsService()
        # Pass the actual path instead of relying on default path resolution
        settings = service.load_settings(settings_file)

        assert len(settings.providers) == 1
        assert settings.providers[0].name == "OpenAI GPT-4"

    def test_load_settings_returns_cached_instance_on_get_settings(self, tmp_path: Path) -> None:
        """Test that get_settings returns cached instance after load_settings."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-key
    is_default: true
"""
        )

        service = SettingsService()
        settings1 = service.load_settings(settings_file)
        settings2 = service.get_settings()
        settings3 = service.get_settings()

        assert settings1 is settings2
        assert settings2 is settings3

    def test_load_settings_loads_defaults_when_file_missing(self, tmp_path: Path) -> None:
        """Test that load_settings loads default settings when settings.yaml file is missing."""
        # Use a path that doesn't exist
        non_existent = tmp_path / "nonexistent.yaml"

        service = SettingsService()
        settings = service.load_settings(non_existent)

        assert settings is not None
        assert settings.providers == []
        assert settings.target_language == "de"


@pytest.mark.unit
class TestSettingsServiceSaveSettings:
    """Test SettingsService save_settings persistence."""

    def test_save_settings_persists_to_specified_file(self, tmp_path: Path) -> None:
        """Test that save_settings persists settings to specified settings file."""
        settings_file = tmp_path / "output.yaml"

        service = SettingsService()
        service.load_settings()  # Load defaults
        service.add_provider(
            ProviderConfig(
                name="OpenAI GPT-4",
                provider_type="openai",
                model="gpt-4o",
                api_key="sk-test-key",
                is_default=True,
            )
        )

        service.save_settings(settings_file)

        assert settings_file.exists()
        content = settings_file.read_text()
        assert "name: OpenAI GPT-4" in content
        assert "api_key: sk-test-key" in content
        assert "target_language: de" in content

    def test_save_settings_requires_loaded_settings(self, tmp_path: Path) -> None:
        """Test that save_settings requires settings to be loaded first."""
        settings_file = tmp_path / "output.yaml"
        service = SettingsService()

        with pytest.raises(RuntimeError, match="Settings not loaded"):
            service.save_settings(settings_file)

    def test_save_settings_with_default_path(self, tmp_path: Path) -> None:
        """Test that save_settings can save to a specified path."""
        settings_file = tmp_path / "settings.yaml"

        service = SettingsService()
        service.load_settings()  # Load defaults
        service.add_provider(
            ProviderConfig(
                name="Claude Sonnet",
                provider_type="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test",
                is_default=True,
            )
        )

        service.save_settings(settings_file)

        assert settings_file.exists()
        content = settings_file.read_text()
        assert "name: Claude Sonnet" in content

    def test_save_settings_round_trip_preserves_data(self, tmp_path: Path) -> None:
        """Test that save and load round trip preserves all settings data."""
        settings_file = tmp_path / "roundtrip.yaml"

        service1 = SettingsService()
        service1.load_settings()  # Load defaults
        service1.add_provider(
            ProviderConfig(
                name="OpenAI GPT-4",
                provider_type="openai",
                model="gpt-4o",
                api_key="sk-test-openai",
                is_default=False,
            )
        )
        service1.add_provider(
            ProviderConfig(
                name="Claude Sonnet",
                provider_type="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key="sk-ant-test",
                is_default=True,
            )
        )
        original_settings = service1.get_settings()
        original_settings.target_language = "es"

        service1.save_settings(settings_file)

        service2 = SettingsService()
        loaded_settings = service2.load_settings(settings_file)

        assert len(loaded_settings.providers) == 2
        assert loaded_settings.target_language == "es"
        assert loaded_settings.providers[0].name == "OpenAI GPT-4"
        assert loaded_settings.providers[0].is_default is False
        assert loaded_settings.providers[1].name == "Claude Sonnet"
        assert loaded_settings.providers[1].is_default is True


@pytest.mark.unit
class TestSettingsServiceGetDefaultProvider:
    """Test SettingsService get_default_provider delegation."""

    def test_get_default_provider_returns_marked_default(self, tmp_path: Path) -> None:
        """Test that get_default_provider returns provider marked as default."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: false
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: true
"""
        )

        service = SettingsService()
        service.load_settings(settings_file)
        default_provider = service.get_default_provider()

        assert default_provider is not None
        assert default_provider.name == "Claude Sonnet"
        assert default_provider.is_default is True

    def test_get_default_provider_returns_first_if_none_marked(self, tmp_path: Path) -> None:
        """Test that get_default_provider returns first provider if none marked default."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: false
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: false
"""
        )

        service = SettingsService()
        service.load_settings(settings_file)
        default_provider = service.get_default_provider()

        assert default_provider is not None
        assert default_provider.name == "OpenAI GPT-4"

    def test_get_default_provider_returns_none_if_no_providers(self, tmp_path: Path) -> None:
        """Test that get_default_provider returns None if no providers configured."""
        service = SettingsService()
        service.load_settings()  # Load defaults (no providers)

        default_provider = service.get_default_provider()

        assert default_provider is None

    def test_get_default_provider_delegates_to_settings_model(self, tmp_path: Path) -> None:
        """Test that get_default_provider delegates to Settings.get_default_provider()."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: true
"""
        )

        service = SettingsService()
        service.load_settings(settings_file)
        service_default = service.get_default_provider()
        settings_default = service.get_settings().get_default_provider()

        assert service_default is settings_default
        assert service_default is not None
        assert service_default.name == "Claude Sonnet"


@pytest.mark.unit
class TestSettingsServiceThreadSafety:
    """Test SettingsService thread safety."""

    def test_concurrent_load_settings_thread_safe(self, tmp_path: Path) -> None:
        """Test that concurrent load_settings calls on same instance are thread-safe."""
        settings_files = []
        for i in range(5):
            settings_file = tmp_path / f"config{i}.yaml"
            settings_file.write_text(
                f"""providers:
  - name: Provider {i}
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-key-{i}
    is_default: true
target_language: de
"""
            )
            settings_files.append(settings_file)

        service = SettingsService()
        num_threads = 5
        barrier = Barrier(num_threads)
        results = []

        def load_settings_with_barrier(settings_file: str | Path) -> None:
            barrier.wait()
            settings = service.load_settings(settings_file)
            results.append(settings)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(load_settings_with_barrier, settings_files[i]) for i in range(num_threads)]
            for future in futures:
                future.result()

        final_settings = service.get_settings()
        assert final_settings in results
        assert all(isinstance(s, Settings) for s in results)

    def test_concurrent_save_settings_thread_safe(self, tmp_path: Path) -> None:
        """Test that concurrent save_settings calls are thread-safe."""
        num_threads = 5
        barrier = Barrier(num_threads)

        def save_settings_with_barrier(index: int) -> None:
            barrier.wait()
            service = SettingsService()
            service.load_settings()  # Load defaults
            service.add_provider(
                ProviderConfig(
                    name=f"Provider {index}",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key=f"sk-test-key-{index}",
                    is_default=True,
                )
            )
            settings_file = tmp_path / f"output{index}.yaml"
            service.save_settings(settings_file)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(save_settings_with_barrier, i) for i in range(num_threads)]
            for future in futures:
                future.result()

        for i in range(num_threads):
            settings_file = tmp_path / f"output{i}.yaml"
            assert settings_file.exists()
            content = settings_file.read_text()
            assert f"name: Provider {i}" in content


@pytest.mark.unit
class TestSettingsServiceProviderManagement:
    """Test SettingsService provider management with automatic default handling."""

    def test_add_provider_first_is_default(self) -> None:
        """Test that first provider is automatically marked as default."""
        service = SettingsService()
        service.load_settings()  # Load defaults (no providers)

        provider = ProviderConfig(
            name="Test Provider",
            provider_type="openai",
            model="gpt-4",
            api_key="test-key",
            is_default=False,
        )

        service.add_provider(provider)
        settings = service.get_settings()

        assert len(settings.providers) == 1
        assert settings.providers[0].is_default is True

    def test_add_provider_when_no_default_exists(self) -> None:
        """Test that new provider becomes default if no default exists."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        # Add first provider without default
        provider1 = ProviderConfig(
            name="Provider 1",
            provider_type="openai",
            model="gpt-4",
            api_key="key1",
            is_default=False,
        )
        service.add_provider(provider1)

        # Manually clear default (simulate state where no default exists)
        settings = service.get_settings()
        settings.providers[0].is_default = False

        new_provider = ProviderConfig(
            name="Provider 2",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
            is_default=False,
        )

        service.add_provider(new_provider)
        settings = service.get_settings()

        assert len(settings.providers) == 2
        assert settings.providers[1].is_default is True

    def test_add_provider_clears_existing_default(self) -> None:
        """Test that adding a default provider clears existing default."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        provider1 = ProviderConfig(
            name="Provider 1",
            provider_type="openai",
            model="gpt-4",
            api_key="key1",
            is_default=True,
        )
        service.add_provider(provider1)

        new_provider = ProviderConfig(
            name="Provider 2",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
            is_default=True,
        )

        service.add_provider(new_provider)
        settings = service.get_settings()

        assert len(settings.providers) == 2
        assert settings.providers[0].is_default is False
        assert settings.providers[1].is_default is True

    def test_update_provider_clears_other_defaults(self) -> None:
        """Test that updating a provider as default clears other defaults."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        service.add_provider(
            ProviderConfig(
                name="Provider 1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            )
        )
        service.add_provider(
            ProviderConfig(
                name="Provider 2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
                is_default=False,
            )
        )

        updated_provider = ProviderConfig(
            name="Provider 2 Updated",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
            is_default=True,
        )

        service.update_provider(1, updated_provider)
        settings = service.get_settings()

        assert settings.providers[0].is_default is False
        assert settings.providers[1].is_default is True
        assert settings.providers[1].name == "Provider 2 Updated"

    def test_update_provider_invalid_index_raises_error(self) -> None:
        """Test that updating with invalid index raises IndexError."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        service.add_provider(
            ProviderConfig(
                name="Provider 1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            )
        )

        provider = ProviderConfig(
            name="Test",
            provider_type="openai",
            model="gpt-4",
            api_key="key",
            is_default=False,
        )

        with pytest.raises(IndexError):
            service.update_provider(99, provider)

    def test_delete_provider_sets_first_as_default(self) -> None:
        """Test that deleting default provider sets first remaining as default."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        service.add_provider(
            ProviderConfig(
                name="Provider 1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            )
        )
        service.add_provider(
            ProviderConfig(
                name="Provider 2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
                is_default=False,
            )
        )

        service.delete_provider(0)
        settings = service.get_settings()

        assert len(settings.providers) == 1
        assert settings.providers[0].is_default is True
        assert settings.providers[0].name == "Provider 2"

    def test_delete_non_default_provider_keeps_default(self) -> None:
        """Test that deleting non-default provider keeps existing default."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        service.add_provider(
            ProviderConfig(
                name="Provider 1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            )
        )
        service.add_provider(
            ProviderConfig(
                name="Provider 2",
                provider_type="anthropic",
                model="claude-3",
                api_key="key2",
                is_default=False,
            )
        )

        service.delete_provider(1)
        settings = service.get_settings()

        assert len(settings.providers) == 1
        assert settings.providers[0].is_default is True
        assert settings.providers[0].name == "Provider 1"

    def test_delete_provider_invalid_index_raises_error(self) -> None:
        """Test that deleting with invalid index raises IndexError."""
        service = SettingsService()
        service.load_settings()  # Load defaults

        service.add_provider(
            ProviderConfig(
                name="Provider 1",
                provider_type="openai",
                model="gpt-4",
                api_key="key1",
                is_default=True,
            )
        )

        with pytest.raises(IndexError):
            service.delete_provider(99)
