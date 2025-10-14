"""Dynamic provider registry for PydanticAI models.

Discovers and registers all available PydanticAI providers at runtime by parsing
KnownModelName from pydantic_ai.models. This approach avoids heavy imports at startup
and stays automatically synchronized with pydantic_ai updates.
"""

import re
from dataclasses import dataclass
from typing import get_args

from pydantic_ai.models import KnownModelName, Model

from birkenbihl.models.settings import ProviderConfig


@dataclass
class ProviderMetadata:
    """Metadata for a registered provider.

    Attributes:
        provider_type: Provider identifier (openai, anthropic, gemini, etc.)
        display_name: Human-readable name for UI
        model_class_path: Import path to Model class (lazy loaded)
        default_models: Suggested model identifiers for this provider
        requires_api_key: Whether provider requires API key authentication
    """

    provider_type: str
    display_name: str
    model_class_path: str
    default_models: list[str]
    requires_api_key: bool = True
    requires_api_url_input: bool = False
    api_url: str | None = None

    @property
    def model_class(self) -> type[Model]:
        """Lazy load Model class to avoid heavy imports."""
        module_path, class_name = self.model_class_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)


def _model_sort_key(model_name: str) -> tuple[int, str]:
    """Extract sort key for model names: (version_number, full_name).

    Models with version numbers are sorted numerically first, then alphabetically.
    Models without version numbers come last, sorted alphabetically.

    Examples:
        "claude-3-5-sonnet" -> (3, "claude-3-5-sonnet")
        "gpt-4o" -> (4, "gpt-4o")
        "gemini-2.0-flash" -> (2, "gemini-2.0-flash")
        "llama3.1" -> (3, "llama3.1")
        "mistral" -> (999999, "mistral")  # No version, comes last
    """
    match = re.search(r"[-.](\d+)", model_name)
    version = int(match.group(1)) if match else 999999
    return (version, model_name)


def _parse_known_model_names() -> dict[str, list[str]]:
    """Parse KnownModelName to extract provider:model mappings.

    Returns:
        Dict mapping provider_type to list of model names
    """
    provider_models: dict[str, list[str]] = {}

    # KnownModelName is a TypeAliasType, need __value__ to get the Literal
    actual_type = KnownModelName.__value__
    model_names = get_args(actual_type)

    for model_name in model_names:
        if isinstance(model_name, str) and ":" in model_name:
            provider, model = model_name.split(":", 1)
            if provider not in provider_models:
                provider_models[provider] = []
            provider_models[provider].append(model)

    return provider_models


# Provider display names
PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic Claude",
    "google-gla": "Google Gemini",
    "google-vertex": "Google Gemini (Vertex)",
    "groq": "Groq",
    "cohere": "Cohere",
    "mistral": "Mistral AI",
    "bedrock": "AWS Bedrock",
    "huggingface": "HuggingFace",
    "azure": "Azure OpenAI",
    "deepseek": "DeepSeek",
    "cerebras": "Cerebras",
    "fireworks": "Fireworks AI",
    "github": "GitHub Models",
    "grok": "Grok (xAI)",
    "heroku": "Heroku",
    "moonshotai": "Moonshot AI",
    "ollama": "Ollama (Local)",
    "openrouter": "OpenRouter",
    "together": "Together AI",
    "vercel": "Vercel AI",
    "litellm": "LiteLLM",
}

DEFAULT_MODEL_CLASS_PATH = "pydantic_ai.models.openai.OpenAIChatModel"

# Provider to Model class mapping (from infer_model() in pydantic_ai)
# Only list providers that use non-OpenAI model classes
# All other providers default to OpenAIChatModel
PROVIDER_MODEL_CLASSES = {
    "cohere": "pydantic_ai.models.cohere.CohereModel",
    "google-gla": "pydantic_ai.models.google.GoogleModel",
    "google-vertex": "pydantic_ai.models.google.GoogleModel",
    "groq": "pydantic_ai.models.groq.GroqModel",
    "mistral": "pydantic_ai.models.mistral.MistralModel",
    "anthropic": "pydantic_ai.models.anthropic.AnthropicModel",
    "bedrock": "pydantic_ai.models.bedrock.BedrockConverseModel",
    "huggingface": "pydantic_ai.models.huggingface.HuggingFaceModel",
}

