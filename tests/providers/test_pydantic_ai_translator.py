"""Tests for universal PydanticAITranslator.

Tests cover both unit tests (mocking) and integration tests (real API calls).
Integration tests require appropriate API keys for each provider.
"""

import pytest

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.language_service import get_language_by


@pytest.mark.unit
class TestPydanticAITranslatorUnit:
    """Unit tests for PydanticAITranslator factory logic."""

    def test_unsupported_provider_raises_value_error(self):
        """Test that unsupported provider_type raises ValueError."""
        # Arrange
        config = ProviderConfig(
            name="Unknown Provider",
            provider_type="unsupported_provider",
            model="some-model",
            api_key="fake-key",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported provider: unsupported_provider") as exc_info:
            PydanticAITranslator(config)

        assert "Supported providers:" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorOpenAIIntegration:
    """Integration tests with OpenAI provider."""

    def test_translate_with_openai(self, openai_provider_config: ProviderConfig):
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

    def test_detect_language_with_openai(self, openai_provider_config: ProviderConfig):
        """Test language detection using OpenAI through universal translator."""
        # Arrange
        translator = PydanticAITranslator(openai_provider_config)

        # Act
        result = translator.detect_language("Hola mundo")

        # Assert
        assert result.code == "es"


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorAnthropicIntegration:
    """Integration tests with Anthropic provider."""

    def test_translate_with_anthropic(self, anthropic_provider_config: ProviderConfig):
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

    def test_detect_language_with_anthropic(self, anthropic_provider_config: ProviderConfig):
        """Test language detection using Anthropic through universal translator."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)

        # Act
        result = translator.detect_language("Hello world, how are you?")

        # Assert
        assert result.code == "en"

    def test_spanish_translation_with_anthropic(self, anthropic_provider_config: ProviderConfig):
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
    ):
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

    def test_consistent_language_detection_openai_vs_anthropic(
        self, openai_provider_config: ProviderConfig, anthropic_provider_config: ProviderConfig
    ):
        """Test that language detection is consistent across providers."""
        # Arrange
        openai_translator = PydanticAITranslator(openai_provider_config)
        anthropic_translator = PydanticAITranslator(anthropic_provider_config)

        test_cases = [
            ("Hello world, how are you?", "en"),
            ("Hola mundo, ¿cómo estás?", "es"),
            ("Hallo Welt, wie geht es dir?", "de"),
        ]

        # Act & Assert
        for text, expected_lang in test_cases:
            openai_lang = openai_translator.detect_language(text)
            anthropic_lang = anthropic_translator.detect_language(text)

            assert openai_lang.code == expected_lang
            assert anthropic_lang.code == expected_lang


@pytest.mark.integration
@pytest.mark.slow
class TestPydanticAITranslatorBirkenbilhCompliance:
    """Test Birkenbihl method compliance using universal translator."""

    def test_natural_and_word_alignments_present(self, openai_provider_config: ProviderConfig):
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

        for alignment in sentence.word_alignments:
            assert alignment.source_word.strip() != ""
            assert alignment.target_word.strip() != ""

    def test_word_alignment_positions_sequential(self, anthropic_provider_config: ProviderConfig):
        """Test that word alignment positions are sequential."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)

        # Act
        result = translator.translate("Hello world", get_language_by("en"), get_language_by("de"))

        # Assert
        sentence = result.sentences[0]
        for i, alignment in enumerate(sentence.word_alignments):
            assert alignment.position == i

    def test_metadata_present_in_translation(self, openai_provider_config: ProviderConfig):
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
    """Tests for translation editing features (generate_alternatives, regenerate_alignment)."""

    def test_generate_alternatives_returns_multiple(self, openai_provider_config: ProviderConfig):
        """Test that generate_alternatives returns multiple translation options."""
        # Arrange
        translator = PydanticAITranslator(openai_provider_config)
        source_text = "Yo te extrañaré"

        # Act
        alternatives = translator.generate_alternatives(
            source_text, get_language_by("es"), get_language_by("de"), count=3
        )

        # Assert
        assert isinstance(alternatives, list)
        assert len(alternatives) == 3
        assert all(isinstance(alt, str) for alt in alternatives)
        assert all(len(alt.strip()) > 0 for alt in alternatives)
        # Should have different translations
        assert len(set(alternatives)) >= 2  # At least 2 unique alternatives

    def test_generate_alternatives_custom_count(self, anthropic_provider_config: ProviderConfig):
        """Test that generate_alternatives respects custom count parameter."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)
        source_text = "Hello world"

        # Act
        alternatives = translator.generate_alternatives(
            source_text, get_language_by("en"), get_language_by("de"), count=5
        )

        # Assert
        assert len(alternatives) == 5
        assert all(isinstance(alt, str) for alt in alternatives)
        assert all(len(alt.strip()) > 0 for alt in alternatives)

    def test_regenerate_alignment_creates_valid_alignments(self, openai_provider_config: ProviderConfig):
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

        # Check all alignments are valid WordAlignment objects
        for i, alignment in enumerate(alignments):
            assert alignment.source_word.strip() != ""
            assert alignment.target_word.strip() != ""
            assert alignment.position == i  # Sequential positions

    def test_regenerate_alignment_preserves_all_words(self, anthropic_provider_config: ProviderConfig):
        """Test that regenerate_alignment includes all words from natural translation."""
        # Arrange
        translator = PydanticAITranslator(anthropic_provider_config)
        source_text = "Hello world"
        natural_translation = "Hallo Welt"

        # Act
        alignments = translator.regenerate_alignment(
            source_text, natural_translation, get_language_by("en"), get_language_by("de")
        )

        # Assert
        # Extract all target words from alignments (handle hyphenated combinations)
        target_words = []
        for alignment in alignments:
            if "-" in alignment.target_word:
                target_words.extend(alignment.target_word.split("-"))
            else:
                target_words.append(alignment.target_word)

        # All words from natural_translation should be present (case-insensitive)
        natural_words = natural_translation.split()
        natural_words_lower = [w.lower() for w in natural_words]
        target_words_lower = [w.lower() for w in target_words]

        for word in natural_words_lower:
            assert word in target_words_lower, f"Word '{word}' from natural translation not found in alignments"
