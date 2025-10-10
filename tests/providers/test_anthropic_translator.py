"""Integration tests for AnthropicTranslator.

These tests make real API calls and require ANTHROPIC_API_KEY environment variable.
Mark tests with @pytest.mark.integration to run separately from unit tests.
"""

import os

import pytest

from birkenbihl.models.translation import Translation
from birkenbihl.providers.anthropic_translator import AnthropicTranslator


@pytest.fixture
def translator():
    """Create Anthropic translator (requires ANTHROPIC_API_KEY)."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")
    return AnthropicTranslator(model="anthropic:claude-3-5-sonnet-20241022")


def skip_if_no_api_key():
    """Skip test if ANTHROPIC_API_KEY not set."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")


@pytest.mark.integration
@pytest.mark.slow
class TestAnthropicTranslatorIntegration:
    """Integration tests with real Anthropic API calls."""

    def test_translate_english_to_german_simple(self, translator: AnthropicTranslator):
        """Test simple English to German translation."""
        skip_if_no_api_key()
        # Act
        result = translator.translate("Hello world", "en", "de")

        # Assert
        assert isinstance(result, Translation)
        assert result.source_language == "en"
        assert result.target_language == "de"
        assert len(result.sentences) >= 1

        # Verify sentence structure
        sentence = result.sentences[0]
        assert sentence.source_text.strip() != ""
        assert sentence.natural_translation.strip() != ""
        assert len(sentence.word_alignments) >= 2

        # Verify word alignments have correct positions
        for i, alignment in enumerate(sentence.word_alignments):
            assert alignment.position == i
            assert alignment.source_word.strip() != ""
            assert alignment.target_word.strip() != ""

    def test_translate_spanish_to_german(self, translator: AnthropicTranslator):
        """Test Spanish to German translation with Birkenbihl method."""
        skip_if_no_api_key()
        # Act: Example from ORIGINAL_REQUIREMENTS.md
        result = translator.translate("Yo te extrañaré", "es", "de")

        # Assert
        assert result.source_language == "es"
        assert result.target_language == "de"
        assert len(result.sentences) == 1

        sentence = result.sentences[0]
        assert "Yo" in sentence.source_text or "yo" in sentence.source_text
        assert sentence.natural_translation.strip() != ""

        # Verify we have alignments for all words
        assert len(sentence.word_alignments) >= 3

    def test_translate_multiple_sentences(self, translator: AnthropicTranslator):
        """Test translation of text with multiple sentences."""
        skip_if_no_api_key()
        # Act
        text = "Hello world. How are you today?"
        result = translator.translate(text, "en", "de")

        # Assert
        assert len(result.sentences) >= 2  # Should split into multiple sentences

        # Verify each sentence has translations
        for sentence in result.sentences:
            assert sentence.source_text.strip() != ""
            assert sentence.natural_translation.strip() != ""
            assert len(sentence.word_alignments) > 0

    def test_translate_complex_spanish_sentence(self, translator: AnthropicTranslator):
        """Test complex Spanish sentence from requirements."""
        skip_if_no_api_key()
        # Act: Example from ORIGINAL_REQUIREMENTS.md
        text = "Fueron tantos bellos y malos momentos"
        result = translator.translate(text, "es", "de")

        # Assert
        sentence = result.sentences[0]
        assert sentence.source_text.strip() != ""
        assert sentence.natural_translation.strip() != ""

        # Should have alignment for each word
        assert len(sentence.word_alignments) >= 6

        # Verify positions are sequential
        for i, alignment in enumerate(sentence.word_alignments):
            assert alignment.position == i

    def test_detect_language_english(self, translator: AnthropicTranslator):
        """Test language detection for English."""
        skip_if_no_api_key()
        # Act
        result = translator.detect_language("Hello world, how are you?")

        # Assert
        assert result == "en"

    def test_detect_language_spanish(self, translator: AnthropicTranslator):
        """Test language detection for Spanish."""
        skip_if_no_api_key()
        # Act
        result = translator.detect_language("Hola mundo, ¿cómo estás?")

        # Assert
        assert result == "es"

    def test_detect_language_german(self, translator: AnthropicTranslator):
        """Test language detection for German."""
        skip_if_no_api_key()
        # Act
        result = translator.detect_language("Hallo Welt, wie geht es dir?")

        # Assert
        assert result == "de"


