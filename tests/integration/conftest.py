"""Shared test fixtures for integration tests."""

import os

import pytest
from dotenv import load_dotenv

from birkenbihl.models.settings import ProviderConfig


@pytest.fixture
def openai_provider_config():
    """Create OpenAI ProviderConfig from environment variable.

    Requires OPENAI_API_KEY environment variable.
    """
    if "OPENAI_API_KEY" not in os.environ:
        load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")

    return ProviderConfig(
        name="OpenAI GPT-4o Mini",
        provider_type="openai",
        model="gpt-4o-mini",
        api_key=api_key,
        is_default=True,
    )


@pytest.fixture
def anthropic_provider_config():
    """Create Anthropic ProviderConfig from environment variable.

    Requires ANTHROPIC_API_KEY environment variable.
    """
    if "ANTHROPIC_API_KEY" not in os.environ:
        load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")

    return ProviderConfig(
        name="Claude Sonnet",
        provider_type="anthropic",
        model="claude-3-5-sonnet-20241022",
        api_key=api_key,
        is_default=True,
    )
