"""Tests for provider registry.

Tests the dynamic provider registry that discovers and registers
all available PydanticAI providers at runtime.
"""

from birkenbihl.providers.registry import ProviderMetadata, ProviderRegistry, _extract_model_names


class TestExtractModelNames:
    """Test model name extraction from PydanticAI types."""

    def test_extract_openai_models(self):
        """Test extraction of OpenAI model names."""
        from pydantic_ai.models.openai import OpenAIModelName

        models = _extract_model_names(OpenAIModelName)

        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, str) for m in models)
        # Check for known models
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models

    def test_extract_anthropic_models(self):
        """Test extraction of Anthropic model names."""
        from pydantic_ai.models.anthropic import AnthropicModelName

        models = _extract_model_names(AnthropicModelName)

        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, str) for m in models)
        # Check for known models
        assert any("claude" in m for m in models)
        assert any("sonnet" in m for m in models)

    def test_extract_gemini_models(self):
        """Test extraction of Gemini model names."""
        from pydantic_ai.models.gemini import GeminiModelName

        models = _extract_model_names(GeminiModelName)

        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, str) for m in models)
        # Check for known models
        assert any("gemini" in m for m in models)

    def test_extract_groq_models(self):
        """Test extraction of Groq model names."""
        from pydantic_ai.models.groq import GroqModelName

        models = _extract_model_names(GroqModelName)

        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, str) for m in models)
        # Check for known models
        assert any("llama" in m for m in models)


class TestProviderRegistry:
    """Test provider registry initialization and access."""

    def test_registry_initialization(self):
        """Test that registry initializes correctly."""
        providers = ProviderRegistry.get_supported_providers()

        assert isinstance(providers, list)
        assert len(providers) > 0
        assert all(isinstance(p, ProviderMetadata) for p in providers)

    def test_registry_contains_expected_providers(self):
        """Test that registry contains all expected provider types."""
        provider_types = ProviderRegistry.get_provider_types()

        # Check for key providers
        expected_providers = ["openai", "anthropic", "gemini", "groq", "cohere", "mistral"]
        for provider in expected_providers:
            assert provider in provider_types, f"Provider {provider} not found in registry"

    def test_registry_openai_compatible_providers(self):
        """Test that OpenAI-compatible providers are registered."""
        provider_types = ProviderRegistry.get_provider_types()

        # All OpenAI-compatible providers
        openai_compatible = [
            "openai",
            "azure",
            "deepseek",
            "cerebras",
            "fireworks",
            "github",
            "grok",
            "heroku",
            "ollama",
            "openrouter",
            "together",
            "vercel",
            "litellm",
        ]

        for provider in openai_compatible:
            assert provider in provider_types, f"OpenAI-compatible provider {provider} not found"

    def test_get_provider_metadata(self):
        """Test getting metadata for specific provider."""
        metadata = ProviderRegistry.get_provider_metadata("openai")

        assert metadata is not None
        assert isinstance(metadata, ProviderMetadata)
        assert metadata.provider_type == "openai"
        assert metadata.display_name == "OpenAI"
        assert len(metadata.default_models) > 0
        assert metadata.requires_api_key is True

    def test_get_provider_metadata_nonexistent(self):
        """Test getting metadata for nonexistent provider returns None."""
        metadata = ProviderRegistry.get_provider_metadata("nonexistent_provider")

        assert metadata is None

    def test_get_model_class(self):
        """Test getting model class for provider."""
        from pydantic_ai.models.openai import OpenAIChatModel

        model_class = ProviderRegistry.get_model_class("openai")

        assert model_class is not None
        assert model_class == OpenAIChatModel

    def test_get_model_class_nonexistent(self):
        """Test getting model class for nonexistent provider returns None."""
        model_class = ProviderRegistry.get_model_class("nonexistent_provider")

        assert model_class is None

    def test_is_supported(self):
        """Test checking if provider is supported."""
        assert ProviderRegistry.is_supported("openai") is True
        assert ProviderRegistry.is_supported("anthropic") is True
        assert ProviderRegistry.is_supported("nonexistent_provider") is False

    def test_provider_has_all_models(self):
        """Test that providers have all available models from PydanticAI."""
        from pydantic_ai.models.anthropic import AnthropicModelName

        metadata = ProviderRegistry.get_provider_metadata("anthropic")
        expected_models = _extract_model_names(AnthropicModelName)

        assert metadata is not None
        assert len(metadata.default_models) == len(expected_models)
        assert set(metadata.default_models) == set(expected_models)

    def test_openai_compatible_have_provider_specific_models(self):
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
        assert "deepseek-coder" in deepseek_meta.default_models
        assert len(deepseek_meta.default_models) > 0

        # Ollama has local models
        assert "llama3.1" in ollama_meta.default_models
        assert len(ollama_meta.default_models) > 0

    def test_openai_compatible_use_same_model_class(self):
        """Test that all OpenAI-compatible providers use OpenAIChatModel."""
        from pydantic_ai.models.openai import OpenAIChatModel

        openai_compatible = ["openai", "azure", "deepseek", "ollama"]

        for provider_type in openai_compatible:
            model_class = ProviderRegistry.get_model_class(provider_type)
            assert model_class == OpenAIChatModel, f"{provider_type} should use OpenAIChatModel"

    def test_anthropic_metadata(self):
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

    def test_gemini_metadata(self):
        """Test Gemini provider metadata."""
        from pydantic_ai.models.google import GoogleModel

        metadata = ProviderRegistry.get_provider_metadata("gemini")

        assert metadata is not None
        assert metadata.provider_type == "gemini"
        assert metadata.display_name == "Google Gemini"
        assert metadata.model_class == GoogleModel
        assert len(metadata.default_models) > 0
        assert any("gemini" in m for m in metadata.default_models)

    def test_groq_metadata(self):
        """Test Groq provider metadata."""
        from pydantic_ai.models.groq import GroqModel

        metadata = ProviderRegistry.get_provider_metadata("groq")

        assert metadata is not None
        assert metadata.provider_type == "groq"
        assert metadata.display_name == "Groq"
        assert metadata.model_class == GroqModel
        assert len(metadata.default_models) > 0

    def test_registry_singleton_behavior(self):
        """Test that registry initializes only once (singleton pattern)."""
        # Call multiple times
        providers1 = ProviderRegistry.get_supported_providers()
        providers2 = ProviderRegistry.get_supported_providers()
        providers3 = ProviderRegistry.get_provider_types()

        # Should return consistent results
        assert len(providers1) == len(providers2)
        assert len(providers3) == len(providers1)

    def test_all_providers_have_valid_metadata(self):
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

            # All models should be strings
            assert all(isinstance(m, str) for m in provider.default_models)

    def test_no_duplicate_provider_types(self):
        """Test that there are no duplicate provider types."""
        provider_types = ProviderRegistry.get_provider_types()

        # Check for duplicates
        assert len(provider_types) == len(set(provider_types)), "Found duplicate provider types"
