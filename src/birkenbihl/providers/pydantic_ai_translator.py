"""Universal PydanticAI translation provider implementation.

Factory-based translator that works with all registered PydanticAI providers.
Uses ProviderRegistry to dynamically instantiate the correct Model class.
"""

from typing import Any

from pydantic_ai.models import Model

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.registry import ProviderRegistry


class PydanticAITranslator:
    """Universal translation provider using PydanticAI models.

    Factory pattern implementation that supports all registered providers
    (OpenAI, Anthropic, Gemini, Groq, DeepSeek, etc.) through dynamic
    Model instantiation via ProviderRegistry.

    Design:
    - Uses ProviderRegistry to get correct Model class for provider_type
    - Handles API key injection for all provider types
    - Delegates translation logic to BaseTranslator
    - Supports both native providers (Anthropic, Gemini) and OpenAI-compatible

    Example:
        # OpenAI
        config = ProviderConfig(
            name="GPT-4",
            provider_type="openai",
            model="gpt-4o",
            api_key="sk-..."
        )
        translator = PydanticAITranslator(config)

        # Anthropic
        config = ProviderConfig(
            name="Claude",
            provider_type="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="sk-ant-..."
        )
        translator = PydanticAITranslator(config)

        # Groq
        config = ProviderConfig(
            name="Groq",
            provider_type="groq",
            model="llama-3.1-70b-versatile",
            api_key="gsk_..."
        )
        translator = PydanticAITranslator(config)
    """

    def __init__(self, provider_config: ProviderConfig):
        """Initialize universal translator with dynamic Model instantiation.

        Args:
            provider_config: Provider configuration with type, model, and API key

        Raises:
            ValueError: If provider_type is not registered in ProviderRegistry
            ImportError: If required provider library is not installed
        """
        model = self._create_model(provider_config)
        self._translator = BaseTranslator(model)

    def _create_model(self, config: ProviderConfig) -> Model:
        """Create appropriate PydanticAI Model instance for provider.

        Factory method that instantiates the correct Model class based on
        provider_type from ProviderRegistry.

        Args:
            config: Provider configuration

        Returns:
            Instantiated Model ready for use with BaseTranslator

        Raises:
            ValueError: If provider_type is not supported
            ImportError: If provider library is not installed
        """
        model_class = ProviderRegistry.get_model_class(config.provider_type)

        if model_class is None:
            supported = ", ".join(ProviderRegistry.get_provider_types())
            raise ValueError(f"Unsupported provider: {config.provider_type}. Supported providers: {supported}")

        # For OpenAI-compatible providers using OpenAIChatModel
        if model_class.__name__ == "OpenAIChatModel":
            return self._create_openai_compatible_model(config, model_class)

        # For providers with dedicated Model classes
        return self._create_native_model(config, model_class)

    def _create_openai_compatible_model(self, config: ProviderConfig, model_class: Any) -> Model:
        """Create OpenAI-compatible Model instance.

        For providers that use OpenAIChatModel with custom provider parameter
        (OpenAI, DeepSeek, Groq, Cerebras, Fireworks, etc.).

        Args:
            config: Provider configuration
            model_class: OpenAIChatModel class from registry

        Returns:
            Instantiated OpenAIChatModel with correct provider
        """
        # Import provider class dynamically based on provider_type
        provider_instance = self._get_openai_provider(config)

        # Instantiate OpenAIChatModel with model name and provider
        return model_class(config.model, provider=provider_instance)

    def _create_native_model(self, config: ProviderConfig, model_class: Any) -> Model:
        """Create native Model instance for providers with dedicated classes.

        For Anthropic, Google, Groq, Cohere, Mistral, Bedrock models that
        have their own Model classes in PydanticAI.

        Args:
            config: Provider configuration
            model_class: Model class (AnthropicModel, GoogleModel, etc.)

        Returns:
            Instantiated Model with appropriate provider
        """
        # Get corresponding Provider class
        provider_instance = self._get_native_provider(config, model_class)

        # Instantiate Model with model name and provider
        return model_class(config.model, provider=provider_instance)

    def _get_openai_provider(self, config: ProviderConfig):
        """Get OpenAI-compatible Provider instance.

        Dynamically imports and instantiates the correct Provider class
        for OpenAI-compatible endpoints.

        Args:
            config: Provider configuration

        Returns:
            Provider instance (OpenAIProvider, DeepSeekProvider, etc.)
        """
        provider_map = {
            "openai": "pydantic_ai.providers.openai.OpenAIProvider",
            "deepseek": "pydantic_ai.providers.openai.OpenAIProvider",
            "cerebras": "pydantic_ai.providers.openai.OpenAIProvider",
            "fireworks": "pydantic_ai.providers.openai.OpenAIProvider",
            "github": "pydantic_ai.providers.openai.OpenAIProvider",
            "grok": "pydantic_ai.providers.openai.OpenAIProvider",
            "heroku": "pydantic_ai.providers.openai.OpenAIProvider",
            "ollama": "pydantic_ai.providers.openai.OpenAIProvider",
            "openrouter": "pydantic_ai.providers.openai.OpenAIProvider",
            "together": "pydantic_ai.providers.openai.OpenAIProvider",
            "vercel": "pydantic_ai.providers.openai.OpenAIProvider",
            "litellm": "pydantic_ai.providers.openai.OpenAIProvider",
            "azure": "pydantic_ai.providers.openai.OpenAIProvider",
        }

        provider_path = provider_map.get(config.provider_type)
        if not provider_path:
            raise ValueError(f"No OpenAI-compatible provider mapping for: {config.provider_type}")

        # Import Provider class dynamically
        module_path, class_name = provider_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        provider_class = getattr(module, class_name)

        # Instantiate with API key
        return provider_class(api_key=config.api_key)

    def _get_native_provider(self, config: ProviderConfig, model_class: Any):
        """Get native Provider instance for dedicated Model classes.

        Dynamically imports and instantiates Provider for Anthropic, Google,
        Groq, Cohere, Mistral, Bedrock models.

        Args:
            config: Provider configuration
            model_class: Model class (AnthropicModel, GoogleModel, etc.)

        Returns:
            Provider instance
        """
        provider_map = {
            "AnthropicModel": "pydantic_ai.providers.anthropic.AnthropicProvider",
            "GoogleModel": "pydantic_ai.providers.google.GoogleProvider",
            "GroqModel": "pydantic_ai.providers.groq.GroqProvider",
            "CohereModel": "pydantic_ai.providers.cohere.CohereProvider",
            "MistralModel": "pydantic_ai.providers.mistral.MistralProvider",
            "BedrockConverseModel": "pydantic_ai.providers.bedrock.BedrockProvider",
        }

        model_name = model_class.__name__
        provider_path = provider_map.get(model_name)

        if not provider_path:
            raise ValueError(f"No provider mapping for model class: {model_name}")

        # Import Provider class dynamically
        module_path, class_name = provider_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        provider_class = getattr(module, class_name)

        # Instantiate with API key
        return provider_class(api_key=config.api_key)

    def translate(self, text: str, source_lang: str, target_lang: str) -> Translation:
        """Translate text using Birkenbihl method.

        Args:
            text: Text to translate
            source_lang: Source language code (en, es)
            target_lang: Target language code (de)

        Returns:
            Translation with natural and word-by-word translations

        Raises:
            Exception: If API call fails or API key is invalid
        """
        return self._translator.translate(text, source_lang, target_lang)

    def detect_language(self, text: str) -> str:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language code (en, es, de)
        """
        return self._translator.detect_language(text)
