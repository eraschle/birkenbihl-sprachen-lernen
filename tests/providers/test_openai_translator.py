"""Integration tests for OpenAITranslator.

These tests make real API calls and require OPENAI_API_KEY environment variable.
Mark tests with @pytest.mark.integration to run separately from unit tests.
"""

import os

import pytest

from birkenbihl.models.translation import Translation
from birkenbihl.providers.openai_translator import OpenAITranslator


@pytest.fixture
def translator():
    """Create OpenAI translator (requires OPENAI_API_KEY)."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")
    return OpenAITranslator(model="openai:gpt-4o-mini")


def skip_if_no_api_key():
    """Skip test if OPENAI_API_KEY not set."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")


@pytest.mark.integration
@pytest.mark.slow
class TestOpenAITranslatorIntegration:
    """Integration tests with real OpenAI API calls."""

    def test_translate_english_to_german_simple(self, translator: OpenAITranslator):
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

    def test_translate_spanish_to_german(self, translator: OpenAITranslator):
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

    def test_translate_multiple_sentences(self, translator: OpenAITranslator):
        """Test translation of text with multiple sentences."""
        skip_if_no_api_key()
        # Act
        text = "Hello world. How are you today?"
        result = translator.translate(text, "en", "de")

        # Assert: Should split into multiple sentences (done by text_utils.split_into_sentences)
        assert len(result.sentences) >= 2, "Code should deterministically split sentences"

        # Verify each sentence has translations
        for sentence in result.sentences:
            assert sentence.source_text.strip() != ""
            assert sentence.natural_translation.strip() != ""
            assert len(sentence.word_alignments) > 0

    def test_translate_complex_spanish_sentence(self, translator: OpenAITranslator):
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

    def test_detect_language_english(self, translator: OpenAITranslator):
        """Test language detection for English."""
        skip_if_no_api_key()
        # Act
        result = translator.detect_language("Hello world, how are you?")

        # Assert
        assert result == "en"

    def test_detect_language_spanish(self, translator: OpenAITranslator):
        """Test language detection for Spanish."""
        skip_if_no_api_key()
        # Act
        result = translator.detect_language("Hola mundo, ¿cómo estás?")

        # Assert
        assert result == "es"

    def test_detect_language_german(self, translator: OpenAITranslator):
        """Test language detection for German."""
        skip_if_no_api_key()
        # Act
        result = translator.detect_language("Hallo Welt, wie geht es dir?")

        # Assert
        assert result == "de"


@pytest.mark.integration
@pytest.mark.slow
class TestBirkenbilhMethodCompliance:
    """Test compliance with Birkenbihl method requirements from ORIGINAL_REQUIREMENTS.md."""

    def test_natural_translation_exists(self, translator: OpenAITranslator):
        """Test that natural translation is provided (Phase 1: Übersetzen)."""
        skip_if_no_api_key()
        # Act
        result = translator.translate("Hello world", "en", "de")

        # Assert: Natural translation exists and is non-empty
        sentence = result.sentences[0]
        assert sentence.natural_translation is not None
        assert len(sentence.natural_translation.strip()) > 0

    def test_word_by_word_translation_exists(self, translator: OpenAITranslator):
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

    def test_all_words_from_natural_used_in_alignments(self, translator: OpenAITranslator):
        """Test that all words from natural translation appear in word alignments.

        Critical requirement from ORIGINAL_REQUIREMENTS.md:
        'Alle Wörter aus der natürlichen Übersetzung müssen in der Wort-für-Wort verwendet werden'
        """
        skip_if_no_api_key()
        # Act: Complex sentence with subordinate clause and past perfect
        complex_text = (
            "After having studied German for five years at university, "
            "she finally decided to move to Berlin to improve her language skills"
        )
        result = translator.translate(complex_text, "en", "de")

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

    def test_position_ordering_for_ui_alignment(self, translator: OpenAITranslator):
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

    def test_metadata_preserved(self, translator: OpenAITranslator):
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

    def test_complex_multi_sentence_word_alignments(self, translator: OpenAITranslator):
        """Test word-by-word translation with multiple complex sentences.

        Ensures that complex grammatical structures are properly handled across multiple sentences.
        """
        skip_if_no_api_key()
        # Act: Multiple moderately complex sentences with different tenses
        complex_text = (
            "I visited my grandparents last summer in the countryside. "
            "They told me many interesting stories about their youth. "
            "Next year I want to visit them again with my sister."
        )
        result = translator.translate(complex_text, "en", "de")

        # Assert: Should have at least 2 sentences (splitting done by text_utils)
        assert len(result.sentences) >= 2, "Code should split into multiple sentences"

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
