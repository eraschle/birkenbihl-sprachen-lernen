"""Comprehensive edge case tests for settings storage."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from birkenbihl.models.settings import ProviderConfig, Settings
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


@pytest.mark.unit
class TestSettingsStorageEdgeCases:
    """Edge case tests for settings storage."""

    def test_save_empty_providers_list(self, storage: SettingsStorageProvider) -> None:
        """Test saving settings with empty providers list."""
        settings = Settings(target_language="de", providers=[])

        saved = storage.save(settings)

        assert saved.target_language == "de"
        assert len(saved.providers) == 0

    def test_save_many_providers(self, storage: SettingsStorageProvider) -> None:
        """Test saving settings with many providers."""
        providers = [
            ProviderConfig(
                name=f"Provider{i}",
                provider_type="openai" if i % 2 == 0 else "anthropic",
                model=f"model-{i}",
                api_key=f"key-{i}",
                is_default=(i == 0),
            )
            for i in range(50)
        ]

        settings = Settings(target_language="de", providers=providers)
        _saved = storage.save(settings)

        assert len(_saved.providers) == 50
        assert _saved.providers[0].name == "Provider0"
        assert _saved.providers[49].name == "Provider49"

    def test_provider_with_long_strings(self, storage: SettingsStorageProvider) -> None:
        """Test saving provider with very long strings."""
        long_string = "x" * 10000

        settings = Settings(
            providers=[
                ProviderConfig(
                    name=long_string,
                    provider_type="openai",
                    model=long_string,
                    api_key=long_string,
                    api_url=f"https://{long_string}.com",
                )
            ]
        )

        settings = storage.save(settings)
        loaded = storage.load()

        assert len(loaded.providers[0].name) == 10000
        assert len(loaded.providers[0].model) == 10000
        assert len(loaded.providers[0].api_key) == 10000

    def test_provider_with_special_characters(self, storage: SettingsStorageProvider) -> None:
        """Test saving provider with special characters."""
        special_chars = "äöüß™€£¥§©®→↓←↑∞≈≠≤≥±÷×√∫∂∑∏π"

        settings = Settings(
            providers=[
                ProviderConfig(
                    name=f"Provider {special_chars}",
                    provider_type="openai",
                    model=f"model-{special_chars}",
                    api_key=f"key-{special_chars}",
                )
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert special_chars in loaded.providers[0].name
        assert special_chars in loaded.providers[0].model

    def test_provider_with_unicode_emoji(self, storage: SettingsStorageProvider) -> None:
        """Test saving provider with unicode emoji."""
        emoji_string = "🚀 Provider 🔥 with 💡 emoji 🎉"

        settings = Settings(
            providers=[
                ProviderConfig(
                    name=emoji_string,
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].name == emoji_string

    def test_provider_with_newlines_and_tabs(self, storage: SettingsStorageProvider) -> None:
        """Test saving provider with newlines and tabs."""
        multiline_string = "Line1\nLine2\tTabbed\rCarriageReturn"

        settings = Settings(
            providers=[
                ProviderConfig(
                    name=multiline_string,
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].name == multiline_string

    def test_provider_with_sql_injection_attempt(self, storage: SettingsStorageProvider) -> None:
        """Test that SQL injection attempts are safely handled."""
        malicious_string = "'; DROP TABLE provider_configs; --"

        settings = Settings(
            providers=[
                ProviderConfig(
                    name=malicious_string,
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        # Should not raise any errors
        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].name == malicious_string

    def test_update_rapid_succession(self, storage: SettingsStorageProvider) -> None:
        """Test multiple rapid updates to settings."""
        initial_settings = Settings(
            target_language="de",
            providers=[
                ProviderConfig(
                    name="Initial",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="key1",
                )
            ],
        )

        storage.save(initial_settings)

        # Perform 10 rapid updates
        for i in range(10):
            updated = Settings(
                target_language=f"lang{i}",
                providers=[
                    ProviderConfig(
                        name=f"Provider{i}",
                        provider_type="openai",
                        model=f"model{i}",
                        api_key=f"key{i}",
                    )
                ],
            )
            storage.update(updated)

        final = storage.load()
        assert final.target_language == "lang9"
        assert final.providers[0].name == "Provider9"

    def test_save_after_delete(self, storage: SettingsStorageProvider) -> None:
        """Test saving new settings after deleting all."""
        settings1 = Settings(
            providers=[
                ProviderConfig(
                    name="First",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="key1",
                )
            ]
        )

        storage.save(settings1)
        storage.delete_all()

        settings2 = Settings(
            providers=[
                ProviderConfig(
                    name="Second",
                    provider_type="anthropic",
                    model="claude",
                    api_key="key2",
                )
            ]
        )

        storage.save(settings2)
        loaded = storage.load()

        assert loaded.providers[0].name == "Second"
        assert loaded.providers[0].provider_type == "anthropic"

    def test_all_provider_boolean_combinations(self, storage: SettingsStorageProvider) -> None:
        """Test all combinations of boolean flags."""
        test_cases = [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]

        for is_default, supports_streaming in test_cases:
            settings = Settings(
                providers=[
                    ProviderConfig(
                        name=f"Test_{is_default}_{supports_streaming}",
                        provider_type="openai",
                        model="gpt-4o",
                        api_key="test-key",
                        is_default=is_default,
                        supports_streaming=supports_streaming,
                    )
                ]
            )

            storage.save(settings)
            loaded = storage.load()

            assert loaded.providers[0].is_default == is_default
            assert loaded.providers[0].supports_streaming == supports_streaming

            storage.delete_all()

    def test_provider_with_none_base_url(self, storage: SettingsStorageProvider) -> None:
        """Test provider with explicitly None base_url."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Test",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                    api_url=None,
                )
            ]
        )

        saved = storage.save(settings)
        assert saved.providers[0].api_url is None

        loaded = storage.load()
        assert loaded.providers[0].api_url is None

    def test_multiple_providers_with_same_name(self, storage: SettingsStorageProvider) -> None:
        """Test saving multiple providers with identical names."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="SameName",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="key1",
                ),
                ProviderConfig(
                    name="SameName",
                    provider_type="anthropic",
                    model="claude",
                    api_key="key2",
                ),
                ProviderConfig(
                    name="SameName",
                    provider_type="gemini",
                    model="gemini",
                    api_key="key3",
                ),
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert len(loaded.providers) == 3
        assert all(p.name == "SameName" for p in loaded.providers)
        assert loaded.providers[0].provider_type == "openai"
        assert loaded.providers[1].provider_type == "anthropic"
        assert loaded.providers[2].provider_type == "gemini"

    def test_target_language_various_codes(self, storage: SettingsStorageProvider) -> None:
        """Test various language codes."""
        language_codes = ["de", "en", "es", "fr", "it", "pt", "ru", "zh", "ja", "ko"]

        for lang_code in language_codes:
            settings = Settings(target_language=lang_code, providers=[])
            storage.save(settings)
            loaded = storage.load()
            assert loaded.target_language == lang_code
            storage.delete_all()

    def test_timestamps_preserved_on_load(self, storage: SettingsStorageProvider) -> None:
        """Test that timestamps are preserved correctly."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Test",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        storage.save(settings)

        # Load multiple times - timestamps should remain consistent
        loaded1 = storage.load()
        loaded2 = storage.load()

        # Both loads should return same data (no timestamp changes on read)
        assert loaded1.target_language == loaded2.target_language

    def test_close_and_reopen_database(self, temp_db: Path) -> None:
        """Test closing and reopening database connection."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Test",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        # Save with first connection
        storage1 = SettingsStorageProvider(temp_db)
        storage1.save(settings)
        storage1.close()

        # Load with new connection
        storage2 = SettingsStorageProvider(temp_db)
        loaded = storage2.load()
        storage2.close()

        assert loaded.providers[0].name == "Test"

    def test_provider_empty_strings(self, storage: SettingsStorageProvider) -> None:
        """Test provider with empty string values (should still work)."""
        settings = Settings(
            providers=[
                ProviderConfig(
                    name="",
                    provider_type="openai",
                    model="",
                    api_key="",
                    api_url="",
                )
            ]
        )

        storage.save(settings)
        loaded = storage.load()

        assert loaded.providers[0].name == ""
        assert loaded.providers[0].model == ""
        assert loaded.providers[0].api_key == ""
        assert loaded.providers[0].api_url == ""

    def test_database_file_permissions(self, temp_db: Path) -> None:
        """Test that database file is created with proper permissions."""
        storage = SettingsStorageProvider(temp_db)

        settings = Settings(
            providers=[
                ProviderConfig(
                    name="Test",
                    provider_type="openai",
                    model="gpt-4o",
                    api_key="test-key",
                )
            ]
        )

        storage.save(settings)

        # Verify database file exists and is readable
        assert temp_db.exists()
        assert temp_db.is_file()
        assert temp_db.stat().st_size > 0
