"""Shared test fixtures for provider tests."""

import os

import pytest
from dotenv import load_dotenv

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.models import (
    SentenceResponse,
    TranslationResponse,
    WordAlignmentResponse,
)


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


@pytest.fixture
def sample_english_german_response():
    """Sample translation response: English -> German 'Hello world'."""
    return TranslationResponse(
        sentences=[
            SentenceResponse(
                source_text="Hello world",
                natural_translation="Hallo Welt",
                word_alignments=[
                    WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
                    WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
                ],
            )
        ]
    )


@pytest.fixture
def sample_spanish_german_response():
    """Sample translation response: Spanish -> German 'Yo te extrañaré'.

    Example from ORIGINAL_REQUIREMENTS.md demonstrating Birkenbihl method.
    """
    return TranslationResponse(
        sentences=[
            SentenceResponse(
                source_text="Yo te extrañaré",
                natural_translation="Ich werde dich vermissen",
                word_alignments=[
                    WordAlignmentResponse(source_word="Yo", target_word="Ich", position=0),
                    WordAlignmentResponse(source_word="te", target_word="dich", position=1),
                    WordAlignmentResponse(
                        source_word="extrañaré", target_word="vermissen-werde", position=2
                    ),
                ],
            )
        ]
    )


@pytest.fixture
def sample_multi_sentence_response():
    """Sample translation response with multiple sentences."""
    return TranslationResponse(
        sentences=[
            SentenceResponse(
                source_text="Hello world",
                natural_translation="Hallo Welt",
                word_alignments=[
                    WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
                    WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
                ],
            ),
            SentenceResponse(
                source_text="How are you",
                natural_translation="Wie geht es dir",
                word_alignments=[
                    WordAlignmentResponse(source_word="How", target_word="Wie", position=0),
                    WordAlignmentResponse(source_word="are", target_word="geht-es", position=1),
                    WordAlignmentResponse(source_word="you", target_word="dir", position=2),
                ],
            ),
        ]
    )


@pytest.fixture
def sample_complex_spanish_response():
    """Sample complex Spanish sentence from ORIGINAL_REQUIREMENTS.md.

    'Fueron tantos bellos y malos momentos'
    Demonstrates multiple words and compound translations.
    """
    return TranslationResponse(
        sentences=[
            SentenceResponse(
                source_text="Fueron tantos bellos y malos momentos",
                natural_translation="Waren so viele schöne und schlechte momente",
                word_alignments=[
                    WordAlignmentResponse(source_word="Fueron", target_word="Waren", position=0),
                    WordAlignmentResponse(source_word="tantos", target_word="so-viele", position=1),
                    WordAlignmentResponse(source_word="bellos", target_word="schöne", position=2),
                    WordAlignmentResponse(source_word="y", target_word="und", position=3),
                    WordAlignmentResponse(source_word="malos", target_word="schlechte", position=4),
                    WordAlignmentResponse(
                        source_word="momentos", target_word="momente", position=5
                    ),
                ],
            )
        ]
    )


@pytest.fixture
def sample_dekodierung_example():
    """Sample dekodierung example from ORIGINAL_REQUIREMENTS.md.

    'Lo que parecía no importante' -> 'Das was schien nicht wichtig'
    Demonstrates word alignment formatting with proper spacing.
    """
    return TranslationResponse(
        sentences=[
            SentenceResponse(
                source_text="Lo que parecía no importante",
                natural_translation="Das was schien nicht wichtig",
                word_alignments=[
                    WordAlignmentResponse(source_word="Lo", target_word="Das", position=0),
                    WordAlignmentResponse(source_word="que", target_word="was", position=1),
                    WordAlignmentResponse(source_word="parecía", target_word="schien", position=2),
                    WordAlignmentResponse(source_word="no", target_word="nicht", position=3),
                    WordAlignmentResponse(
                        source_word="importante", target_word="wichtig", position=4
                    ),
                ],
            )
        ]
    )
