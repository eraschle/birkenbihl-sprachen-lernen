"""Unit tests for BaseTranslator with a scripted model (real pydantic-ai agents, no API calls)."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from birkenbihl.models.translation import AlignmentStatus, Translation
from birkenbihl.providers.base_translator import BaseTranslator
from birkenbihl.providers.llm_aligner import ALIGNMENT_RETRIES
from birkenbihl.providers.models import (
    AlignmentResponse,
    NaturalSentenceResponse,
    NaturalTranslationResponse,
    WordAlignmentResponse,
)
from birkenbihl.services.language_service import get_language_by


class ScriptedModel:
    """Answers each model request with the next scripted output and records retry feedback."""

    def __init__(self, *outputs: BaseModel):
        self._outputs = list(outputs)
        self.retry_feedback: list[str] = []

    def model(self) -> FunctionModel:
        return FunctionModel(self._answer)

    def _answer(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        for part in messages[-1].parts:
            if isinstance(part, RetryPromptPart):
                self.retry_feedback.append(part.model_response())
        output = self._outputs.pop(0)
        return ModelResponse(parts=[ToolCallPart(tool_name=info.output_tools[0].name, args=output.model_dump())])


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


def _translate(text: str, source: str, *outputs: BaseModel) -> tuple[Translation, ScriptedModel]:
    script = ScriptedModel(*outputs)
    translation = BaseTranslator(script.model()).translate(text, get_language_by(source), get_language_by("de"))
    return translation, script


def _columns(translation: Translation, sentence_index: int = 0) -> list[tuple[str, str]]:
    sentence = translation.sentences[sentence_index]
    return [(sentence.source_word(a), sentence.target_text(a)) for a in sentence.sorted_alignments()]


YO_TE = _natural(("Yo te extrañaré", "Ich werde dich vermissen"))
YO_TE_CORRECT = _alignment(("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde"))
YO_TE_WRONG = _alignment(("Yo", "Ich"), ("te", "dir"), ("extrañaré", "vermissen-werde"))


@pytest.mark.unit
class TestTranslate:
    def test_translate_single_sentence(self) -> None:
        result, _ = _translate(
            "Hello world",
            "en",
            _natural(("Hello world", "Hallo Welt")),
            _alignment(("Hello", "Hallo"), ("world", "Welt")),
        )

        assert result.source_language.code == "en"
        assert result.target_language.code == "de"
        assert isinstance(result.uuid, UUID)
        assert isinstance(result.created_at, datetime)
        assert _columns(result) == [("Hello", "Hallo"), ("world", "Welt")]

    def test_translate_multiple_sentences(self) -> None:
        result, _ = _translate(
            "Hello world. How are you",
            "en",
            _natural(("Hello world", "Hallo Welt"), ("How are you", "Wie geht es dir")),
            _alignment(("Hello", "Hallo"), ("world", "Welt")),
            _alignment(("How", "Wie"), ("are", "geht-es"), ("you", "dir")),
        )

        assert len(result.sentences) == 2
        assert _columns(result, 1) == [("How", "Wie"), ("are", "geht-es"), ("you", "dir")]

    def test_birkenbihl_decoding_with_compound_target(self) -> None:
        result, script = _translate("Yo te extrañaré", "es", YO_TE, YO_TE_CORRECT)

        assert result.sentences[0].get_word_by_word() == "Ich dich vermissen-werde"
        assert script.retry_feedback == []

    def test_alignments_follow_source_order_even_if_ai_reorders(self) -> None:
        reordered = AlignmentResponse(
            word_alignments=[
                WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
                WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
            ]
        )

        result, _ = _translate("Hello world", "en", _natural(("Hello world", "Hallo Welt")), reordered)

        assert [a.source_index for a in result.sentences[0].word_alignments] == [0, 1]


@pytest.mark.unit
class TestSelfCorrection:
    def test_model_fixes_its_alignment_after_feedback(self) -> None:
        result, script = _translate("Yo te extrañaré", "es", YO_TE, YO_TE_WRONG, YO_TE_CORRECT)

        sentence = result.sentences[0]
        assert sentence.get_word_by_word() == "Ich dich vermissen-werde"
        assert not sentence.needs_review()
        assert len(script.retry_feedback) == 1
        assert "Quellwörter ohne Zielwort: te" in script.retry_feedback[0]
        assert "Fehlende Wörter: dich" in script.retry_feedback[0]

    def test_unknown_target_word_is_reported_to_the_model(self) -> None:
        extra_word = _alignment(("Yo", "Ich"), ("te", "dich"), ("extrañaré", "vermissen-werde-wird"))

        _, script = _translate("Yo te extrañaré", "es", YO_TE, extra_word, YO_TE_CORRECT)

        assert (
            "The targets for extrañaré contain words that are not in the natural translation"
            in (script.retry_feedback[0])
        )

    def test_still_wrong_after_retries_is_flagged_for_review(self) -> None:
        wrong_every_time = [YO_TE_WRONG] * (ALIGNMENT_RETRIES + 1)

        result, script = _translate("Yo te extrañaré", "es", YO_TE, *wrong_every_time)

        sentence = result.sentences[0]
        assert len(script.retry_feedback) == ALIGNMENT_RETRIES
        assert sentence.word_alignments[1].status == AlignmentStatus.FLAGGED
        assert sentence.needs_review()

    def test_model_sees_cleaned_tokens(self) -> None:
        script = ScriptedModel(_alignment(("Hola", "Hallo"), ("amigo", "Freund")))
        prompts: list[str] = []
        model = script.model()
        answer = model.function

        def capture(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
            prompts.append(str(messages[0].parts[-1].content))  # type: ignore[union-attr]
            return answer(messages, info)  # type: ignore[misc]

        BaseTranslator(FunctionModel(capture)).regenerate_alignment(
            "¡Hola, amigo!", "Hallo, Freund!", get_language_by("es"), get_language_by("de")
        )

        assert '\'"Hola", "amigo"\'' in prompts[0]
        assert '\'"Hallo", "Freund"\'' in prompts[0]


@pytest.mark.unit
class TestRegenerateAlignment:
    def test_returns_positions_for_given_texts(self) -> None:
        script = ScriptedModel(_alignment(("Hola", "Hallo"), ("mundo", "Welt")))

        alignments = BaseTranslator(script.model()).regenerate_alignment(
            "Hola mundo", "Hallo Welt", get_language_by("es"), get_language_by("de")
        )

        assert [(a.source_index, a.target_indices) for a in alignments] == [(0, [0]), (1, [1])]

    def test_is_self_correcting_too(self) -> None:
        script = ScriptedModel(YO_TE_WRONG, YO_TE_CORRECT)

        alignments = BaseTranslator(script.model()).regenerate_alignment(
            "Yo te extrañaré", "Ich werde dich vermissen", get_language_by("es"), get_language_by("de")
        )

        assert alignments[1].target_indices == [2]
        assert len(script.retry_feedback) == 1
