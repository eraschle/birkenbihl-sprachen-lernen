"""Tests for universal PydanticAITranslator.

Tests cover both unit tests (mocking) and integration tests (real API calls).
Integration tests require appropriate API keys for each provider.
"""

import pytest

from birkenbihl.exceptions import ProviderError
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.language_service import get_language_by


@pytest.mark.unit
class TestPydanticAITranslatorUnit:
    """Unit tests for PydanticAITranslator factory logic."""

    def test_unsupported_provider_raises_provider_error(self) -> None:
        """Test that unsupported provider_type raises ProviderError."""
        # Arrange
        config = ProviderConfig(
            name="Unknown Provider",
            provider_type="unsupported_provider",
            model="some-model",
            api_key="fake-key",
        )

        # Act & Assert
        with pytest.raises(ProviderError, match="Unsupported provider: unsupported_provider") as exc_info:
            PydanticAITranslator(config)

        assert "Supported providers:" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorOpenAIIntegration:
    """Integration tests with OpenAI provider."""

    def test_translate_with_openai(self, openai_provider_config: ProviderConfig) -> None:
        """Test translation using OpenAI through universal translator."""
        # Arrange
        translator = PydanticAITranslator(openai_provider_config)

        # Act
        result = translator.translate("Hello world", get_language_by("en"), get_language_by("de"))

        # Assert
        assert isinstance(result, Translation)
        assert result.source_language.code == "en"
        assert result.target_language.code == "de"
        assert len(result.sentences) >= 1

        sentence = result.sentences[0]
        assert sentence.source_text.strip() != ""
        assert sentence.natural_translation.strip() != ""
        assert len(sentence.word_alignments) >= 2


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorAnthropicIntegration:
    """Integration tests with Anthropic provider."""

    def test_translate_with_anthropic(self, anthropic_provider_config: ProviderConfig) -> None:
        """Test translation using Anthropic through universal translator."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)

        # Act
        result = translator.translate("Hello world", get_language_by("en"), get_language_by("de"))

        # Assert
        assert isinstance(result, Translation)
        assert result.source_language.code == "en"
        assert result.target_language.code == "de"
        assert len(result.sentences) >= 1

        sentence = result.sentences[0]
        assert sentence.source_text.strip() != ""
        assert sentence.natural_translation.strip() != ""
        assert len(sentence.word_alignments) >= 2

    def test_spanish_translation_with_anthropic(self, anthropic_provider_config: ProviderConfig) -> None:
        """Test Spanish to German translation using Anthropic."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)

        # Act
        result = translator.translate("Yo te extrañaré", get_language_by("es"), get_language_by("de"))

        # Assert
        assert result.source_language.code == "es"
        assert result.target_language.code == "de"
        assert len(result.sentences) == 1

        sentence = result.sentences[0]
        assert "Yo" in sentence.source_text or "yo" in sentence.source_text
        assert sentence.natural_translation.strip() != ""
        assert len(sentence.word_alignments) >= 3


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorMultiProviderCompatibility:
    """Test that universal translator works consistently across providers."""

    def test_consistent_translation_structure_openai_vs_anthropic(
        self, openai_provider_config: ProviderConfig, anthropic_provider_config: ProviderConfig
    ) -> None:
        """Test that both providers return consistent Translation structure."""
        # Arrange
        text = "Hello world"
        openai_translator = PydanticAITranslator(openai_provider_config)
        anthropic_translator = PydanticAITranslator(anthropic_provider_config)

        # Act
        openai_result = openai_translator.translate(text, get_language_by("en"), get_language_by("de"))
        anthropic_result = anthropic_translator.translate(text, get_language_by("en"), get_language_by("de"))

        # Assert: Both should have same structure
        assert isinstance(openai_result, Translation)
        assert isinstance(anthropic_result, Translation)

        assert openai_result.source_language.code == anthropic_result.source_language.code == "en"
        assert openai_result.target_language.code == anthropic_result.target_language.code == "de"

        # Both should have sentences
        assert len(openai_result.sentences) >= 1
        assert len(anthropic_result.sentences) >= 1

        # Both should have word alignments
        assert len(openai_result.sentences[0].word_alignments) >= 2
        assert len(anthropic_result.sentences[0].word_alignments) >= 2


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorBirkenbilhCompliance:
    """Test Birkenbihl method compliance using universal translator."""

    def test_natural_and_word_alignments_present(self, openai_provider_config: ProviderConfig) -> None:
        """Test that both natural translation and word alignments are provided."""
        # Arrange
        translator = PydanticAITranslator(openai_provider_config)

        # Act
        result = translator.translate("Hello world", get_language_by("en"), get_language_by("de"))

        # Assert
        sentence = result.sentences[0]
        assert sentence.natural_translation is not None
        assert len(sentence.natural_translation.strip()) > 0
        assert len(sentence.word_alignments) > 0

        assert [a.source_index for a in sentence.word_alignments] == list(range(len(sentence.source_tokens)))

    def test_one_alignment_per_source_word(self, anthropic_provider_config: ProviderConfig) -> None:
        """Test that every source word gets exactly one alignment, in source order."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)

        # Act
        result = translator.translate("Hello world", get_language_by("en"), get_language_by("de"))

        # Assert
        sentence = result.sentences[0]
        assert [a.source_index for a in sentence.word_alignments] == list(range(len(sentence.source_tokens)))

    def test_metadata_present_in_translation(self, openai_provider_config: ProviderConfig) -> None:
        """Test that translation includes all required metadata."""
        # Arrange
        translator = PydanticAITranslator(openai_provider_config)

        # Act
        result = translator.translate("Hello world", get_language_by("en"), get_language_by("de"))

        # Assert
        assert result.uuid is not None
        assert result.source_language.code == "en"
        assert result.target_language.code == "de"
        assert result.created_at is not None
        assert result.updated_at is not None

        sentence = result.sentences[0]
        assert sentence.uuid is not None
        assert sentence.created_at is not None


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorEditingFeatures:
    """Tests for regenerating the word-by-word alignment."""

    def test_regenerate_alignment_creates_valid_alignments(self, openai_provider_config: ProviderConfig) -> None:
        """Test that regenerate_alignment creates valid WordAlignment objects."""
        # Arrange
        translator = PydanticAITranslator(openai_provider_config)
        source_text = "Yo te extrañaré"
        natural_translation = "Ich werde dich vermissen"

        # Act
        alignments = translator.regenerate_alignment(
            source_text, natural_translation, get_language_by("es"), get_language_by("de")
        )

        # Assert
        assert isinstance(alignments, list)
        assert len(alignments) > 0

        # One alignment per source word ("Hello", "world"), in source order
        assert [a.source_index for a in alignments] == [0, 1]

    def test_regenerate_alignment_preserves_all_words(self, anthropic_provider_config: ProviderConfig) -> None:
        """Test that regenerate_alignment includes all words from natural translation."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)
        source_text = "Hello world"
        natural_translation = "Hallo Welt"

        # Act
        alignments = translator.regenerate_alignment(
            source_text, natural_translation, get_language_by("en"), get_language_by("de")
        )

        # Assert: every word of the natural translation is assigned
        sentence = Sentence(
            source_text=source_text, natural_translation=natural_translation, word_alignments=alignments
        )
        assert sentence.unassigned_target_indices() == []
