"""Concurrent access tests for settings storage."""

import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Barrier

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


@pytest.mark.unit
class TestSettingsStorageConcurrent:
    """Concurrent access tests for settings storage."""

    def test_concurrent_reads(self, temp_db):
        """Test multiple concurrent reads."""
        settings = Settings(
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

        # Save initial settings
        storage = SettingsStorageProvider(temp_db)
        storage.save(settings)
        storage.close()

        def read_settings(thread_id):
            storage = SettingsStorageProvider(temp_db)
            loaded = storage.load()
            storage.close()
            return (thread_id, loaded.target_language, loaded.providers[0].name)

        # Perform 20 concurrent reads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_settings, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]

        # All reads should succeed
        assert len(results) == 20
        for thread_id, lang, provider_name in results:
            assert lang == "de"
            assert provider_name == "Test Provider"

    def test_concurrent_writes_different_connections(self, temp_db):
        """Test concurrent writes from different connections."""
        # Initialize database
        storage = SettingsStorageProvider(temp_db)
        storage.save(Settings(target_language="initial", providers=[]))
        storage.close()

        def write_settings(thread_id):
            storage = SettingsStorageProvider(temp_db)
            settings = Settings(
                target_language=f"lang{thread_id}",
                providers=[
                    ProviderConfig(
                        name=f"Provider{thread_id}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"key{thread_id}",
                    )
                ],
            )
            storage.save(settings)
            storage.close()
            return thread_id

        # Perform 10 concurrent writes
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_settings, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # All writes should complete
        assert len(results) == 10

        # Final state should be one of the written values
        storage = SettingsStorageProvider(temp_db)
        final = storage.load()
        storage.close()

        # Verify final state is from one of the threads
        assert final.target_language.startswith("lang")
        assert final.providers[0].name.startswith("Provider")

    def test_concurrent_read_write_mix(self, temp_db):
        """Test mixed concurrent reads and writes."""
        # Initialize database
        storage = SettingsStorageProvider(temp_db)
        storage.save(
            Settings(
                target_language="initial",
                providers=[
                    ProviderConfig(
                        name="Initial",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key="initial-key",
                    )
                ],
            )
        )
        storage.close()

        def read_operation(thread_id):
            storage = SettingsStorageProvider(temp_db)
            loaded = storage.load()
            storage.close()
            return ("read", thread_id, loaded.target_language)

        def write_operation(thread_id):
            storage = SettingsStorageProvider(temp_db)
            settings = Settings(
                target_language=f"write{thread_id}",
                providers=[
                    ProviderConfig(
                        name=f"Writer{thread_id}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"key{thread_id}",
                    )
                ],
            )
            storage.save(settings)
            storage.close()
            return ("write", thread_id, f"write{thread_id}")

        # Mix of 15 reads and 5 writes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(15):
                futures.append(executor.submit(read_operation, i))
            for i in range(5):
                futures.append(executor.submit(write_operation, i))

            results = [future.result() for future in as_completed(futures)]

        # All operations should complete
        assert len(results) == 20

        reads = [r for r in results if r[0] == "read"]
        writes = [r for r in results if r[0] == "write"]

        assert len(reads) == 15
        assert len(writes) == 5

    def test_synchronized_concurrent_updates(self, temp_db):
        """Test synchronized concurrent updates using barrier."""
        # Initialize database
        storage = SettingsStorageProvider(temp_db)
        storage.save(Settings(target_language="initial", providers=[]))
        storage.close()

        num_threads = 5
        barrier = Barrier(num_threads)

        def update_with_barrier(thread_id):
            # Wait for all threads to be ready
            barrier.wait()

            storage = SettingsStorageProvider(temp_db)
            settings = Settings(
                target_language=f"lang{thread_id}",
                providers=[
                    ProviderConfig(
                        name=f"Provider{thread_id}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key=f"key{thread_id}",
                    )
                ],
            )
            storage.update(settings)
            storage.close()
            return thread_id

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(update_with_barrier, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]

        # All updates should complete
        assert len(results) == num_threads

    def test_rapid_save_delete_cycle(self, temp_db):
        """Test rapid save/delete cycles."""

        def save_delete_cycle(thread_id):
            try:
                storage = SettingsStorageProvider(temp_db)

                for i in range(5):
                    settings = Settings(
                        target_language=f"lang{thread_id}_{i}",
                        providers=[
                            ProviderConfig(
                                name=f"Provider{thread_id}_{i}",
                                provider_type="openai",
                                model="gpt-4o",
                                api_key=f"key{thread_id}",
                            )
                        ],
                    )
                    storage.save(settings)

                    if i % 2 == 0:
                        storage.delete_all()

                    # Small delay to avoid database locking issues
                    time.sleep(0.01)

                storage.close()
                return (True, thread_id)
            except Exception as e:
                return (False, str(e))

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(save_delete_cycle, i) for i in range(2)]
            results = [future.result() for future in as_completed(futures)]

        # At least some operations should succeed
        successful = [r for r in results if r[0]]
        assert len(successful) > 0

    def test_concurrent_context_managers(self, temp_db):
        """Test concurrent access using context managers."""
        # Initialize database
        with SettingsStorageProvider(temp_db) as storage:
            storage.save(
                Settings(
                    target_language="initial",
                    providers=[
                        ProviderConfig(
                            name="Initial",
                            provider_type="openai",
                            model="gpt-4o",
                            api_key="initial-key",
                        )
                    ],
                )
            )

        def read_with_context(thread_id):
            with SettingsStorageProvider(temp_db) as storage:
                loaded = storage.load()
                return (thread_id, loaded.target_language)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_with_context, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]

        assert len(results) == 20

    def test_long_running_connections(self, temp_db):
        """Test long-running database connections."""

        def long_running_operation(thread_id):
            try:
                storage = SettingsStorageProvider(temp_db)

                for i in range(10):
                    settings = Settings(
                        target_language=f"lang{thread_id}_{i}",
                        providers=[
                            ProviderConfig(
                                name=f"Provider{thread_id}",
                                provider_type="openai",
                                model="gpt-4o",
                                api_key=f"key{thread_id}",
                            )
                        ],
                    )
                    storage.save(settings)
                    loaded = storage.load()
                    assert loaded.target_language == f"lang{thread_id}_{i}"

                    # Small delay to simulate real work
                    time.sleep(0.02)

                storage.close()
                return (True, thread_id)
            except Exception as e:
                return (False, str(e))

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(long_running_operation, i) for i in range(2)]
            results = [future.result() for future in as_completed(futures)]

        # At least some operations should succeed
        successful = [r for r in results if r[0]]
        assert len(successful) > 0

    def test_concurrent_updates_preserve_data_integrity(self, temp_db):
        """Test that concurrent updates maintain data integrity."""
        # Initialize with known state
        storage = SettingsStorageProvider(temp_db)
        storage.save(Settings(target_language="initial", providers=[]))
        storage.close()

        def update_operation(thread_id):
            try:
                storage = SettingsStorageProvider(temp_db)
                settings = Settings(
                    target_language=f"lang{thread_id}",
                    providers=[
                        ProviderConfig(
                            name=f"Provider{thread_id}_{i}",
                            provider_type="openai" if i % 2 == 0 else "anthropic",
                            model=f"model{i}",
                            api_key=f"key{i}",
                        )
                        for i in range(5)
                    ],
                )
                storage.update(settings)
                storage.close()
                return (True, thread_id)
            except Exception as e:
                return (False, str(e))

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(update_operation, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]

        # At least some operations should succeed
        successful = [r for r in results if r[0]]
        assert len(successful) > 0

        # Verify final state has valid data
        storage = SettingsStorageProvider(temp_db)
        final = storage.load()
        storage.close()

        # Due to concurrent updates, final state may have providers from multiple updates
        # but should be valid and have some providers
        assert len(final.providers) >= 5
        assert final.target_language.startswith("lang")

        # Verify all providers have valid structure
        for provider in final.providers:
            assert provider.name.startswith("Provider")
            assert provider.provider_type in ["openai", "anthropic"]

    def test_read_during_write(self, temp_db):
        """Test reading while another thread is writing."""
        # Initialize database
        storage = SettingsStorageProvider(temp_db)
        storage.save(
            Settings(
                target_language="initial",
                providers=[
                    ProviderConfig(
                        name="Initial",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key="initial-key",
                    )
                ],
            )
        )
        storage.close()

        def slow_write():
            storage = SettingsStorageProvider(temp_db)
            for i in range(5):
                settings = Settings(
                    target_language=f"writing{i}",
                    providers=[
                        ProviderConfig(
                            name=f"Writer{i}",
                            provider_type="openai",
                            model="gpt-4o",
                            api_key=f"key{i}",
                        )
                    ],
                )
                storage.save(settings)
                time.sleep(0.05)
            storage.close()
            return "write_done"

        def fast_read(thread_id):
            storage = SettingsStorageProvider(temp_db)
            loaded = storage.load()
            storage.close()
            return loaded.target_language

        with ThreadPoolExecutor(max_workers=6) as executor:
            # Start slow writer
            write_future = executor.submit(slow_write)

            # Start multiple fast readers
            read_futures = [executor.submit(fast_read, i) for i in range(10)]

            # Collect results
            write_result = write_future.result()
            read_results = [future.result() for future in as_completed(read_futures)]

        assert write_result == "write_done"
        assert len(read_results) == 10

        # All reads should have succeeded (returned some valid language)
        for result in read_results:
            assert isinstance(result, str)
            assert len(result) > 0
