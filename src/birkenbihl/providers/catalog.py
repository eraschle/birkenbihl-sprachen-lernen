"""The AI providers Birkenbihl supports and how to build a pydantic-ai model for each.

A deliberately small, fixed list: provider_type is stored in user settings, so it must not depend on how
pydantic-ai names its providers in a given release. Anything with an OpenAI-style API (Ollama, OpenRouter,
DeepSeek, Groq, LM Studio, ...) is reached through "openai-compatible" with its own URL.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import get_args

from pydantic_ai.exceptions import UserError
from pydantic_ai.models import KnownModelName, Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.typesafe import TypeSafeModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.typesafe import TypeSafeProvider

from birkenbihl.exceptions import ProviderError
from birkenbihl.models.settings import ProviderConfig


class ProviderType(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI_COMPATIBLE = "openai-compatible"


@dataclass(frozen=True)
class ProviderInfo:
    provider_type: ProviderType
    display_name: str
    requires_api_url: bool
    known_model_prefix: str | None  # prefix in pydantic-ai's KnownModelName, used for model suggestions


def _openai(config: ProviderConfig) -> Model:
    return OpenAIChatModel(config.model, provider=OpenAIProvider(api_key=config.api_key))


def _anthropic(config: ProviderConfig) -> Model:
    return AnthropicModel(config.model, provider=AnthropicProvider(api_key=config.api_key))


def _google(config: ProviderConfig) -> Model:
    return GoogleModel(config.model, provider=GoogleProvider(api_key=config.api_key))


def _openai_compatible(config: ProviderConfig) -> Model:
    if not config.api_url:
        raise ProviderError(f"Provider '{config.name}' needs an API URL (e.g. http://localhost:11434/v1 for Ollama)")
    provider = OpenAIProvider(base_url=config.api_url, api_key=config.api_key or None)
    return OpenAIChatModel(config.model, provider=provider)


_PROVIDERS: dict[ProviderType, tuple[ProviderInfo, Callable[[ProviderConfig], Model]]] = {
    ProviderType.OPENAI: (ProviderInfo(ProviderType.OPENAI, "OpenAI", False, "openai"), _openai),
    ProviderType.ANTHROPIC: (ProviderInfo(ProviderType.ANTHROPIC, "Anthropic Claude", False, "anthropic"), _anthropic),
    ProviderType.GOOGLE: (ProviderInfo(ProviderType.GOOGLE, "Google Gemini", False, "google"), _google),
    ProviderType.OPENAI_COMPATIBLE: (
        ProviderInfo(ProviderType.OPENAI_COMPATIBLE, "OpenAI-kompatibel (Ollama, OpenRouter, ...)", True, None),
        _openai_compatible,
    ),
}


def list_providers() -> list[ProviderInfo]:
    return [info for info, _ in _PROVIDERS.values()]


def get_provider_info(provider_type: str) -> ProviderInfo:
    """Raises ProviderError for provider types this app does not support."""
    return _PROVIDERS[_parse(provider_type)][0]


def is_supported(provider_type: str) -> bool:
    return provider_type in {member.value for member in ProviderType}


def suggested_models(provider_type: str) -> list[str]:
    """Model names pydantic-ai knows for this provider (empty for openai-compatible: any model name works)."""
    prefix = get_provider_info(provider_type).known_model_prefix
    if prefix is None:
        return []
    names = (name for name in get_args(KnownModelName.__value__) if isinstance(name, str))
    return [name.split(":", 1)[1] for name in names if name.split(":", 1)[0] == prefix]


def create_model(config: ProviderConfig) -> Model:
    """Build the pydantic-ai model for a configured provider, with the API key from the settings."""
    return _PROVIDERS[_parse(config.provider_type)][1](config)


# Jev is not a translation provider (it writes no text), only a word aligner, so it is not in _PROVIDERS.
# Pin a version (e.g. "jev-1.13.0") once the alignment thresholds are tuned against one.
JEV_MODEL = "jev-latest"


def create_jev_model(api_key: str | None) -> Model:
    """Jev (TypeSafe) model; without api_key, pydantic-ai reads TYPESAFE_API_KEY from the environment."""
    try:
        return TypeSafeModel(JEV_MODEL, provider=TypeSafeProvider(api_key=api_key))
    except UserError as error:
        raise ProviderError(
            f"Jev needs an API key: set jev_api_key in settings.yaml or TYPESAFE_API_KEY ({error})"
        ) from error


def _parse(provider_type: str) -> ProviderType:
    if not is_supported(provider_type):
        supported = ", ".join(member.value for member in ProviderType)
        raise ProviderError(f"Unsupported provider: {provider_type}. Supported providers: {supported}")
    return ProviderType(provider_type)