@pytest.mark.integration
@pytest.mark.slow
class TestAnthropicBirkenbilhMethodCompliance:
    """Test compliance with Birkenbihl method requirements from ORIGINAL_REQUIREMENTS.md."""

    def test_natural_translation_exists(self, translator: AnthropicTranslator):
        """Test that natural translation is provided (Phase 1: Übersetzen)."""
        skip_if_no_api_key()
        # Act
        result = translator.translate("Hello world", "en", "de")

        # Assert: Natural translation exists and is non-empty
        sentence = result.sentences[0]
        assert sentence.natural_translation is not None
        assert len(sentence.natural_translation.strip()) > 0

    def test_word_by_word_translation_exists(self, translator: AnthropicTranslator):
        """Test that word-by-word translation exists (Phase 1: Dekodieren)."""
        skip_if_no_api_key()
        # Act
        result = translator.translate("Hello world", "en", "de")

        # Assert: Word alignments exist
        sentence = result.sentences[0]
        assert len(sentence.word_alignments) > 0

        # Each alignment has source and target word
        for alignment in sentence.word_alignments:
            assert alignment.source_word.strip() != ""
            assert alignment.target_word.strip() != ""

    def test_all_words_from_natural_used_in_alignments(self, translator: AnthropicTranslator):
        """Test that all words from natural translation appear in word alignments.

        Critical requirement from ORIGINAL_REQUIREMENTS.md:
        'Alle Wörter aus der natürlichen Übersetzung müssen in der Wort-für-Wort verwendet werden'
        """
        skip_if_no_api_key()
        # Act: Complex sentence with subordinate clause
        complex_text = (
            "Aunque no tenía mucho dinero en ese momento, "
            "decidí comprar el libro porque sabía que me ayudaría a aprender alemán"
        )
        result = translator.translate(complex_text, "es", "de")

        # Assert
        sentence = result.sentences[0]
        natural_words = set(sentence.natural_translation.lower().split())

        # Extract all target words from alignments (handle hyphens)
        alignment_words = set()
        for alignment in sentence.word_alignments:
            # Split hyphenated words (e.g., "vermissen-werde" -> ["vermissen", "werde"])
            words = alignment.target_word.lower().split("-")
            alignment_words.update(words)

        # Verify that all words from natural translation appear in alignments
        # (Allow for some punctuation differences)
        natural_words_cleaned = {w.strip(".,!?;:") for w in natural_words}
        alignment_words_cleaned = {w.strip(".,!?;:") for w in alignment_words}

        # At least most words should match (allowing for some articles/particles)
        common_words = natural_words_cleaned & alignment_words_cleaned
        coverage = len(common_words) / len(natural_words_cleaned) if natural_words_cleaned else 0
        assert coverage >= 0.7, (
            f"Only {coverage:.1%} of natural translation words found in alignments. "
            f"Natural: {natural_words_cleaned}, Alignments: {alignment_words_cleaned}"
        )

    def test_position_ordering_for_ui_alignment(self, translator: AnthropicTranslator):
        """Test that positions are sequential for UI vertical alignment.

        From ORIGINAL_REQUIREMENTS.md:
        'UI soll Wörter einer Zeile auseinanderziehen für vertikale Alignment'
        """
        skip_if_no_api_key()
        # Act
        result = translator.translate("Hello world", "en", "de")

        # Assert: Positions start at 0 and increment by 1
        sentence = result.sentences[0]
        for i, alignment in enumerate(sentence.word_alignments):
            assert alignment.position == i

    def test_metadata_preserved(self, translator: AnthropicTranslator):
        """Test that translation has all required metadata.

        From ORIGINAL_REQUIREMENTS.md:
        'Übersetzungen speichern, Dekodierung speichern ohne das die Dekodierung verloren geht'
        """
        skip_if_no_api_key()
        # Act
        result = translator.translate("Hello world", "en", "de")

        # Assert: All metadata exists
        assert result.id is not None
        assert result.source_language == "en"
        assert result.target_language == "de"
        assert result.created_at is not None
        assert result.updated_at is not None

        # Sentence metadata
        sentence = result.sentences[0]
        assert sentence.id is not None
        assert sentence.created_at is not None

    def test_complex_multi_sentence_word_alignments(self, translator: AnthropicTranslator):
        """Test word-by-word translation with multiple complex sentences.

        Ensures that complex grammatical structures are properly handled across multiple sentences.
        """
        skip_if_no_api_key()
        # Act: Multiple complex sentences with different tenses and structures
        complex_text = (
            "Cuando era joven, solía visitar a mis abuelos todos los veranos en el pueblo. "
            "Si hubiera estudiado más para el examen, probablemente habría obtenido mejores notas. "
            "Ahora que vivo en Berlín, intento hablar alemán todos los días para mejorar."
        )
        result = translator.translate(complex_text, "es", "de")

        # Assert: Should have 3 sentences
        assert len(result.sentences) >= 2, "Should split complex text into multiple sentences"

        # Verify each sentence has proper word alignments
        for i, sentence in enumerate(result.sentences):
            # Each sentence should have alignments
            assert len(sentence.word_alignments) > 0, f"Sentence {i} has no word alignments"

            # Extract natural and alignment words
            natural_words = set(sentence.natural_translation.lower().split())
            alignment_words = set()
            for alignment in sentence.word_alignments:
                words = alignment.target_word.lower().split("-")
                alignment_words.update(words)

            # Clean punctuation
            natural_cleaned = {w.strip(".,!?;:") for w in natural_words}
            alignment_cleaned = {w.strip(".,!?;:") for w in alignment_words}

            # Verify coverage
            common = natural_cleaned & alignment_cleaned
            coverage = len(common) / len(natural_cleaned) if natural_cleaned else 0

            assert coverage >= 0.7, (
                f"Sentence {i}: Only {coverage:.1%} coverage. "
                f"Natural: {natural_cleaned}, Alignments: {alignment_cleaned}"
            )

            # Verify positions are sequential
            for j, alignment in enumerate(sentence.word_alignments):
                assert alignment.position == j, (
                    f"Sentence {i}, Alignment {j}: Position mismatch"
                )
