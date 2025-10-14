"""Unit tests for SettingsService singleton and orchestration.

Tests singleton pattern, lazy loading, thread safety, and delegation
to Settings model for business logic.
"""

from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService


@pytest.fixture(autouse=True)
def reset_singleton() -> Generator[None, None, None]:
    """Reset SettingsService singleton state before each test.

    Ensures test isolation by clearing singleton instance and settings cache.
    This fixture runs automatically before each test in this module.
    """
    SettingsService._instance = None
    SettingsService._settings = None
    SettingsService._current_provider = None
    yield
    SettingsService._instance = None
    SettingsService._settings = None
    SettingsService._current_provider = None


@pytest.mark.unit
class TestSettingsServiceSingleton:
    """Test SettingsService singleton pattern implementation."""

    def test_get_instance_returns_same_instance_on_multiple_calls(self) -> None:
        """Test that get_instance returns the same instance on multiple calls."""
        instance1 = SettingsService.get_instance()
        instance2 = SettingsService.get_instance()
        instance3 = SettingsService.get_instance()

        assert instance1 is instance2
        assert instance2 is instance3
        assert instance1 is instance3

    def test_direct_instantiation_raises_runtime_error(self) -> None:
        """Test that direct instantiation raises RuntimeError after singleton created."""
        SettingsService.get_instance()

        with pytest.raises(RuntimeError, match="Use get_instance\\(\\) to get singleton instance"):
            SettingsService()

    def test_singleton_persists_across_method_calls(self) -> None:
        """Test that singleton instance persists across different method calls."""
        service = SettingsService.get_instance()
        settings = SettingsService.get_settings()

        service2 = SettingsService.get_instance()

        assert service is service2
        assert settings is SettingsService.get_settings()


@pytest.mark.unit
class TestSettingsServiceLazyLoading:
    """Test SettingsService lazy loading behavior."""

    def test_get_settings_loads_on_first_access(self, tmp_path: Path) -> None:
        """Test that get_settings loads settings on first access."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-key
    is_default: true
target_language: es
"""
        )

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            SettingsService.load_settings()
            settings = SettingsService.get_settings()

            assert settings is not None
            assert len(settings.providers) == 1
            assert settings.target_language == "es"
            assert SettingsService.get_current_provider() is not None
        finally:
            os.chdir(original_cwd)

    def test_get_settings_returns_cached_instance_on_subsequent_calls(self, tmp_path: Path) -> None:
        """Test that get_settings returns cached instance on subsequent calls."""
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

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            settings1 = SettingsService.get_settings()
            settings2 = SettingsService.get_settings()
            settings3 = SettingsService.get_settings()

            assert settings1 is settings2
            assert settings2 is settings3
            assert SettingsService.get_current_provider() is not None
        finally:
            os.chdir(original_cwd)

    def test_get_settings_loads_defaults_when_settings_file_missing(self, tmp_path: Path) -> None:
        """Test that get_settings loads default settings when settings.yaml file is missing."""
        import os

        original_cwd = os.getcwd()
        try:
            # Change to temp directory where no settings.yaml exists
            os.chdir(tmp_path)
            # Reset cached settings to force reload
            SettingsService._settings = None
            SettingsService._current_provider = None

            settings = SettingsService.get_settings()

            assert settings is not None
            assert settings.providers == []
            assert settings.target_language == "de"
            assert SettingsService.get_current_provider() is None
        finally:
            os.chdir(original_cwd)
            # Reset again to avoid affecting other tests
            SettingsService._settings = None
            SettingsService._current_provider = None


@pytest.mark.unit
class TestSettingsServiceLoadSettings:
    """Test SettingsService load_settings explicit loading."""

    def test_load_settings_loads_from_specified_file(self, tmp_path: Path) -> None:
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

        settings = SettingsService.load_settings(settings_file)

        assert len(settings.providers) == 1
        assert settings.providers[0].name == "Claude Sonnet"
        assert settings.providers[0].provider_type == "anthropic"
        assert settings.target_language == "fr"
        assert SettingsService.get_current_provider() == settings.providers[0]

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

        settings1 = SettingsService.load_settings(settings_file1)
        assert settings1.target_language == "es"
        assert settings1.providers[0].provider_type == "openai"
        assert SettingsService.get_current_provider() == settings1.providers[0]

        settings2 = SettingsService.load_settings(settings_file2)
        assert settings2.target_language == "fr"
        assert settings2.providers[0].provider_type == "anthropic"

        current_settings = SettingsService.get_settings()
        assert current_settings is settings2
        assert current_settings.target_language == "fr"
        assert SettingsService.get_current_provider() == settings2.providers[0]

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

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            settings = SettingsService.load_settings()

            assert len(settings.providers) == 1
            assert settings.providers[0].name == "OpenAI GPT-4"
            assert SettingsService.get_current_provider() == settings.providers[0]
        finally:
            os.chdir(original_cwd)