# Fallback models for providers not in KnownModelName or with provider-specific models
# These providers use OpenAI-compatible API but aren't listed in KnownModelName
FALLBACK_MODELS = {
    "ollama": ["llama3.1", "llama3.1:70b", "mistral", "codellama", "qwen2.5:72b"],
    "fireworks": ["llama-v3p1-70b-instruct", "mixtral-8x7b-instruct", "qwen2.5-72b-instruct"],
}

# Providers that should use OpenAI's model list as fallback
USE_OPENAI_MODELS = {"azure"}

# Providers that require custom base URL
PROVIDERS_REQUIRING_URL = {"litellm", "ollama"}


def _get_provider_type_by(provider_name: str) -> str | None:
    for prov_type, prov_name in PROVIDER_DISPLAY_NAMES.items():
        if prov_name != provider_name:
            continue
        return prov_type
    return None


def is_api_url_requiered(provider_type: str) -> bool:
    if provider_type not in PROVIDERS_REQUIRING_URL:
        prov_type = _get_provider_type_by(provider_type)
        if prov_type is None:
            return False
        provider_type = prov_type

    return provider_type in PROVIDERS_REQUIRING_URL


def _create_provider_metadata(
    provider_type: str, models: list[str], model_class_path: str | None = None
) -> ProviderMetadata:
    """Create ProviderMetadata for a single provider.

    Args:
        provider_type: Provider identifier (openai, anthropic, etc.)
        models: List of model names for this provider
        model_class_path: Optional custom model class path

    Returns:
        ProviderMetadata instance
    """
    if model_class_path is None:
        model_class_path = PROVIDER_MODEL_CLASSES.get(provider_type, DEFAULT_MODEL_CLASS_PATH)

    display_name = PROVIDER_DISPLAY_NAMES.get(provider_type, provider_type.title())
    requires_url = is_api_url_requiered(provider_type=provider_type)

    return ProviderMetadata(
        provider_type=provider_type,
        display_name=display_name,
        model_class_path=model_class_path,
        default_models=models,
        requires_api_url_input=requires_url,
    )


def _add_providers_from_dict(
    providers: dict[str, ProviderMetadata], source: dict[str, list[str]], skip_existing: bool = False
) -> None:
    """Add providers from a source dictionary to registry.

    Args:
        providers: Target provider registry
        source: Dict mapping provider_type to list of models
        skip_existing: If True, skip providers already in registry
    """
    for provider_type, models in source.items():
        if skip_existing and provider_type in providers:
            continue
        sorted_models = sorted(models, key=_model_sort_key)
        providers[provider_type] = _create_provider_metadata(provider_type, sorted_models)


def _create_providers_from_known_models() -> dict[str, ProviderMetadata]:
    """Create provider registry from KnownModelName without heavy imports.

    Orchestrates creation of provider metadata from multiple sources:
    1. Known providers from pydantic_ai's KnownModelName
    2. Fallback providers (ollama, fireworks)
    3. OpenAI-compatible providers (azure)

    Returns:
        Dict mapping provider_type to ProviderMetadata
    """
    provider_models = _parse_known_model_names()
    providers: dict[str, ProviderMetadata] = {}

    # Add providers from KnownModelName
    _add_providers_from_dict(providers, provider_models)

    # Add fallback providers
    _add_providers_from_dict(providers, FALLBACK_MODELS, skip_existing=True)

    # Add OpenAI-compatible providers (azure) with OpenAI's model list
    openai_models = providers.get("openai", _create_provider_metadata("openai", [])).default_models
    for provider_type in USE_OPENAI_MODELS:
        if provider_type not in providers:
            providers[provider_type] = _create_provider_metadata(provider_type, openai_models)

    return providers


