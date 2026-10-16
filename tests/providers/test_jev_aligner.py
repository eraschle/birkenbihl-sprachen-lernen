"""Unit tests for JevAligner with a scripted decision model (real pydantic-ai agent, no API calls)."""

import re

import pytest
from pydantic_ai.models.decision import (
    DecisionModel,
    DecisionModelSettings,
    DecisionRequest,
    DecisionResponse,
    NoulAnswer,
    NoulQuestion,
)

from birkenbihl.models.languages import Language
from birkenbihl.models.translation import AlignmentStatus, Sentence
from birkenbihl.providers.jev_aligner import JevAligner
from birkenbihl.services.language_service import get_language_by

_QUESTION = re.compile(r"source_(\d+)_target_(\d+)")


class ScriptedJev(DecisionModel[None]):
    """Answers every word pair question with a probability from a [source][target] table."""

    def __init__(self, probabilities: list[list[float]]):
        super().__init__()
        self._probabilities = probabilities
        self.requests: list[DecisionRequest] = []

    @property
    def model_name(self) -> str:
        return "scripted-jev"

    @property
    def system(self) -> str:
        return "test"

    async def decide(self, request: DecisionRequest, model_settings: DecisionModelSettings) -> DecisionResponse:
        self.requests.append(request)
        return DecisionResponse(
            answers={name: NoulAnswer(noul=self._probability(name)) for name in request.questions},
            model_name=self.model_name,
        )

    def _probability(self, question_name: str) -> float:
        match = _QUESTION.fullmatch(question_name)
        assert match, f"unexpected question {question_name!r}"
        return self._probabilities[int(match[1]) - 1][int(match[2]) - 1]


def _align(model: ScriptedJev, source_text: str, natural_translation: str, source: str = "es") -> Sentence:
    languages: tuple[Language, Language] = (get_language_by(source), get_language_by("de"))
    return JevAligner(model).align(source_text, natural_translation, *languages)


@pytest.mark.unit
class TestJevAligner:
    def test_aligns_from_probabilities(self) -> None:
        jev = ScriptedJev(
            [
                [0.96, 0.05, 0.11, 0.02],
                [0.03, 0.04, 0.95, 0.01],
                [0.02, 0.80, 0.05, 0.90],
            ]
        )

        sentence = _align(jev, "Yo te extrañaré", "Ich werde dich vermissen")

        assert [sentence.target_text(a) for a in sentence.sorted_alignments()] == ["Ich", "dich", "werde-vermissen"]
        assert {a.status for a in sentence.word_alignments} == {AlignmentStatus.SUGGESTED}

    def test_asks_every_word_pair_in_one_request(self) -> None:
        jev = ScriptedJev([[0.9, 0.1], [0.1, 0.9]])

        _align(jev, "Hola mundo", "Hallo Welt")

        assert len(jev.requests) == 1
        assert sorted(jev.requests[0].questions) == [
            "source_1_target_1",
            "source_1_target_2",
            "source_2_target_1",
            "source_2_target_2",
        ]

    def test_question_names_the_words_and_state_holds_the_sentences(self) -> None:
        jev = ScriptedJev([[0.9, 0.1], [0.1, 0.9]])

        _align(jev, "Hola mundo", "Hallo Welt")

        request = jev.requests[0]
        question = request.questions["source_2_target_1"]
        assert isinstance(question, NoulQuestion)
        assert "'Hallo' (word 1)" in str(question.instructions)
        assert "'mundo' (word 2)" in str(question.instructions)
        assert "Hola mundo" in str(request.state)
        assert "Hallo Welt" in str(request.state)

    def test_single_word_translation(self) -> None:
        sentence = _align(ScriptedJev([[0.97]]), "Hola", "Hallo")

        assert sentence.get_word_by_word() == "Hallo"

    def test_uncertain_alignment_is_flagged(self) -> None:
        jev = ScriptedJev([[0.9, 0.3, 0.1], [0.1, 0.35, 0.95]])

        sentence = _align(jev, "Good morning", "Guten lieben Morgen", source="en")

        assert sentence.needs_review()
