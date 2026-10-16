"""Integration tests for Birkenbihl Unit 1.1 word-by-word translations.

Tests validate the translator's word-by-word output against expected translations
from the official Birkenbihl method Unit 1.1 material.
"""

import pytest

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from integration import conftest


@pytest.mark.integration
@pytest.mark.slow
class TestBirkenbihUnit11WordByWord:
    """Test word-by-word translations against Unit 1.1 expected outputs."""

    @pytest.fixture(scope="class")
    def test_data(self) -> dict[str, object]:
        """Fixture providing Unit 1.1 test cases."""
        return conftest.load_test_data("birkenbihl_unit1_1.json")

    def test_fixture_loaded(self, test_data: dict[str, object]) -> None:
        """Verify fixture loads correctly with expected structure."""

        assert "test_cases" in test_data
        assert isinstance(test_data["test_cases"], list)
        assert len(test_data["test_cases"]) > 0
        assert test_data["source_language"] == "en"
        assert test_data["target_language"] == "de"

    def test_word_by_word_translation_accuracy(
        self, test_data: dict[str, object], anthropic_config: ProviderConfig
    ) -> None:
        """Test word-by-word translation accuracy against all Unit 1.1 cases.

        This test translates each source_text and compares the generated word-by-word
        translation against the expected output from the Birkenbihl material.

        Note: The translator may split input into multiple sentences. We combine all
        word alignments from all sentences for comparison.
        """
        translator = PydanticAITranslator(anthropic_config)
        source_lang = conftest.get_source_language(test_data)
        target_lang = conftest.get_target_language(test_data)

        failed_cases = []

        for idx, test_case in enumerate(conftest.get_test_cases(test_data)):
            source_text = conftest.get_source_text(test_case)
            expected_word_by_word = conftest.get_expected_text(test_case)

            result = translator.translate(source_text, source_lang, target_lang)

            # Combine word alignments from all sentences (translator may split into multiple)
            all_parts = [sentence.get_word_by_word() for sentence in result.sentences]
            generated_word_by_word = " ".join(all_parts)

            if conftest.normalize_word_by_word(generated_word_by_word) != conftest.normalize_word_by_word(
                expected_word_by_word
            ):
                failed_cases.append(
                    {
                        "case_index": idx,
                        "source_text": source_text,
                        "expected": expected_word_by_word,
                        "generated": generated_word_by_word,
                    }
                )

        if failed_cases:
            failure_msg = "\n\nFailed word-by-word translations:\n"
            for case in failed_cases:
                failure_msg += f"\nCase {case['case_index']}: {case['source_text']}\n"
                failure_msg += f"  Expected:  {case['expected']}\n"
                failure_msg += f"  Generated: {case['generated']}\n"

            pytest.fail(failure_msg)

    def test_sample_translation_structure(self, test_data: dict[str, object], anthropic_config: ProviderConfig) -> None:
        """Test a sample translation to verify structure is correct."""
        translator = PydanticAITranslator(anthropic_config)

        test_cases = conftest.get_test_cases(test_data)
        source_text = conftest.get_source_text(test_cases[0])
        source_lang = conftest.get_source_language(test_data)
        target_lang = conftest.get_target_language(test_data)

        result = translator.translate(source_text, source_lang, target_lang)

        assert len(result.sentences) > 0

        for sentence in result.sentences:
            assert sentence.source_text.strip() != ""
            assert sentence.natural_translation.strip() != ""
            assert len(sentence.word_alignments) > 0

            for alignment in sentence.word_alignments:
                assert alignment.source_word.strip() != ""
                # Note: target_word may be empty in some cases (e.g., articles)
                assert alignment.position >= 0

    @pytest.mark.parametrize("test_index", [0, 1, 2, 3, 4])
    def test_first_five_translations_sample(
        self, test_data: dict[str, object], anthropic_config: ProviderConfig, test_index: int
    ) -> None:
        """Test first 5 translations and show comparison for review (non-failing)."""
        translator = PydanticAITranslator(anthropic_config)
        source_lang = conftest.get_source_language(test_data)
        target_lang = conftest.get_target_language(test_data)

        test_cases = conftest.get_test_cases(test_data)
        test_case = test_cases[test_index]
        source_text = conftest.get_source_text(test_case)
        expected_word_by_word = conftest.get_expected_text(test_case)

        result = translator.translate(source_text, source_lang, target_lang)

        all_parts = [sentence.get_word_by_word() for sentence in result.sentences]
        generated_word_by_word = " ".join(all_parts)

        print(f"\nCase {test_index}: {source_text}")
        print(f"Expected:  {expected_word_by_word}")
        print(f"Generated: {generated_word_by_word}")

        generated_normalized = conftest.normalize_word_by_word(generated_word_by_word)
        expected_normalized = conftest.normalize_word_by_word(expected_word_by_word)
        print(f"Match: {generated_normalized == expected_normalized}")
