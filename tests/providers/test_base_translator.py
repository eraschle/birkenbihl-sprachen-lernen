"""Unit tests for BaseTranslator.

Tests the core translation logic with mocked AI responses.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID

import pytest

from birkenbihl.models.translation import Translation
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.models import (
    SentenceResponse,
    TranslationResponse,
    WordAlignmentResponse,
)


@pytest.fixture
def mock_model():
    """Create a mock PydanticAI Model."""
    return MagicMock()


@pytest.fixture
def mock_agent():
    """Create a mock PydanticAI Agent."""
    with patch("birkenbihl.providers.base_translator.Agent") as mock_agent_class:
        mock_instance = MagicMock()
        mock_agent_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def base_translator(mock_agent, mock_model):
    """Create BaseTranslator with mocked Agent."""
    return BaseTranslator(mock_model)


@pytest.mark.unit
class TestBaseTranslator:
    """Test BaseTranslator core functionality."""

    def test_initialization(self, mock_agent, mock_model):
        """Test translator initialization creates Agent correctly."""
        BaseTranslator(mock_model)

        # Verify Agent was created with correct parameters
        from birkenbihl.providers.base_translator import Agent
        from birkenbihl.providers.models import TranslationResponse
        from birkenbihl.providers.prompts import BIRKENBIHL_SYSTEM_PROMPT

        Agent.assert_called_once_with(  # type: ignore[reportAttributeAccessIssue]
            model=mock_model,
            output_type=TranslationResponse,
            system_prompt=BIRKENBIHL_SYSTEM_PROMPT,
        )

    def test_translate_single_sentence(self, base_translator: BaseTranslator, mock_agent):
        """Test translation of single sentence returns correct domain model."""
        # Arrange: Mock AI response
        mock_response = TranslationResponse(
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
        mock_result = Mock()
        mock_result.output = mock_response
        mock_agent.run_sync.return_value = mock_result

        # Act
        result = base_translator.translate("Hello world", "en", "de")

        # Assert: Verify domain model structure
        assert isinstance(result, Translation)
        assert result.source_language == "en"
        assert result.target_language == "de"
        assert len(result.sentences) == 1
        assert isinstance(result.uuid, UUID)
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

        # Assert: Verify sentence data
        sentence = result.sentences[0]
        assert sentence.source_text == "Hello world"
        assert sentence.natural_translation == "Hallo Welt"
        assert len(sentence.word_alignments) == 2

        # Assert: Verify word alignments
        assert sentence.word_alignments[0].source_word == "Hello"
        assert sentence.word_alignments[0].target_word == "Hallo"
        assert sentence.word_alignments[0].position == 0

        assert sentence.word_alignments[1].source_word == "world"
        assert sentence.word_alignments[1].target_word == "Welt"
        assert sentence.word_alignments[1].position == 1

    def test_translate_multiple_sentences(self, base_translator: BaseTranslator, mock_agent):
        """Test translation of multiple sentences."""
        # Arrange: Mock AI response with 2 sentences
        mock_response = TranslationResponse(
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
        mock_result = Mock()
        mock_result.output = mock_response
        mock_agent.run_sync.return_value = mock_result

        # Act
        result = base_translator.translate("Hello world. How are you", "en", "de")

        # Assert
        assert len(result.sentences) == 2
        assert result.sentences[0].source_text == "Hello world"
        assert result.sentences[1].source_text == "How are you"
        assert result.sentences[1].natural_translation == "Wie geht es dir"

    def test_translate_spanish_to_german(self, base_translator: BaseTranslator, mock_agent):
        """Test Spanish to German translation (Birkenbihl method focus)."""
        # Arrange: Example from ORIGINAL_REQUIREMENTS.md
        mock_response = TranslationResponse(
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
        mock_result = Mock()
        mock_result.output = mock_response
        mock_agent.run_sync.return_value = mock_result

        # Act
        result = base_translator.translate("Yo te extrañaré", "es", "de")

        # Assert
        sentence = result.sentences[0]
        assert sentence.source_text == "Yo te extrañaré"
        assert sentence.natural_translation == "Ich werde dich vermissen"

        # Verify word alignments follow Birkenbihl format
        assert len(sentence.word_alignments) == 3
        assert sentence.word_alignments[2].source_word == "extrañaré"
        assert (
            sentence.word_alignments[2].target_word == "vermissen-werde"
        )  # Compound word with hyphen

    def test_detect_language_english(self, base_translator: BaseTranslator):
        """Test language detection for English text."""
        with patch("birkenbihl.providers.base_translator.detector_factory.detect") as mock_detect:
            mock_detect.return_value = "en"

            result = base_translator.detect_language("Hello world")

            assert result == "en"
            mock_detect.assert_called_once_with("Hello world")

    def test_detect_language_spanish(self, base_translator: BaseTranslator):
        """Test language detection for Spanish text."""
        with patch("birkenbihl.providers.base_translator.detector_factory.detect") as mock_detect:
            mock_detect.return_value = "es"

            result = base_translator.detect_language("Hola mundo")

            assert result == "es"

    def test_detect_language_german(self, base_translator: BaseTranslator):
        """Test language detection for German text."""
        with patch("birkenbihl.providers.base_translator.detector_factory.detect") as mock_detect:
            mock_detect.return_value = "de"

            result = base_translator.detect_language("Hallo Welt")

            assert result == "de"

    def test_convert_to_domain_model_preserves_uuids(self, base_translator: BaseTranslator):
        """Test that converting to domain model generates unique UUIDs."""
        # Arrange
        response = TranslationResponse(
            sentences=[
                SentenceResponse(
                    source_text="Test",
                    natural_translation="Test",
                    word_alignments=[
                        WordAlignmentResponse(source_word="Test", target_word="Test", position=0),
                    ],
                )
            ]
        )

        # Act: Convert twice
        result1 = base_translator._convert_to_domain_model(response, "en", "de")
        result2 = base_translator._convert_to_domain_model(response, "en", "de")

        # Assert: Each conversion creates unique UUIDs
        assert result1.uuid != result2.uuid
        assert result1.sentences[0].uuid != result2.sentences[0].uuid

    def test_convert_to_domain_model_timestamps(self, base_translator: BaseTranslator):
        """Test that domain model has proper timestamps."""
        # Arrange
        response = TranslationResponse(
            sentences=[
                SentenceResponse(
                    source_text="Test",
                    natural_translation="Test",
                    word_alignments=[
                        WordAlignmentResponse(source_word="Test", target_word="Test", position=0),
                    ],
                )
            ]
        )

        # Act
        result = base_translator._convert_to_domain_model(response, "en", "de")

        # Assert
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)
        assert result.created_at == result.updated_at  # Should be same on creation
        assert result.sentences[0].created_at is not None


@pytest.mark.unit
class TestBirkenbilFormatValidation:
    """Test Birkenbihl method format requirements."""

    def test_word_alignment_position_ordering(self, base_translator: BaseTranslator, mock_agent):
        """Test that word alignments maintain correct position ordering."""
        # Arrange: Example from ORIGINAL_REQUIREMENTS.md
        mock_response = TranslationResponse(
            sentences=[
                SentenceResponse(
                    source_text="Lo que parecía no importante",
                    natural_translation="Das was schien nicht wichtig",
                    word_alignments=[
                        WordAlignmentResponse(source_word="Lo", target_word="Das", position=0),
                        WordAlignmentResponse(source_word="que", target_word="was", position=1),
                        WordAlignmentResponse(
                            source_word="parecía", target_word="schien", position=2
                        ),
                        WordAlignmentResponse(source_word="no", target_word="nicht", position=3),
                        WordAlignmentResponse(
                            source_word="importante", target_word="wichtig", position=4
                        ),
                    ],
                )
            ]
        )
        mock_result = Mock()
        mock_result.output = mock_response
        mock_agent.run_sync.return_value = mock_result

        # Act
        result = base_translator.translate("Lo que parecía no importante", "es", "de")

        # Assert: Positions are sequential and start at 0
        alignments = result.sentences[0].word_alignments
        for i, alignment in enumerate(alignments):
            assert alignment.position == i

    def test_hyphenated_compound_words(self, base_translator: BaseTranslator, mock_agent):
        """Test that compound translations use hyphens correctly."""
        # Arrange: Example with compound word
        mock_response = TranslationResponse(
            sentences=[
                SentenceResponse(
                    source_text="Fueron tantos bellos y malos momentos",
                    natural_translation="Waren so viele schöne und schlechte momente",
                    word_alignments=[
                        WordAlignmentResponse(
                            source_word="Fueron", target_word="Waren", position=0
                        ),
                        WordAlignmentResponse(
                            source_word="tantos", target_word="so-viele", position=1
                        ),
                        WordAlignmentResponse(
                            source_word="bellos", target_word="schöne", position=2
                        ),
                        WordAlignmentResponse(source_word="y", target_word="und", position=3),
                        WordAlignmentResponse(
                            source_word="malos", target_word="schlechte", position=4
                        ),
                        WordAlignmentResponse(
                            source_word="momentos", target_word="momente", position=5
                        ),
                    ],
                )
            ]
        )
        mock_result = Mock()
        mock_result.output = mock_response
        mock_agent.run_sync.return_value = mock_result

        # Act
        result = base_translator.translate("Fueron tantos bellos y malos momentos", "es", "de")

        # Assert: Compound word uses hyphen
        alignments = result.sentences[0].word_alignments
        assert alignments[1].target_word == "so-viele"  # Compound with hyphen
