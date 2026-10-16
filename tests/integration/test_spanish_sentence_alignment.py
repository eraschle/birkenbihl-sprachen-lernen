"""Integration test for a real Spanish course sentence with reported alignment issues."""

import pytest

from birkenbihl.models import validation
from birkenbihl.models.alignment import WordPair, align_word_pairs
from birkenbihl.models.translation import AlignmentStatus, Translation
from birkenbihl.services import language_service as lang_service

SOURCE_TEXT = "Mas comprendo que llegó tu tiempo, que Dios te ha llamado para estar a Su lado."
NATURAL_TRANSLATION = (
    "Aber ich verstehe, dass deine Zeit gekommen ist, dass Gott dich gerufen hat, um an Seiner Seite zu sein."
)


@pytest.fixture
def word_pairs() -> list[WordPair]:
    return [
        ("Mas", "Aber"),
        ("comprendo", "verstehe-ich"),
        ("que", "dass"),
        ("llegó", "gekommen-ist"),
        ("tu", "deine"),
        ("tiempo", "Zeit"),
        ("que", "dass"),
        ("Dios", "Gott"),
        ("te", "dich"),
        ("ha", "hat"),
        ("llamado", "gerufen"),
        ("para", "um"),
        ("estar", "zu-sein"),
        ("a", "an"),
        ("Su", "Seiner"),
        ("lado", "Seite"),
    ]


class TestSpanishSentenceAlignment:
    def test_full_sentence_alignment_is_valid(self, word_pairs: list[WordPair]) -> None:
        sentence = align_word_pairs(SOURCE_TEXT, NATURAL_TRANSLATION, word_pairs)

        assert validation.validate_alignment_complete(sentence) == (True, None)
        assert len(sentence.word_alignments) == 16
        assert not sentence.needs_review()

    def test_both_que_get_their_own_dass(self, word_pairs: list[WordPair]) -> None:
        sentence = align_word_pairs(SOURCE_TEXT, NATURAL_TRANSLATION, word_pairs)

        que_alignments = [a for a in sentence.word_alignments if sentence.source_word(a) == "que"]
        assert [a.target_indices for a in que_alignments] == [[3], [8]]

    def test_word_by_word_in_source_order(self, word_pairs: list[WordPair]) -> None:
        sentence = align_word_pairs(SOURCE_TEXT, NATURAL_TRANSLATION, word_pairs)

        assert sentence.get_word_by_word() == (
            "Aber verstehe-ich dass gekommen-ist deine Zeit dass Gott dich hat gerufen um zu-sein an Seiner Seite"
        )

    def test_reported_broken_alignment_is_flagged_and_invalid(self, word_pairs: list[WordPair]) -> None:
        """The originally reported AI output: 'gerufen-hat' on 'ha' and whitespace on 'llamado'."""
        word_pairs[9] = ("ha", "gerufen-hat")
        word_pairs[10] = ("llamado", " ")

        sentence = align_word_pairs(SOURCE_TEXT, NATURAL_TRANSLATION, word_pairs)

        llamado = next(a for a in sentence.word_alignments if sentence.source_word(a) == "llamado")
        assert llamado.status == AlignmentStatus.FLAGGED
        is_valid, error = validation.validate_alignment_complete(sentence)
        assert not is_valid
        assert error is not None
        assert "Quellwörter ohne Zielwort: llamado" in error

    def test_tokens_drop_punctuation(self) -> None:
        sentence = align_word_pairs(SOURCE_TEXT, NATURAL_TRANSLATION, [])

        assert "um" in sentence.target_tokens
        assert "hat" in sentence.target_tokens
        assert "lado" in sentence.source_tokens
        assert all(token.isalpha() for token in sentence.source_tokens + sentence.target_tokens)

    def test_create_full_translation_object(self, word_pairs: list[WordPair]) -> None:
        sentence = align_word_pairs(SOURCE_TEXT, NATURAL_TRANSLATION, word_pairs)

        translation = Translation(
            title="Spanish Test Sentence",
            source_language=lang_service.get_language_by("es"),
            target_language=lang_service.get_language_by("de"),
            sentences=[sentence],
        )

        assert translation.sentences[0].source_text == SOURCE_TEXT
        assert validation.validate_alignment_complete(translation.sentences[0]) == (True, None)
