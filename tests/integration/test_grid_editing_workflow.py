"""Integration tests: edit word alignments via GridState and persist them through TranslationService.

GridState is the model behind the edit mode's drag&drop grid (InterleavedGridEditable).
"""

import tempfile
from pathlib import Path

import pytest

from birkenbihl.gui.models.grid_state import GridState, build_grid_state
from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.requests import AlignmentUpdateRequest
from birkenbihl.models.translation import AlignmentStatus, Sentence, Translation
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


@pytest.fixture
def translation_service():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield TranslationService(None, JsonStorageProvider(Path(temp_dir) / "translations.json"))


def _save_sentence(service: TranslationService, sentence: Sentence) -> Translation:
    translation = Translation(
        title="Grid editing",
        source_language=get_language_by("es"),
        target_language=get_language_by("de"),
        sentences=[sentence],
    )
    return service.save_translation(translation)


def _move_word(grid: GridState, word: str, to_column: int | None) -> None:
    """Move the first occurrence of a word like a drag&drop does; None drops it into the pool."""
    grid.move(grid.sentence.target_tokens.index(word), to_column)


def _columns(grid: GridState) -> list[tuple[str, list[str]]]:
    return [(c.source_word, [grid.target_word(i) for i in c.target_indices]) for c in grid.columns]


def _wrong_ai_sentence() -> Sentence:
    """'Yo te extrañaré' with 'dich' and 'vermissen' swapped, as an AI might propose."""
    return align_word_pairs(
        "Yo te extrañaré", "Ich werde dich vermissen", [("Yo", "Ich"), ("te", "vermissen"), ("extrañaré", "dich-werde")]
    )


class TestGridEditingWorkflow:
    def test_user_corrects_ai_alignment_and_it_persists(self, translation_service):
        saved = _save_sentence(translation_service, _wrong_ai_sentence())
        sentence = saved.sentences[0]
        grid = build_grid_state(sentence)

        _move_word(grid, "dich", to_column=1)
        _move_word(grid, "vermissen", to_column=2)
        assert grid.validate() == (True, None)

        translation_service.update_sentence_alignment(
            AlignmentUpdateRequest(saved.uuid, sentence.uuid, grid.to_word_alignments())
        )

        reloaded = translation_service.get_translation(saved.uuid)
        assert reloaded is not None
        assert _columns(build_grid_state(reloaded.sentences[0])) == [
            ("Yo", ["Ich"]),
            ("te", ["dich"]),
            ("extrañaré", ["werde", "vermissen"]),
        ]
        assert [a.status for a in reloaded.sentences[0].word_alignments] == [
            AlignmentStatus.SUGGESTED,
            AlignmentStatus.CONFIRMED,
            AlignmentStatus.CONFIRMED,
        ]

    def test_empty_column_is_reported_by_grid(self, translation_service):
        grid = build_grid_state(_wrong_ai_sentence())

        _move_word(grid, "vermissen", to_column=2)

        assert grid.columns[1].is_empty()
        assert grid.validate()[0] is False

    def test_service_rejects_alignment_with_word_left_in_pool(self, translation_service):
        saved = _save_sentence(translation_service, _wrong_ai_sentence())
        sentence = saved.sentences[0]
        grid = build_grid_state(sentence)

        _move_word(grid, "werde", to_column=None)

        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(
                AlignmentUpdateRequest(saved.uuid, sentence.uuid, grid.to_word_alignments())
            )

    def test_repeated_source_word_keeps_its_own_target(self):
        sentence = align_word_pairs(
            "the dog and the man",
            "der Hund und die Frau",
            [("the", "der"), ("dog", "Hund"), ("and", "und"), ("the", "die"), ("man", "Frau")],
        )

        grid = build_grid_state(sentence)

        assert _columns(grid)[0] == ("the", ["der"])
        assert _columns(grid)[3] == ("the", ["die"])
