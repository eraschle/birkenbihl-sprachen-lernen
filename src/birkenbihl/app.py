"""Birkenbihl App - Shared application logic for CLI and GUI.

This module contains the core application logic that is independent of
the presentation layer (CLI or GUI). It provides factory functions for
creating services and handles configuration.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from birkenbihl.providers import AnthropicTranslator, OpenAITranslator
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage import JsonStorageProvider

# Load environment variables
load_dotenv()

# Environment variable configuration
DEFAULT_PROVIDER = os.getenv("BIRKENBIHL_PROVIDER", "openai")
DEFAULT_OPENAI_MODEL = os.getenv("BIRKENBIHL_OPENAI_MODEL", "openai:gpt-4o")
DEFAULT_ANTHROPIC_MODEL = os.getenv("BIRKENBIHL_ANTHROPIC_MODEL", "anthropic:claude-3-5-sonnet-20241022")
DEFAULT_STORAGE_PATH = os.getenv("BIRKENBIHL_STORAGE_PATH")


def get_translator(provider: str, model: str | None = None):
    """Create translator based on provider choice.

    Uses environment variables for default models if not specified.

    Args:
        provider: AI provider name (openai or anthropic)
        model: Optional model override

    Returns:
        Configured translator instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider == "openai":
        model = model or DEFAULT_OPENAI_MODEL
        return OpenAITranslator(model)
    elif provider == "anthropic":
        model = model or DEFAULT_ANTHROPIC_MODEL
        return AnthropicTranslator(model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_service(
    provider: str | None = None,
    model: str | None = None,
    storage_path: Path | None = None,
) -> TranslationService:
    """Create translation service with configured providers.

    Uses environment variables for defaults if not specified.

    Args:
        provider: AI provider name (defaults to env var)
        model: Optional model override (defaults to env var)
        storage_path: Optional storage path (defaults to env var or ~/.birkenbihl)

    Returns:
        Configured TranslationService instance
    """
    provider = provider or DEFAULT_PROVIDER
    translator = get_translator(provider, model)

    # Use env var default if no storage_path provided
    if storage_path is None and DEFAULT_STORAGE_PATH:
        storage_path = Path(DEFAULT_STORAGE_PATH)

    storage = JsonStorageProvider(storage_path)
    return TranslationService(translator, storage)
