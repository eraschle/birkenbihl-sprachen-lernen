"""Tests for the supported AI provider catalog."""

from pathlib import Path

import pytest
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.typesafe import TypeSafeModel

from birkenbihl.exceptions import ProviderError
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.providers import catalog, translator_factory
from birkenbihl.providers.jev_aligner import JevAligner
from birkenbihl.providers.llm_aligner import LLMAligner
from birkenbihl.services.settings_service import SettingsService


def _config(provider_type: str, model: str = "some-model", api_url: str | None = None) -> ProviderConfig:
    return ProviderConfig(name="Test", provider_type=provider_type, model=model, api_key="key", api_url=api_url)


class TestCatalog:
    def test_supported_provider_types_are_stable(self) -> None:
        """Provider types are stored in user settings; renaming one breaks existing settings."""
        types = [info.provider_type.value for info in catalog.list_providers()]

        assert types == ["openai", "anthropic", "google", "openai-compatible"]

    @pytest.mark.parametrize(
        ("provider_type", "model_class"),
        [("openai", OpenAIChatModel), ("anthropic", AnthropicModel), ("google", GoogleModel)],
    )
    def test_create_model(self, provider_type: str, model_class: type) -> None:
        model = catalog.create_model(_config(provider_type, model="my-model"))

        assert isinstance(model, model_class)
        assert model.model_name == "my-model"

    def test_openai_compatible_uses_configured_url(self) -> None:
        model = catalog.create_model(_config("openai-compatible", "llama3.1", api_url="http://localhost:11434/v1"))

        assert isinstance(model, OpenAIChatModel)
        assert model.base_url.startswith("http://localhost:11434/v1")

    def test_openai_compatible_without_url_is_rejected(self) -> None:
        with pytest.raises(ProviderError, match="needs an API URL"):
            catalog.create_model(_config("openai-compatible"))

    def test_unknown_provider_is_rejected(self) -> None:
        with pytest.raises(ProviderError, match="Unsupported provider: groq"):
            catalog.create_model(_config("groq"))

    def test_only_openai_compatible_requires_url(self) -> None:
        requires_url = {info.provider_type.value: info.requires_api_url for info in catalog.list_providers()}

        assert requires_url == {"openai": False, "anthropic": False, "google": False, "openai-compatible": True}

    @pytest.mark.parametrize(("provider_type", "expected"), [("anthropic", "claude"), ("google", "gemini")])
    def test_suggested_models_come_from_pydantic_ai(self, provider_type: str, expected: str) -> None:
        models = catalog.suggested_models(provider_type)

        assert models
        assert all(expected in model for model in models)

    def test_openai_compatible_has_no_suggestions(self) -> None:
        assert catalog.suggested_models("openai-compatible") == []


class TestSettingsValidation:
    def test_valid_provider(self) -> None:
        assert SettingsService.validate_provider_config(_config("anthropic")) is None

    def test_unsupported_provider_lists_supported_ones(self) -> None:
        error = SettingsService.validate_provider_config(_config("google-gla"))

        assert error is not None
        assert "'google-gla' wird nicht unterstützt" in error
        assert "openai-compatible" in error

    def test_openai_compatible_needs_url(self) -> None:
        error = SettingsService.validate_provider_config(_config("openai-compatible"))

        assert error == "Provider 'Test' braucht eine API-URL"


class TestJev:
    def test_create_jev_model_with_key(self) -> None:
        assert isinstance(catalog.create_jev_model("key"), TypeSafeModel)

    def test_create_jev_model_falls_back_to_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TYPESAFE_API_KEY", "key-from-env")

        assert isinstance(catalog.create_jev_model(None), TypeSafeModel)

    def test_create_jev_model_without_any_key_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)

        with pytest.raises(ProviderError, match="jev_api_key"):
            catalog.create_jev_model(None)

    def test_translator_factory_uses_jev_when_chosen(self) -> None:
        factory = translator_factory(Settings(word_aligner="jev", jev_api_key="key"))

        assert isinstance(factory(_config("anthropic"))._aligner, JevAligner)

    def test_translator_factory_defaults_to_the_language_model(self) -> None:
        factory = translator_factory(Settings())

        assert isinstance(factory(_config("anthropic"))._aligner, LLMAligner)

    def test_word_aligner_is_read_from_settings_file(self, tmp_path: Path) -> None:
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text("providers: []\nword_aligner: jev\njev_api_key: key\n", encoding="utf-8")

        settings = SettingsService(settings_file).load_settings()

        assert (settings.word_aligner, settings.jev_api_key) == ("jev", "key")
