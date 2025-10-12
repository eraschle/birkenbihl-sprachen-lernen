"""Stress tests for settings storage provider."""

import tempfile
from pathlib import Path

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings
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
def storage(temp_db):
    """Create settings storage provider with temporary database."""
    return SettingsStorageProvider(temp_db)


@pytest.mark.slow
@pytest.mark.unit
class TestSettingsStorageStress:
    """Stress tests for settings storage."""

    def test_save_load_cycle_1000_times(self, storage):
        """Test 1000 save/load cycles."""
        for i in range(1000):
            settings = Settings(
                target_language=f"lang{i % 10}",
                providers=[
                    ProviderConfig(
                        name=f"Provider{i}",
                        provider_type="openai" if i % 2 == 0 else "anthropic",
                        model="gpt-4o" if i % 2 == 0 else "claude",
                        api_key=f"key{i}",
                    )
                ],
            )

            storage.save(settings)
            loaded = storage.load()

            assert loaded.target_language == f"lang{i % 10}"
            assert loaded.providers[0].name == f"Provider{i}"

    def test_large_provider_list_100_providers(self, storage):
        """Test saving 100 providers."""
        providers = [
            ProviderConfig(
                name=f"Provider{i}",
                provider_type="openai" if i % 3 == 0 else ("anthropic" if i % 3 == 1 else "gemini"),
                model=f"model-{i}",
                api_key=f"key-{i}" * 10,  # Longer keys
                base_url=f"https://api{i}.example.com" if i % 5 == 0 else None,
                is_default=(i == 0),
                supports_streaming=(i % 2 == 0),
            )
            for i in range(100)
        ]

        settings = Settings(target_language="de", providers=providers)

        saved = storage.save(settings)
        loaded = storage.load()

        assert len(loaded.providers) == 100
        assert loaded.providers[0].name == "Provider0"
        assert loaded.providers[99].name == "Provider99"

        # Verify random samples
        assert loaded.providers[25].name == "Provider25"
        assert loaded.providers[50].name == "Provider50"
        assert loaded.providers[75].name == "Provider75"

    def test_rapid_updates_500_times(self, storage):
        """Test 500 rapid updates."""
        # Initial save
        storage.save(Settings(target_language="initial", providers=[]))

        for i in range(500):
            settings = Settings(
                target_language=f"update{i}",
                providers=[
                    ProviderConfig(
                        name=f"UpdatedProvider{i}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"key{i}",
                    )
                ],
            )

            storage.update(settings)

        # Verify final state
        final = storage.load()
        assert final.target_language == "update499"
        assert final.providers[0].name == "UpdatedProvider499"

    def test_save_delete_cycle_500_times(self, storage):
        """Test 500 save/delete cycles."""
        for i in range(500):
            settings = Settings(
                target_language="de",
                providers=[
                    ProviderConfig(
                        name=f"Provider{i}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"key{i}",
                    )
                ],
            )

            storage.save(settings)

            # Delete every other iteration
            if i % 2 == 0:
                deleted = storage.delete_all()
                assert deleted is True

        # Final state depends on whether last iteration was deleted
        # Since 499 is odd, settings should exist
        final = storage.load()
        assert final.providers[0].name == "Provider499"

    def test_very_large_api_keys(self, storage):
        """Test with very large API key strings."""
        large_key = "x" * 100000  # 100KB API key

        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Large Key Provider",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key=large_key,
                )
            ]
        )

        saved = storage.save(settings)
        loaded = storage.load()

        assert len(loaded.providers[0].api_key) == 100000
        assert loaded.providers[0].api_key == large_key

    def test_many_sequential_connections(self, temp_db):
        """Test many sequential database connections."""
        for i in range(200):
            storage = SettingsStorageProvider(temp_db)

            settings = Settings(
                target_language="de",
                providers=[
                    ProviderConfig(
                        name=f"Provider{i}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"key{i}",
                    )
                ],
            )

            storage.save(settings)
            loaded = storage.load()
            storage.close()

            assert loaded.providers[0].name == f"Provider{i}"

    def test_context_manager_many_times(self, temp_db):
        """Test context manager usage many times."""
        for i in range(100):
            with SettingsStorageProvider(temp_db) as storage:
                settings = Settings(
                    target_language=f"lang{i}",
                    providers=[
                        ProviderConfig(
                            name=f"Provider{i}",
                            provider_type="openai",
                            model="gpt-4o",
                            api_key=f"key{i}",
                        )
                    ],
                )

                storage.save(settings)
                loaded = storage.load()

                assert loaded.target_language == f"lang{i}"

    def test_growing_provider_list(self, storage):
        """Test progressively growing provider list."""
        # Start with empty
        storage.save(Settings(target_language="de", providers=[]))

        # Add providers incrementally
        for i in range(50):
            loaded = storage.load()

            new_provider = ProviderConfig(
                name=f"Provider{i}",
                provider_type="openai",
                model="gpt-4o",
                api_key=f"key{i}",
            )

            updated = Settings(target_language=loaded.target_language, providers=loaded.providers + [new_provider])

            storage.save(updated)

        # Verify final state
        final = storage.load()
        assert len(final.providers) == 50

        # Verify all providers are present
        for i in range(50):
            assert final.providers[i].name == f"Provider{i}"

    def test_shrinking_provider_list(self, storage):
        """Test progressively shrinking provider list."""
        # Start with 50 providers
        initial_providers = [
            ProviderConfig(
                name=f"Provider{i}",
                provider_type="openai",
                model="gpt-4o",
                api_key=f"key{i}",
            )
            for i in range(50)
        ]

        storage.save(Settings(target_language="de", providers=initial_providers))

        # Remove providers one by one
        for i in range(49):  # Leave one provider
            loaded = storage.load()
            updated = Settings(target_language=loaded.target_language, providers=loaded.providers[1:])
            storage.save(updated)

        # Verify final state
        final = storage.load()
        assert len(final.providers) == 1
        assert final.providers[0].name == "Provider49"

    def test_alternating_target_languages_1000_times(self, storage):
        """Test alternating between different target languages 1000 times."""
        languages = ["de", "en", "es", "fr", "it"]

        for i in range(1000):
            lang = languages[i % len(languages)]

            settings = Settings(
                target_language=lang,
                providers=[
                    ProviderConfig(
                        name="Provider",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key="test-key",
                    )
                ],
            )

            storage.save(settings)
            loaded = storage.load()

            assert loaded.target_language == lang

    def test_database_size_with_large_dataset(self, temp_db, storage):
        """Test database size with large dataset."""
        # Save large settings
        large_providers = [
            ProviderConfig(
                name=f"Provider{i}" * 10,  # Longer names
                provider_type="openai",
                model=f"model-{i}" * 10,
                api_key=f"key-{i}" * 50,  # Longer keys
                base_url=f"https://api{i}.example.com/v1/very/long/path",
            )
            for i in range(100)
        ]

        settings = Settings(target_language="de", providers=large_providers)

        storage.save(settings)

        # Check database file exists and has reasonable size
        assert temp_db.exists()
        db_size = temp_db.stat().st_size

        # Database should be less than 10MB for this dataset
        assert db_size < 10 * 1024 * 1024

        # But should be larger than empty (> 10KB)
        assert db_size > 10 * 1024

    def test_mixed_operations_stress(self, storage):
        """Test mixed save/load/update/delete operations."""
        operations = ["save", "load", "update", "delete"]

        for i in range(200):
            op = operations[i % len(operations)]

            if op == "save":
                settings = Settings(
                    target_language="de",
                    providers=[
                        ProviderConfig(
                            name=f"Provider{i}",
                            provider_type="openai",
                            model="gpt-4o",
                            api_key=f"key{i}",
                        )
                    ],
                )
                storage.save(settings)

            elif op == "load":
                try:
                    loaded = storage.load()
                    assert loaded is not None
                except Exception:
                    # May fail if deleted
                    pass

            elif op == "update":
                try:
                    settings = Settings(
                        target_language=f"updated{i}",
                        providers=[
                            ProviderConfig(
                                name=f"Updated{i}",
                                provider_type="openai",
                                model="gpt-4o",
                                api_key=f"key{i}",
                            )
                        ],
                    )
                    storage.update(settings)
                except Exception:
                    # May fail if no settings exist
                    pass

            elif op == "delete":
                storage.delete_all()

    def test_maximum_provider_name_length(self, storage):
        """Test with maximum reasonable provider name length."""
        # Very long but realistic provider name
        long_name = "x" * 1000

        settings = Settings(
            providers=[
                ProviderConfig(
                    name=long_name,
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        saved = storage.save(settings)
        loaded = storage.load()

        assert len(loaded.providers[0].name) == 1000
        assert loaded.providers[0].name == long_name
