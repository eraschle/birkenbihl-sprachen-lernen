"""Unit tests for BaseTranslator with mocked AI responses (two-step process)."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from birkenbihl.models.translation import AlignmentStatus, Translation
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.models import (
    AlignmentResponse,
    NaturalSentenceResponse,
    NaturalTranslationResponse,
    WordAlignmentResponse,
)
from birkenbihl.services.language_service import get_language_by


@pytest.fixture
def translator() -> BaseTranslator:
    return BaseTranslator(MagicMock())


def _agent_returning(output: object) -> MagicMock:
    agent = MagicMock()
    agent.run_sync.return_value = MagicMock(output=output)
    return agent


def _natural(*pairs: tuple[str, str]) -> NaturalTranslationResponse:
    return NaturalTranslationResponse(
        sentences=[NaturalSentenceResponse(source_text=s, natural_translation=n) for s, n in pairs]
    )


def _alignment(*pairs: tuple[str, str]) -> AlignmentResponse:
    return AlignmentResponse(
        word_alignments=[
            WordAlignmentResponse(source_word=s, target_word=t, position=i) for i, (s, t) in enumerate(pairs)
        ]
    )


def _translate(translator: BaseTranslator, text: str, source: str, *responses: object) -> Translation:
    with patch("birkenbihl.providers.base_translator.Agent") as agent_class:
        agent_class.side_effect = [_agent_returning(response) for response in responses]
        return translator.translate(text, get_language_by(source), get_language_by("de"))


def _columns(translation: Translation, sentence_index: int = 0) -> list[tuple[str, str]]:
    sentence = translation.sentences[sentence_index]
    return [(sentence.source_word(a), sentence.target_text(a)) for a in sentence.sorted_alignments()]


@pytest.mark.unit
class TestBaseTranslator:
    def test_translate_single_sentence(self, translator: BaseTranslator) -> None:
        result = _translate(
            translator,
            "Hello world",
            "en",
            _natural(("Hello world", "Hallo Welt")),
            _alignment(("Hello", "Hallo"), ("world", "Welt")),
        )

        assert result.source_language.code == "en"
        assert result.target_language.code == "de"
        assert isinstance(result.uuid, UUID)
        assert isinstance(result.created_at, datetime)
        assert result.sentences[0].natural_translation == "Hallo Welt"
        assert _columns(result) == [("Hello", "Hallo"), ("world", "Welt")]

    def test_translate_multiple_sentences(self, translator: BaseTranslator) -> None:
        result = _translate(
            translator,
            "Hello world. How are you",
            "en",
            _natural(("Hello world", "Hallo Welt"), ("How are you", "Wie geht es dir")),
            _alignment(("Hello", "Hallo"), ("world", "Welt")),
            _alignment(("How", "Wie"), ("are", "geht-es"), ("you", "dir")),
        )

        assert len(result.sentences) == 2
        assert _columns(result, 1) == [("How", "Wie"), ("are", "geht-es"), ("you", "dir")]

    def test_birkenbihl_decoding_with_compound_target(self, translator: BaseTranslator) -> None:
        result = _translate(
            translator,
            "Yo te extrañaré",
            "es",
            _natural(("Yo te extrañaré", "Ich werde dich vermissen")),
            _alignment(("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde")),
        )

        sentence = result.sentences[0]
        assert sentence.get_word_by_word() == "Ich dich vermissen-werde"
        assert not sentence.needs_review()

    def test_alignments_follow_source_order_even_if_ai_reorders(self, translator: BaseTranslator) -> None:
        alignment = AlignmentResponse(
            word_alignments=[
                WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
                WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
            ]
        )

        result = _translate(translator, "Hello world", "en", _natural(("Hello world", "Hallo Welt")), alignment)

        assert [a.source_index for a in result.sentences[0].word_alignments] == [0, 1]

    def test_ai_alignment_error_is_flagged_for_review(self, translator: BaseTranslator) -> None:
        result = _translate(
            translator,
            "Yo te extrañaré",
            "es",
            _natural(("Yo te extrañaré", "Ich werde dich vermissen")),
            _alignment(("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde")),
        )

        sentence = result.sentences[0]
        assert sentence.word_alignments[1].status == AlignmentStatus.FLAGGED
        assert [sentence.target_tokens[i] for i in sentence.unassigned_target_indices()] == ["dich"]
        assert sentence.needs_review()

    def test_regenerate_alignment_returns_positions_for_given_texts(self, translator: BaseTranslator) -> None:
        with patch("birkenbihl.providers.base_translator.Agent") as agent_class:
            agent_class.return_value = _agent_returning(_alignment(("Hola", "Hallo"), ("mundo", "Welt")))
            alignments = translator.regenerate_alignment(
                "Hola mundo", "Hallo Welt", get_language_by("es"), get_language_by("de")
            )

        assert [(a.source_index, a.target_indices) for a in alignments] == [(0, [0]), (1, [1])]

    @pytest.mark.parametrize(("code", "text"), [("en", "Hello world"), ("es", "Hola mundo"), ("de", "Hallo Welt")])
    def test_detect_language(self, translator: BaseTranslator, code: str, text: str) -> None:
        with patch("birkenbihl.providers.base_translator.detector_factory.detect", return_value=code) as detect:
            assert translator.detect_language(text).code == code
            detect.assert_called_once_with(text)
