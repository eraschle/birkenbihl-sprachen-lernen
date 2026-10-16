"""Integration tests: edit word alignments via GridState and persist them through TranslationService.

GridState is the model behind the edit mode's drag&drop grid (InterleavedGridEditable).
"""

import tempfile
from pathlib import Path

import pytest

from birkenbihl.gui.models.grid_state import GridState, build_grid_state
from birkenbihl.models.requests import AlignmentUpdateRequest
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
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
    """Move a word like a drag&drop does; to_column=None drops it into the unassigned pool."""
    for column in grid.columns:
        if word in column.assigned_words:
            column.assigned_words.remove(word)
    if word in grid.unassigned_words:
        grid.unassigned_words.remove(word)

    if to_column is None:
        grid.unassigned_words.append(word)
    else:
        grid.columns[to_column].assigned_words.append(word)


def _columns(grid: GridState) -> list[tuple[str, list[str]]]:
    return [(column.source_word, column.assigned_words) for column in grid.columns]


def _wrong_ai_sentence() -> Sentence:
    """'Yo te extrañaré' with 'dich' and 'vermissen' swapped, as an AI might propose."""
    return Sentence(
        source_text="Yo te extrañaré",
        natural_translation="Ich werde dich vermissen",
        word_alignments=[
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="vermissen", position=1),
            WordAlignment(source_word="extrañaré", target_word="dich-werde", position=2),
        ],
    )


class TestGridEditingWorkflow:
    def test_user_corrects_ai_alignment_and_it_persists(self, translation_service):
        saved = _save_sentence(translation_service, _wrong_ai_sentence())
        sentence = saved.sentences[0]
        grid = build_grid_state(sentence)

        _move_word(grid, "dich", to_column=1)
        _move_word(grid, "vermissen", to_column=2)
        assert grid.is_valid()

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

    def test_empty_column_is_reported_by_grid(self, translation_service):
        grid = build_grid_state(_wrong_ai_sentence())

        _move_word(grid, "vermissen", to_column=2)

        assert not grid.is_valid()
        assert grid.get_error_columns() == ["te"]

    def test_service_rejects_alignment_with_word_left_in_pool(self, translation_service):
        saved = _save_sentence(translation_service, _wrong_ai_sentence())
        sentence = saved.sentences[0]
        grid = build_grid_state(sentence)

        _move_word(grid, "werde", to_column=None)

        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(
                AlignmentUpdateRequest(saved.uuid, sentence.uuid, grid.to_word_alignments())
            )

    @pytest.mark.xfail(
        strict=True,
        reason="GridState matches columns by source word text; repeated source words share targets (fix: positions)",
    )
    def test_repeated_source_word_keeps_its_own_target(self):
        sentence = Sentence(
            source_text="the dog and the man",
            natural_translation="der Hund und die Frau",
            word_alignments=[
                WordAlignment(source_word="the", target_word="der", position=0),
                WordAlignment(source_word="dog", target_word="Hund", position=1),
                WordAlignment(source_word="and", target_word="und", position=2),
                WordAlignment(source_word="the", target_word="die", position=3),
                WordAlignment(source_word="man", target_word="Frau", position=4),
            ],
        )

        grid = build_grid_state(sentence)

        assert grid.columns[0].assigned_words == ["der"]
        assert grid.columns[3].assigned_words == ["die"]
