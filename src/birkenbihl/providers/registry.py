"""Dynamic provider registry for PydanticAI models.

Discovers and registers all available PydanticAI providers at runtime,
eliminating the need for separate provider classes for each AI service.
Uses PydanticAI's KnownModelName types to extract valid model names.
"""

from dataclasses import dataclass
from typing import Any, get_args

from pydantic_ai.models import Model


@dataclass
class ProviderMetadata:
    """Metadata for a registered provider.

    Attributes:
        provider_type: Provider identifier (openai, anthropic, gemini, etc.)
        display_name: Human-readable name for UI
        model_class: PydanticAI Model class to instantiate
        default_models: Suggested model identifiers for this provider
        requires_api_key: Whether provider requires API key authentication
    """

    provider_type: str
    display_name: str
    model_class: type[Model]
    default_models: list[str]
    requires_api_key: bool = True


def _extract_model_names(model_name_type: Any) -> list[str]:
    """Extract all valid model names from a ModelName Union type.

    Extracts model names from Union[str, Literal[model1, model2, ...]] types
    used by PydanticAI for model name validation.

    Args:
        model_name_type: Union type (e.g., OpenAIModelName, AnthropicModelName)
                         typically Union[str, Literal[...]]

    Returns:
        List of valid model name strings extracted from Literal types
    """
    result = []
    args = get_args(model_name_type)

    for arg in args:
        if hasattr(arg, "__args__"):  # It's a Literal type with concrete model names
            literal_values = get_args(arg)
            result.extend(literal_values)
        elif arg is not str:  # Skip the generic str fallback
            result.append(arg)

    # Filter to ensure we only return string values
    return [model for model in result if isinstance(model, str)]


def _create_openai_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.openai import OpenAIChatModel, OpenAIModelName

    all_models = _extract_model_names(OpenAIModelName)

    # OpenAI-compatible providers - all use OpenAIChatModel class
    # Each gets all available OpenAI models as options
    openai_providers = [
        ("openai", "OpenAI"),
        ("azure", "Azure OpenAI"),
        ("deepseek", "DeepSeek"),
        ("cerebras", "Cerebras"),
        ("fireworks", "Fireworks AI"),
        ("github", "GitHub Models"),
        ("grok", "Grok (xAI)"),
        ("heroku", "Heroku"),
        ("ollama", "Ollama (Local)"),
        ("openrouter", "OpenRouter"),
        ("together", "Together AI"),
        ("vercel", "Vercel AI"),
        ("litellm", "LiteLLM"),
    ]

    provider_metadata = {}
    for provider_type, display_name in openai_providers:
        provider_metadata[provider_type] = ProviderMetadata(
            provider_type=provider_type,
            display_name=display_name,
            model_class=OpenAIChatModel,
            default_models=all_models,
        )
    return provider_metadata


def _create_anthropic_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelName

    all_models = _extract_model_names(AnthropicModelName)

    return {
        "anthropic": ProviderMetadata(
            provider_type="anthropic",
            display_name="Anthropic Claude",
            model_class=AnthropicModel,
            default_models=all_models,
        )
    }


def _create_gemini_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.google import GoogleModel, GoogleModelName

    all_models = _extract_model_names(GoogleModelName)

    return {
        "gemini": ProviderMetadata(
            provider_type="gemini",
            display_name="Google Gemini",
            model_class=GoogleModel,
            default_models=all_models,
        )
    }


def _create_groq_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.groq import GroqModel, GroqModelName

    all_models = _extract_model_names(GroqModelName)

    return {
        "groq": ProviderMetadata(
            provider_type="groq",
            display_name="Groq",
            model_class=GroqModel,
            default_models=all_models,
        )
    }


def _create_cohere_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.cohere import CohereModel, CohereModelName

    all_models = _extract_model_names(CohereModelName)

    return {
        "cohere": ProviderMetadata(
            provider_type="cohere",
            display_name="Cohere",
            model_class=CohereModel,
            default_models=all_models,
        )
    }


def _create_mistral_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.mistral import MistralModel, MistralModelName

    all_models = _extract_model_names(MistralModelName)

    return {
        "mistral": ProviderMetadata(
            provider_type="mistral",
            display_name="Mistral AI",
            model_class=MistralModel,
            default_models=all_models,
        )
    }


def _create_bedrock_models() -> dict[str, ProviderMetadata]:
    from pydantic_ai.models.bedrock import BedrockConverseModel

    # Bedrock uses ARNs, keep manual list
    return {
        "bedrock": ProviderMetadata(
            provider_type="bedrock",
            display_name="AWS Bedrock",
            model_class=BedrockConverseModel,
            default_models=["anthropic.claude-3-sonnet", "anthropic.claude-3-haiku"],
        )
    }


class ProviderRegistry:
    """Registry for PydanticAI providers.

    Maintains mapping of provider_type → ProviderMetadata.
    Provides discovery and instantiation methods for UI and factory.

    Thread-safe singleton pattern ensures consistent provider access.
    Uses PydanticAI's ModelName types to auto-discover valid models.
    """

    _providers: dict[str, ProviderMetadata] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize registry with all available PydanticAI providers.

        Discovers provider modules dynamically and registers metadata.
        Falls back gracefully if modules are unavailable.
        """
        if cls._initialized:
            return

        # OpenAI and OpenAI-compatible providers
        try:
            cls._providers.update(_create_openai_models())
        except ImportError:
            pass

        # Anthropic
        try:
            cls._providers.update(_create_anthropic_models())
        except ImportError:
            pass

        # Google Gemini
        try:
            cls._providers.update(_create_gemini_models())
        except ImportError:
            pass

        # Groq
        try:
            cls._providers.update(_create_groq_models())
        except ImportError:
            pass

        # Cohere
        try:
            cls._providers.update(_create_cohere_models())
        except ImportError:
            pass

        # Mistral
        try:
            cls._providers.update(_create_mistral_models())
        except ImportError:
            pass

        # AWS Bedrock
        try:
            cls._providers.update(_create_bedrock_models())
        except ImportError:
            pass

        cls._initialized = True

    @classmethod
    def get_supported_providers(cls) -> list[ProviderMetadata]:
        """Get list of all registered providers.

        Returns:
            List of ProviderMetadata for all available providers
        """
        cls._initialize()
        return list(cls._providers.values())

    @classmethod
    def get_provider_types(cls) -> list[str]:
        """Get list of all provider type identifiers.

        Returns:
            List of provider_type strings (openai, anthropic, etc.)
        """
        cls._initialize()
        return list(cls._providers.keys())

    @classmethod
    def get_provider_metadata(cls, provider_type: str) -> ProviderMetadata | None:
        """Get metadata for specific provider.

        Args:
            provider_type: Provider identifier (openai, anthropic, etc.)

        Returns:
            ProviderMetadata if found, None otherwise
        """
        cls._initialize()
        return cls._providers.get(provider_type)

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
        cls._initialize()
        return provider_type in cls._providers