@pytest.mark.unit
class TestSettingsServiceSaveSettings:
    """Test SettingsService save_settings persistence."""

    def test_save_settings_persists_to_specified_file(self, tmp_path: Path) -> None:
        """Test that save_settings persists settings to specified settings file."""
        settings_file = tmp_path / "output.yaml"

        settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-key",
                    is_default=True,
                )
            ],
            target_language="de",
        )

        SettingsService.save_settings(settings, settings_file)

        assert settings_file.exists()
        content = settings_file.read_text()
        assert "name: OpenAI GPT-4" in content
        assert "api_key: sk-test-key" in content
        assert "target_language: de" in content

    def test_save_settings_updates_cached_settings(self, tmp_path: Path) -> None:
        """Test that save_settings updates the cached settings instance."""
        settings_file = tmp_path / "output.yaml"

        original_settings = Settings(
            providers=[
                ProviderConfig(
                    name="OpenAI GPT-4",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="sk-test-openai",
                    is_default=True,
                )
            ],
            target_language="es",
        )

        SettingsService.save_settings(original_settings, settings_file)

        cached_settings = SettingsService.get_settings()

        assert cached_settings is original_settings
        assert cached_settings.target_language == "es"
        assert cached_settings.providers[0].api_key == "sk-test-openai"

    def test_save_settings_with_default_path(self, tmp_path: Path) -> None:
        """Test that save_settings uses default settings.yaml path when not specified."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            settings = Settings(
                providers=[
                    ProviderConfig(
                        name="Claude Sonnet",
                        provider_type="anthropic",
                        model="claude-3-5-sonnet-20241022",
                        api_key="sk-ant-test",
                        is_default=True,
                    )
                ],
                target_language="fr",
            )

            SettingsService.save_settings(settings)

            settings_file = tmp_path / "settings.yaml"
            assert settings_file.exists()
            content = settings_file.read_text()
            assert "name: Claude Sonnet" in content
        finally:
            os.chdir(original_cwd)

    def test_save_settings_round_trip_preserves_data(self, tmp_path: Path) -> None:
        """Test that save and load round trip preserves all settings data."""
        settings_file = tmp_path / "roundtrip.yaml"

        original_settings = Settings(
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
            target_language="es",
        )

        SettingsService.save_settings(original_settings, settings_file)
        loaded_settings = SettingsService.load_settings(settings_file)

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

        SettingsService.load_settings(settings_file)
        default_provider = SettingsService.get_default_provider()

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

        SettingsService.load_settings(settings_file)
        default_provider = SettingsService.get_default_provider()

        assert default_provider is not None
        assert default_provider.name == "OpenAI GPT-4"

    def test_get_default_provider_returns_none_if_no_providers(self) -> None:
        """Test that get_default_provider returns None if no providers configured."""
        settings = Settings(providers=[], target_language="de")
        SettingsService.save_settings(settings, Path("settings.yaml"))

        default_provider = SettingsService.get_default_provider()

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

        SettingsService.load_settings(settings_file)
        service_default = SettingsService.get_default_provider()
        settings_default = SettingsService.get_settings().get_default_provider()

        assert service_default is settings_default
        assert service_default is not None
        assert service_default.name == "Claude Sonnet"


@pytest.mark.unit
class TestSettingsServiceCurrentProvider:
    """Test SettingsService current provider management."""

    def test_get_current_provider_returns_current_provider(self, tmp_path: Path) -> None:
        """Test that get_current_provider returns current provider."""
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

        SettingsService.load_settings(settings_file)
        current_provider = SettingsService.get_current_provider()

        assert current_provider is not None
        assert current_provider.name == "OpenAI GPT-4"

    def test_get_current_provider_auto_initializes_to_default(self, tmp_path: Path) -> None:
        """Test that get_current_provider auto-initializes to default provider."""
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

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            SettingsService.get_settings()
            current_provider = SettingsService.get_current_provider()

            assert current_provider is not None
            assert current_provider.name == "Claude Sonnet"
            assert current_provider == SettingsService.get_default_provider()
        finally:
            os.chdir(original_cwd)

    def test_set_current_provider_sets_the_current_provider(self, tmp_path: Path) -> None:
        """Test that set_current_provider sets the current provider."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: true
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: false
"""
        )

        SettingsService.load_settings(settings_file)
        initial_provider = SettingsService.get_current_provider()
        assert initial_provider
        assert initial_provider.name == "OpenAI GPT-4"

        claude_provider = SettingsService.get_settings().providers[1]
        SettingsService.set_current_provider(claude_provider)
        current_provider = SettingsService.get_current_provider()

        assert current_provider
        assert current_provider.name == "Claude Sonnet"
        assert current_provider == claude_provider

    def test_set_current_provider_doesnt_persist_to_file(self, tmp_path: Path) -> None:
        """Test that set_current_provider doesn't persist to file."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: true
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: false
"""
        )

        SettingsService.load_settings(settings_file)
        claude_provider = SettingsService.get_settings().providers[1]
        SettingsService.set_current_provider(claude_provider)

        SettingsService._settings = None
        SettingsService._current_provider = None
        reloaded_settings = SettingsService.load_settings(settings_file)
        assert reloaded_settings
        current_provider = SettingsService.get_current_provider()
        assert current_provider
        assert current_provider.name == "OpenAI GPT-4"

    def test_reset_current_provider_resets_to_default(self, tmp_path: Path) -> None:
        """Test that reset_current_provider resets to default provider."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: true
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: false
"""
        )

        SettingsService.load_settings(settings_file)
        claude_provider = SettingsService.get_settings().providers[1]
        SettingsService.set_current_provider(claude_provider)
        current_provider = SettingsService.get_current_provider()
        assert current_provider
        assert current_provider.name == "Claude Sonnet"

        SettingsService.reset_current_provider()
        current_provider = SettingsService.get_current_provider()

        assert current_provider
        assert current_provider.name == "OpenAI GPT-4"
        assert current_provider == SettingsService.get_default_provider()

    def test_current_provider_persists_across_get_settings_calls(self, tmp_path: Path) -> None:
        """Test that current provider persists across get_settings() calls."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            """providers:
  - name: OpenAI GPT-4
    provider_type: openai
    model: gpt-4o
    api_key: sk-test-openai
    is_default: true
  - name: Claude Sonnet
    provider_type: anthropic
    model: claude-3-5-sonnet-20241022
    api_key: sk-ant-test
    is_default: false
