"""Universal PydanticAI translation provider implementation.

Factory-based translator that works with all registered PydanticAI providers.
Uses ProviderRegistry to dynamically instantiate the correct Model class.
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai.models import Model

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation, WordAlignment
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


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
        logger.info(
            "Initializing PydanticAITranslator: provider=%s, model=%s, base_url=%s",
            provider_config.provider_type,
            provider_config.model,
            provider_config.base_url or "default",
        )
        model = self._create_model(provider_config)
        self._translator = BaseTranslator(model)
        logger.debug("PydanticAITranslator initialized successfully")

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
        logger.debug("Creating model for provider_type: %s", config.provider_type)
        model_class = ProviderRegistry.get_model_class(config.provider_type)

        if model_class is None:
            supported = ", ".join(ProviderRegistry.get_provider_types())
            logger.error("Unsupported provider: %s", config.provider_type)
            raise ValueError(f"Unsupported provider: {config.provider_type}. Supported providers: {supported}")

        logger.debug("Using model class: %s", model_class.__name__)

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
            "publicai": "pydantic_ai.providers.openai.OpenAIProvider",
            "hugginface": "pydantic_ai.providers.openai.OpenAIProvider",
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

        # Build provider arguments
        provider_kwargs: dict[str, object] = {"api_key": config.api_key}

        # Add base_url if configured
        if config.base_url:
            provider_kwargs["base_url"] = config.base_url

        # Create custom HTTP client with User-Agent header for better API compatibility
        from httpx import AsyncClient

        headers = {"User-Agent": "Birkenbihl/1.0 (PydanticAI)"}
        http_client = AsyncClient(headers=headers)
        provider_kwargs["http_client"] = http_client

        # Instantiate provider
        return provider_class(**provider_kwargs)

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

    def translate(
        self, text: str, source_lang: Language, target_lang: Language, title: str | None = None
    ) -> Translation:
        """Translate text using Birkenbihl method.

        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language

        Returns:
            Translation with natural and word-by-word translations

        Raises:
            Exception: If API call fails or API key is invalid
        """
        logger.info(
            "Starting translation: %s → %s, text_length=%d chars",
            source_lang,
            target_lang,
            len(text),
        )
        result = self._translator.translate(text, source_lang, target_lang, title=title)
        logger.info("Translation completed: %d sentences generated", len(result.sentences))
        return result

    async def translate_stream(
        self, text: str, source_lang: Language, target_lang: Language
    ) -> AsyncIterator[tuple[float, Translation | None]]:
        """Translate text using Birkenbihl method with streaming progress.

        Args:
            text: Text to translate
            source_lang: Source language
            target_lang: Target language

        Yields:
            Tuple of (progress: float, translation: Translation | None)
            - progress: 0.0 to 1.0 based on completed sentences
            - translation: Partial Translation with completed sentences

        Raises:
            Exception: If API call fails or API key is invalid
        """
        async for progress, translation in self._translator.translate_stream(text, source_lang, target_lang):
            yield progress, translation

    def detect_language(self, text: str) -> Language:
        """Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            Language instance
        """
        logger.debug("Detecting language for text: %d chars", len(text))
        detected = self._translator.detect_language(text)
        logger.info("Language detected: %s", detected)
        return detected

    def generate_alternatives(
        self,
        source_text: str,
        source_lang: Language,
        target_lang: Language,
        count: int = 3,
    ) -> list[str]:
        """Generate alternative natural translations for a sentence.

        Args:
            source_text: Original sentence to translate
            source_lang: Source language
            target_lang: Target language
            count: Number of alternative translations to generate (default: 3)

        Returns:
            List of natural translation alternatives

        Raises:
            Exception: If generation fails
        """
        return self._translator.generate_alternatives(source_text, source_lang, target_lang, count)

    def regenerate_alignment(
        self,
        source_text: str,
        natural_translation: str,
        source_lang: Language,
        target_lang: Language,
    ) -> list[WordAlignment]:
        """Generate word-by-word alignment based on given natural translation.

        Args:
            source_text: Original sentence
            natural_translation: Natural translation (chosen by user)
            source_lang: Source language
            target_lang: Target language

        Returns:
            List of WordAlignment objects mapping source words to target words

        Raises:
            Exception: If alignment generation fails
        """
        return self._translator.regenerate_alignment(source_text, natural_translation, source_lang, target_lang)
