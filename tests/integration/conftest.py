"""Shared test fixtures for integration tests."""

import json
import os
from pathlib import Path

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
def anthropic_config():
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


def get_source_language(test_data: dict[str, object]) -> str:
    source_lang = test_data["source_language"]

    assert isinstance(source_lang, str)
    return source_lang


def get_target_language(test_data: dict[str, object]) -> str:
    target_lang = test_data["target_language"]

    assert isinstance(target_lang, str)
    return target_lang


def get_test_cases(test_data: dict[str, object], start: int = 0, count: int = 5) -> list[dict[str, object]]:
    test_cases = test_data["test_cases"]
    assert isinstance(test_cases, list)

    start_idx = min(start, len(test_cases) - count)
    end_idx = min(start + count, len(test_cases))

    return test_cases[start_idx:end_idx]


def get_source_text(test_case: dict[str, object]) -> str:
    source_text = test_case["source_text"]
    assert isinstance(source_text, str)

    return source_text


def get_expected_text(test_case: dict[str, object]) -> str:
    expected_text = test_case["expected_word_by_word"]
    assert isinstance(expected_text, str)

    return expected_text


def load_test_data(file_name: str) -> dict[str, object]:
    """Load Unit 1.1 test cases from JSON fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / file_name
    with open(fixture_path) as f:
        return json.load(f)