class ProviderRegistry:
    """Registry for PydanticAI providers.

    Parses pydantic_ai's KnownModelName to discover all providers and models.
    Model classes are lazy-loaded to avoid heavy imports at startup.

    Thread-safe singleton pattern ensures consistent provider access.
    Automatically stays synchronized with pydantic_ai updates.
    """

    _instance: "ProviderRegistry | None" = None
    _lock = __import__("threading").Lock()

    def __init__(self) -> None:
        """Private constructor - use get_instance() instead."""
        self._providers: dict[str, ProviderMetadata] = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        """Get singleton instance of ProviderRegistry.

        Thread-safe lazy initialization ensures instance is created only once.

        Returns:
            Singleton ProviderRegistry instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _ensure_initialized(self) -> None:
        """Ensure registry is initialized by parsing KnownModelName.

        Parses pydantic_ai's KnownModelName exactly once.
        No heavy imports - Model classes are lazy-loaded when accessed.
        Thread-safe - safe to call multiple times.
        """
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self._providers = _create_providers_from_known_models()
            self._initialized = True

    @classmethod
    def initialize(cls) -> None:
        """Initialize registry with all available providers.

        Safe to call multiple times - subsequent calls are no-op.
        Useful for pre-loading providers at application startup.
        """
        instance = cls.get_instance()
        instance._ensure_initialized()

    @classmethod
    def get_supported_providers(cls) -> list[ProviderMetadata]:
        """Get list of all registered providers.

        Returns:
            List of ProviderMetadata for all available providers
        """
        instance = cls.get_instance()
        instance._ensure_initialized()
        return sorted(instance._providers.values(), key=lambda prv: prv.display_name)

    @classmethod
    def get_provider_types(cls) -> list[str]:
        """Get list of all provider type identifiers.

        Returns:
            List of provider_type strings (openai, anthropic, etc.)
        """
        instance = cls.get_instance()
        instance._ensure_initialized()
        return list(instance._providers.keys())

    @classmethod
    def get_provider_metadata(cls, provider_type: str) -> ProviderMetadata | None:
        """Get metadata for specific provider.

        Args:
            provider_type: Provider identifier (openai, anthropic, etc.)

        Returns:
            ProviderMetadata if found, None otherwise
        """
        instance = cls.get_instance()
        instance._ensure_initialized()
        return instance._providers.get(provider_type)

    @classmethod
    def get_model_class(cls, provider_type: str) -> type[Model] | None:
        """Get PydanticAI Model class for provider.

        Args:
            provider_type: Provider identifier

        Returns:
            Model class if found, None otherwise
        """
        metadata = cls.get_provider_metadata(provider_type)
        return metadata.model_class if metadata else None

    @classmethod
    def is_supported(cls, provider_type: str) -> bool:
        """Check if provider is supported.

        Args:
            provider_type: Provider identifier

        Returns:
            True if provider is registered, False otherwise
        """
        instance = cls.get_instance()
        instance._ensure_initialized()
        return provider_type in instance._providers

    @classmethod
    def supports_streaming(cls, config: ProviderConfig) -> bool:
        """Check if provider/model combination supports streaming structured output.

        Uses a blacklist approach: most providers support streaming,
        only known problematic provider/model combinations return False.

        Known issues:
        - bedrock/*: Bedrock-Claude returns streaming as single chunk (Issue #1889)

        Args:
            config: Provider configuration with provider_type and model

        Returns:
            True if streaming is supported (default), False if known to not work
        """
        # Blacklist of provider/model combinations with known streaming issues
        # Format: (provider_type, model_pattern)
        # Use "*" as wildcard for all models of a provider
        streaming_blacklist = {
            ("bedrock", "*"),  # All Bedrock models: streaming returns as single chunk
            ("hugginface", "*"),  # HuggingFace Inference API may not support streaming properly
        }

        # Check exact matches first
        if (config.provider_type, config.model) in streaming_blacklist:
            return False

        # Check wildcard matches (provider_type, "*")
        if (config.provider_type, "*") in streaming_blacklist:
            return False

        return True
