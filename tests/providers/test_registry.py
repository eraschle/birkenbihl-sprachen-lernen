"""Tests for provider registry.

Tests the dynamic provider registry that discovers and registers
all available PydanticAI providers at runtime.
"""

from birkenbihl.providers.registry import ProviderMetadata, ProviderRegistry, _parse_known_model_names


class TestProviderRegistry:
    """Test provider registry initialization and access."""

    def test_registry_initialization(self) -> None:
        """Test that registry initializes correctly."""
        providers = ProviderRegistry.get_supported_providers()

        assert isinstance(providers, list)
        assert len(providers) > 0
        assert all(isinstance(p, ProviderMetadata) for p in providers)

    def test_registry_contains_expected_providers(self) -> None:
        """Test that registry contains all expected provider types."""
        provider_types = ProviderRegistry.get_provider_types()

        # Check for key providers
        expected_providers = ["openai", "anthropic", "google-gla", "groq", "cohere", "mistral"]
        for provider in expected_providers:
            assert provider in provider_types, f"Provider {provider} not found in registry"

    def test_registry_openai_compatible_providers(self) -> None:
        """Test that OpenAI-compatible providers are registered."""
        provider_types = ProviderRegistry.get_provider_types()

        # OpenAI-compatible providers that should be registered
        # (from KnownModelName or FALLBACK_MODELS)
        openai_compatible = [
            "openai",
            "azure",
            "deepseek",
            "cerebras",
            "fireworks",
            "grok",
            "heroku",
            "moonshotai",
            "ollama",
        ]

        for provider in openai_compatible:
            assert provider in provider_types, f"OpenAI-compatible provider {provider} not found"

    def test_get_provider_metadata(self) -> None:
        """Test getting metadata for specific provider."""
        metadata = ProviderRegistry.get_provider_metadata("openai")

        assert metadata is not None
        assert isinstance(metadata, ProviderMetadata)
        assert metadata.provider_type == "openai"
        assert metadata.display_name == "OpenAI"
        assert len(metadata.default_models) > 0
        assert metadata.requires_api_key is True
        assert metadata.requires_api_url_input is False

    def test_get_provider_metadata_nonexistent(self) -> None:
        """Test getting metadata for nonexistent provider returns None."""
        metadata = ProviderRegistry.get_provider_metadata("nonexistent_provider")

        assert metadata is None

    def test_get_model_class(self) -> None:
        """Test getting model class for provider."""
        from pydantic_ai.models.openai import OpenAIChatModel

        model_class = ProviderRegistry.get_model_class("openai")

        assert model_class is not None
        assert model_class == OpenAIChatModel

    def test_get_model_class_nonexistent(self) -> None:
        """Test getting model class for nonexistent provider returns None."""
        model_class = ProviderRegistry.get_model_class("nonexistent_provider")

        assert model_class is None

    def test_is_supported(self) -> None:
        """Test checking if provider is supported."""
        assert ProviderRegistry.is_supported("openai") is True
        assert ProviderRegistry.is_supported("anthropic") is True
        assert ProviderRegistry.is_supported("nonexistent_provider") is False

    def test_provider_has_all_models(self) -> None:
        """Test that providers have all available models from PydanticAI."""
        provider_models = _parse_known_model_names()
        metadata = ProviderRegistry.get_provider_metadata("anthropic")

        assert metadata is not None
        assert "anthropic" in provider_models
        expected_models = provider_models["anthropic"]
        assert len(metadata.default_models) == len(expected_models)
        assert set(metadata.default_models) == set(expected_models)

    def test_openai_compatible_have_provider_specific_models(self) -> None:
        """Test that OpenAI-compatible providers have provider-specific model lists."""
        openai_meta = ProviderRegistry.get_provider_metadata("openai")
        azure_meta = ProviderRegistry.get_provider_metadata("azure")
        deepseek_meta = ProviderRegistry.get_provider_metadata("deepseek")
        ollama_meta = ProviderRegistry.get_provider_metadata("ollama")

        assert openai_meta is not None
        assert azure_meta is not None
        assert deepseek_meta is not None
        assert ollama_meta is not None

        # OpenAI and Azure share models (Azure hosts OpenAI models)
        assert openai_meta.default_models == azure_meta.default_models

        # DeepSeek has its own models
        assert "deepseek-chat" in deepseek_meta.default_models
        assert len(deepseek_meta.default_models) > 0

        # Ollama has local models
        assert "llama3.1" in ollama_meta.default_models
        assert len(ollama_meta.default_models) > 0

    def test_openai_compatible_use_same_model_class(self) -> None:
        """Test that all OpenAI-compatible providers use OpenAIChatModel."""
        from pydantic_ai.models.openai import OpenAIChatModel

        openai_compatible = ["openai", "azure", "deepseek", "ollama"]

        for provider_type in openai_compatible:
            model_class = ProviderRegistry.get_model_class(provider_type)
            assert model_class == OpenAIChatModel, f"{provider_type} should use OpenAIChatModel"

    def test_anthropic_metadata(self) -> None:
        """Test Anthropic provider metadata."""
        from pydantic_ai.models.anthropic import AnthropicModel

        metadata = ProviderRegistry.get_provider_metadata("anthropic")

        assert metadata is not None
        assert metadata.provider_type == "anthropic"
        assert metadata.display_name == "Anthropic Claude"
        assert metadata.model_class == AnthropicModel
        assert len(metadata.default_models) > 0
        # Check for known Claude models
        assert any("claude" in m for m in metadata.default_models)
        assert any("sonnet" in m or "haiku" in m or "opus" in m for m in metadata.default_models)

    def test_gemini_metadata(self) -> None:
        """Test Google Gemini provider metadata."""
        from pydantic_ai.models.google import GoogleModel

        metadata = ProviderRegistry.get_provider_metadata("google-gla")

        assert metadata is not None
        assert metadata.provider_type == "google-gla"
        assert metadata.display_name == "Google Gemini"
        assert metadata.model_class == GoogleModel
        assert len(metadata.default_models) > 0
        assert any("gemini" in m for m in metadata.default_models)

    def test_groq_metadata(self) -> None:
        """Test Groq provider metadata."""
        from pydantic_ai.models.groq import GroqModel

        metadata = ProviderRegistry.get_provider_metadata("groq")

        assert metadata is not None
        assert metadata.provider_type == "groq"
        assert metadata.display_name == "Groq"
        assert metadata.model_class == GroqModel
        assert len(metadata.default_models) > 0

    def test_registry_singleton_behavior(self) -> None:
        """Test that registry initializes only once (singleton pattern)."""
        # Call multiple times
        providers1 = ProviderRegistry.get_supported_providers()
        providers2 = ProviderRegistry.get_supported_providers()
        providers3 = ProviderRegistry.get_provider_types()

        # Should return consistent results
        assert len(providers1) == len(providers2)
        assert len(providers3) == len(providers1)

    def test_initialize_method_is_idempotent(self) -> None:
        """Test that initialize() can be called multiple times safely."""
        # Call initialize multiple times
        ProviderRegistry.initialize()
        providers1 = ProviderRegistry.get_supported_providers()

        ProviderRegistry.initialize()
        providers2 = ProviderRegistry.get_supported_providers()

        ProviderRegistry.initialize()
        providers3 = ProviderRegistry.get_supported_providers()

        # All calls should return the same results
        assert len(providers1) == len(providers2) == len(providers3)
        assert len(providers1) > 0

    def test_all_providers_have_valid_metadata(self) -> None:
        """Test that all registered providers have valid metadata."""
        providers = ProviderRegistry.get_supported_providers()

        for provider in providers:
            # Check all required fields are set
            assert provider.provider_type
            assert provider.display_name
            assert provider.model_class is not None
            assert isinstance(provider.default_models, list)
            assert len(provider.default_models) > 0
            assert isinstance(provider.requires_api_key, bool)
            assert isinstance(provider.requires_api_url_input, bool)

            # All models should be strings
            assert all(isinstance(m, str) for m in provider.default_models)

    def test_providers_requiring_api_url(self) -> None:
        """Test that providers requiring API URL have correct metadata."""
        from birkenbihl.providers.registry import is_api_url_requiered

        # Test ollama (requires API URL)
        ollama_meta = ProviderRegistry.get_provider_metadata("ollama")
        assert ollama_meta is not None
        assert ollama_meta.requires_api_url_input is True
        assert is_api_url_requiered("ollama") is True

        # Test providers that don't require API URL
        openai_meta = ProviderRegistry.get_provider_metadata("openai")
        anthropic_meta = ProviderRegistry.get_provider_metadata("anthropic")
        azure_meta = ProviderRegistry.get_provider_metadata("azure")

        assert openai_meta is not None
        assert openai_meta.requires_api_url_input is False
        assert is_api_url_requiered("openai") is False

        assert anthropic_meta is not None
        assert anthropic_meta.requires_api_url_input is False
        assert is_api_url_requiered("anthropic") is False

        assert azure_meta is not None
        assert azure_meta.requires_api_url_input is False
        assert is_api_url_requiered("azure") is False

    def test_no_duplicate_provider_types(self) -> None:
        """Test that there are no duplicate provider types."""
        provider_types = ProviderRegistry.get_provider_types()

        # Check for duplicates
        assert len(provider_types) == len(set(provider_types)), "Found duplicate provider types"