"""
        )

        SettingsService.load_settings(settings_file)
        claude_provider = SettingsService.get_settings().providers[1]
        SettingsService.set_current_provider(claude_provider)

        SettingsService.get_settings()
        SettingsService.get_settings()
        current_provider = SettingsService.get_current_provider()

        assert current_provider
        assert current_provider.name == "Claude Sonnet"
        assert current_provider == claude_provider


@pytest.mark.unit
class TestSettingsServiceThreadSafety:
    """Test SettingsService thread safety."""

    def test_concurrent_get_instance_returns_same_singleton(self) -> None:
        """Test that concurrent get_instance calls return the same singleton instance."""
        num_threads = 10
        barrier = Barrier(num_threads)
        instances = []

        def get_instance_with_barrier() -> None:
            barrier.wait()
            instance = SettingsService.get_instance()
            instances.append(instance)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(get_instance_with_barrier) for _ in range(num_threads)]
            for future in futures:
                future.result()

        assert len(instances) == num_threads
        assert all(instance is instances[0] for instance in instances)

    def test_concurrent_get_settings_returns_same_instance(self, tmp_path: Path) -> None:
        """Test that concurrent get_settings calls return the same settings instance."""
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

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            num_threads = 10
            barrier = Barrier(num_threads)
            settings_list = []

            def get_settings_with_barrier() -> None:
                barrier.wait()
                settings = SettingsService.get_settings()
                settings_list.append(settings)

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(get_settings_with_barrier) for _ in range(num_threads)]
                for future in futures:
                    future.result()

            assert len(settings_list) == num_threads
            assert all(settings is settings_list[0] for settings in settings_list)
        finally:
            os.chdir(original_cwd)

    def test_concurrent_load_settings_thread_safe(self, tmp_path: Path) -> None:
        """Test that concurrent load_settings calls are thread-safe."""
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

        num_threads = 5
        barrier = Barrier(num_threads)
        results = []

        def load_settings_with_barrier(settings_file: str | Path) -> None:
            barrier.wait()
            settings = SettingsService.load_settings(settings_file)
            results.append(settings)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(load_settings_with_barrier, settings_files[i]) for i in range(num_threads)]
            for future in futures:
                future.result()

        final_settings = SettingsService.get_settings()
        assert final_settings in results
        assert all(isinstance(s, Settings) for s in results)

    def test_concurrent_save_settings_thread_safe(self, tmp_path: Path) -> None:
        """Test that concurrent save_settings calls are thread-safe."""
        num_threads = 5
        barrier = Barrier(num_threads)

        def save_settings_with_barrier(index: int) -> None:
            barrier.wait()
            settings = Settings(
                providers=[
                    ProviderConfig(
                        name=f"Provider {index}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"sk-test-key-{index}",
                        is_default=True,
                    )
                ],
                target_language="de",
            )
            settings_file = tmp_path / f"output{index}.yaml"
            SettingsService.save_settings(settings, settings_file)

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
        settings = Settings(providers=[], target_language="de")
        provider = ProviderConfig(
            name="Test Provider",
            provider_type="openai",
            model="gpt-4",
            api_key="test-key",
            is_default=False,
        )

        SettingsService.add_provider(settings, provider)

        assert len(settings.providers) == 1
        assert settings.providers[0].is_default is True

    def test_add_provider_when_no_default_exists(self) -> None:
        """Test that new provider becomes default if no default exists."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=False,
                )
            ],
            target_language="de",
        )

        new_provider = ProviderConfig(
            name="Provider 2",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
            is_default=False,
        )

        SettingsService.add_provider(settings, new_provider)

        assert len(settings.providers) == 2
        assert settings.providers[1].is_default is True

    def test_add_provider_clears_existing_default(self) -> None:
        """Test that adding a default provider clears existing default."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=True,
                )
            ],
            target_language="de",
        )

        new_provider = ProviderConfig(
            name="Provider 2",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
            is_default=True,
        )

        SettingsService.add_provider(settings, new_provider)

        assert len(settings.providers) == 2
        assert settings.providers[0].is_default is False
        assert settings.providers[1].is_default is True

    def test_update_provider_clears_other_defaults(self) -> None:
        """Test that updating a provider as default clears other defaults."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Provider 2",
                    provider_type="anthropic",
                    model="claude-3",
                    api_key="key2",
                    is_default=False,
                ),
            ],
            target_language="de",
        )

        updated_provider = ProviderConfig(
            name="Provider 2 Updated",
            provider_type="anthropic",
            model="claude-3",
            api_key="key2",
            is_default=True,
        )

        SettingsService.update_provider(settings, 1, updated_provider)

        assert settings.providers[0].is_default is False
        assert settings.providers[1].is_default is True
        assert settings.providers[1].name == "Provider 2 Updated"

    def test_update_provider_invalid_index_raises_error(self) -> None:
        """Test that updating with invalid index raises IndexError."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=True,
                )
            ],
            target_language="de",
        )

        provider = ProviderConfig(
            name="Test",
            provider_type="openai",
            model="gpt-4",
            api_key="key",
            is_default=False,
        )

        with pytest.raises(IndexError):
            SettingsService.update_provider(settings, 99, provider)

    def test_delete_provider_sets_first_as_default(self) -> None:
        """Test that deleting default provider sets first remaining as default."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Provider 2",
                    provider_type="anthropic",
                    model="claude-3",
                    api_key="key2",
                    is_default=False,
                ),
            ],
            target_language="de",
        )

        SettingsService.delete_provider(settings, 0)

        assert len(settings.providers) == 1
        assert settings.providers[0].is_default is True
        assert settings.providers[0].name == "Provider 2"

    def test_delete_non_default_provider_keeps_default(self) -> None:
        """Test that deleting non-default provider keeps existing default."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=True,
                ),
                ProviderConfig(
                    name="Provider 2",
                    provider_type="anthropic",
                    model="claude-3",
                    api_key="key2",
                    is_default=False,
                ),
            ],
            target_language="de",
        )

        SettingsService.delete_provider(settings, 1)

        assert len(settings.providers) == 1
        assert settings.providers[0].is_default is True
        assert settings.providers[0].name == "Provider 1"

    def test_delete_provider_invalid_index_raises_error(self) -> None:
        """Test that deleting with invalid index raises IndexError."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Provider 1",
                    provider_type="openai",
                    model="gpt-4",
                    api_key="key1",
                    is_default=True,
                )
            ],
            target_language="de",
        )

        with pytest.raises(IndexError):
            SettingsService.delete_provider(settings, 99)
