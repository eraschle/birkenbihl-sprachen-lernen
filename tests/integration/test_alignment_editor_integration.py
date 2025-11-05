"""End-to-end integration tests for Alignment Editor workflow."""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from birkenbihl.gui.viewmodels.alignment_editor_vm import AlignmentEditorViewModel
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services.language_service import SUPPORTED_LANGUAGES
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


@pytest.fixture
def temp_storage():
    """Create temporary JSON storage for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_translations.json"
        yield JsonStorageProvider(str(storage_path))


@pytest.fixture
def translation_service(temp_storage):
    """Create TranslationService with temporary storage."""
    return TranslationService(translator=None, storage=temp_storage)


@pytest.fixture
def sample_translation():
    """Create sample translation with sentence."""
    return Translation(
        uuid=uuid4(),
        title="Test Translation",
        source_language=SUPPORTED_LANGUAGES["en"],
        target_language=SUPPORTED_LANGUAGES["de"],
        sentences=[
            Sentence(
                uuid=uuid4(),
                source_text="The cat sat",
                natural_translation="Die Katze saß",
                word_alignments=[
                    WordAlignment(source_word="The", target_word="Die", position=0),
                    WordAlignment(source_word="cat", target_word="Katze", position=1),
                    WordAlignment(source_word="sat", target_word="saß", position=2),
                ],
            )
        ],
    )


@pytest.mark.integration
class TestAlignmentEditorIntegration:
    """Test complete alignment editor workflow with persistence."""

    def test_load_edit_save_workflow(self, translation_service, sample_translation):
        """Test complete workflow: save → load → edit → save → verify."""
        # Step 1: Save initial translation
        saved = translation_service.save_translation(sample_translation)
        assert saved.uuid == sample_translation.uuid
        sentence = saved.sentences[0]

        # Step 2: Load into ViewModel
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # Verify initial state
        state = viewmodel.get_state()
        assert state.source_words == ["The", "cat", "sat"]
        assert state.assigned_words == {0: ["Die"], 1: ["Katze"], 2: ["saß"]}
        assert state.unassigned_words == []
        assert state.is_valid is True

        # Step 3: Edit alignment - move "saß" to column 1
        viewmodel.unassign_word("saß", 2)
        viewmodel.assign_word("saß", 1)

        # Verify edited state
        state = viewmodel.get_state()
        assert state.assigned_words == {0: ["Die"], 1: ["Katze", "saß"]}
        assert 2 not in state.assigned_words
        assert state.is_valid is False  # Column 2 is now empty

        # Step 4: Fix by assigning another word
        viewmodel.assign_word("unten", 2)  # Add new word to column 2
        state = viewmodel.get_state()
        assert state.is_valid is True

        # Step 5: Convert to alignments and save through service
        new_alignments = viewmodel.to_word_alignments()
        assert len(new_alignments) == 3
        assert new_alignments[1].target_word == "Katze-saß"  # Hyphenated
        assert new_alignments[2].target_word == "unten"

        translation_service.update_sentence_alignment(
            translation_id=saved.uuid, sentence_uuid=sentence.uuid, alignments=new_alignments
        )

        # Step 6: Verify persistence - reload from storage
        reloaded = translation_service.get_translation(saved.uuid)
        assert reloaded is not None
        reloaded_sentence = reloaded.sentences[0]

        assert len(reloaded_sentence.word_alignments) == 3
        assert reloaded_sentence.word_alignments[0].target_word == "Die"
        assert reloaded_sentence.word_alignments[1].target_word == "Katze-saß"
        assert reloaded_sentence.word_alignments[2].target_word == "unten"

    def test_edit_with_unassigned_words(self, translation_service):
        """Test editing sentence where not all words are initially assigned."""
        # Create sentence with incomplete alignment
        translation = Translation(
            uuid=uuid4(),
            title="Incomplete Alignment",
            source_language=SUPPORTED_LANGUAGES["en"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="The cat",
                    natural_translation="Die schwarze Katze",
                    word_alignments=[
                        WordAlignment(source_word="The", target_word="Die", position=0),
                        WordAlignment(source_word="cat", target_word="Katze", position=1),
                    ],
                )
            ],
        )

        saved = translation_service.save_translation(translation)
        sentence = saved.sentences[0]

        # Load into ViewModel
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # Verify "schwarze" is unassigned
        state = viewmodel.get_state()
        assert "schwarze" in state.unassigned_words
        assert state.is_valid is False

        # Assign "schwarze" to column 1
        viewmodel.assign_word("schwarze", 1)

        # Verify state is now valid
        state = viewmodel.get_state()
        assert state.assigned_words[1] == ["Katze", "schwarze"]
        assert state.unassigned_words == []
        assert state.is_valid is True

        # Save and verify persistence
        alignments = viewmodel.to_word_alignments()
        translation_service.update_sentence_alignment(
            translation_id=saved.uuid, sentence_uuid=sentence.uuid, alignments=alignments
        )

        reloaded = translation_service.get_translation(saved.uuid)
        assert reloaded is not None
        reloaded_sentence = reloaded.sentences[0]
        alignment_1 = next(a for a in reloaded_sentence.word_alignments if a.position == 1)
        assert alignment_1.target_word == "Katze-schwarze"

    def test_reset_restores_from_storage(self, translation_service, sample_translation):
        """Test reset functionality reloads original alignment."""
        saved = translation_service.save_translation(sample_translation)
        sentence = saved.sentences[0]

        # Load and edit
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)
        viewmodel.unassign_word("Katze", 1)

        # Verify edited
        state = viewmodel.get_state()
        assert "Katze" in state.unassigned_words

        # Reset
        viewmodel.reset()

        # Verify restored
        state = viewmodel.get_state()
        assert state.assigned_words == {0: ["Die"], 1: ["Katze"], 2: ["saß"]}
        assert state.unassigned_words == []
        assert state.is_valid is True
        assert state.is_dirty is False

    def test_validation_prevents_invalid_save(self, translation_service, sample_translation):
        """Test that invalid alignment cannot be saved through service."""
        saved = translation_service.save_translation(sample_translation)
        sentence = saved.sentences[0]

        # Load and create invalid state
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)
        viewmodel.unassign_word("Die", 0)  # Remove Die, leaving column 0 empty

        # Verify invalid state
        is_valid, errors = viewmodel.validate()
        assert is_valid is False
        assert any("The" in err for err in errors)

        # Try to save invalid alignment
        alignments = viewmodel.to_word_alignments()

        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(
                translation_id=saved.uuid, sentence_uuid=sentence.uuid, alignments=alignments
            )

    def test_complex_word_order_changes(self, translation_service):
        """Test handling complex word order changes between languages."""
        translation = Translation(
            uuid=uuid4(),
            title="Word Order Test",
            source_language=SUPPORTED_LANGUAGES["en"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="I will miss you",
                    natural_translation="Ich werde dich vermissen",
                    word_alignments=[
                        WordAlignment(source_word="I", target_word="Ich", position=0),
                        WordAlignment(source_word="will", target_word="werde", position=1),
                        WordAlignment(source_word="miss", target_word="vermissen", position=2),
                        WordAlignment(source_word="you", target_word="dich", position=3),
                    ],
                )
            ],
        )

        saved = translation_service.save_translation(translation)
        sentence = saved.sentences[0]

        # Load and reorganize
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # Move "dich" from column 3 to column 2
        viewmodel.unassign_word("dich", 3)
        viewmodel.assign_word("dich", 2)

        state = viewmodel.get_state()
        assert state.assigned_words[2] == ["vermissen", "dich"]
        assert 3 not in state.assigned_words

        # Save
        alignments = viewmodel.to_word_alignments()
        translation_service.update_sentence_alignment(
            translation_id=saved.uuid, sentence_uuid=sentence.uuid, alignments=alignments
        )

        # Verify
        reloaded = translation_service.get_translation(saved.uuid)
        assert reloaded is not None
        reloaded_sentence = reloaded.sentences[0]

        # Should now have only 3 alignments (column 3 removed)
        assert len(reloaded_sentence.word_alignments) == 3
        miss_alignment = next(a for a in reloaded_sentence.word_alignments if a.source_word == "miss")
        assert miss_alignment.target_word == "vermissen-dich"

    def test_hyphenated_word_splitting(self, translation_service):
        """Test loading sentence with hyphenated target words."""
        translation = Translation(
            uuid=uuid4(),
            title="Hyphenated Test",
            source_language=SUPPORTED_LANGUAGES["es"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Yo te extrañaré",
                    natural_translation="Ich werde dich vermissen",
                    word_alignments=[
                        WordAlignment(source_word="Yo", target_word="Ich", position=0),
                        WordAlignment(source_word="te", target_word="dich", position=1),
                        WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
                    ],
                )
            ],
        )

        saved = translation_service.save_translation(translation)
        sentence = saved.sentences[0]

        # Load into ViewModel
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # Verify hyphenated word is split
        state = viewmodel.get_state()
        assert state.assigned_words[2] == ["werde", "vermissen"]

        # Verify can be saved back
        alignments = viewmodel.to_word_alignments()
        translation_service.update_sentence_alignment(
            translation_id=saved.uuid, sentence_uuid=sentence.uuid, alignments=alignments
        )

        reloaded = translation_service.get_translation(saved.uuid)
        assert reloaded is not None
        reloaded_sentence = reloaded.sentences[0]
        alignment_2 = next(a for a in reloaded_sentence.word_alignments if a.position == 2)
        assert alignment_2.target_word == "werde-vermissen"


@pytest.mark.integration
class TestMultipleSentenceEditing:
    """Test editing multiple sentences in same translation."""

    def test_edit_different_sentences_sequentially(self, translation_service):
        """Test editing different sentences in same translation."""
        translation = Translation(
            uuid=uuid4(),
            title="Multi-Sentence",
            source_language=SUPPORTED_LANGUAGES["en"],
            target_language=SUPPORTED_LANGUAGES["de"],
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="The cat sat",
                    natural_translation="Die Katze saß",
                    word_alignments=[
                        WordAlignment(source_word="The", target_word="Die", position=0),
                        WordAlignment(source_word="cat", target_word="Katze", position=1),
                        WordAlignment(source_word="sat", target_word="saß", position=2),
                    ],
                ),
                Sentence(
                    uuid=uuid4(),
                    source_text="The dog ran",
                    natural_translation="Der Hund rannte",
                    word_alignments=[
                        WordAlignment(source_word="The", target_word="Der", position=0),
                        WordAlignment(source_word="dog", target_word="Hund", position=1),
                        WordAlignment(source_word="ran", target_word="rannte", position=2),
                    ],
                ),
            ],
        )

        saved = translation_service.save_translation(translation)
        sentence1 = saved.sentences[0]
        sentence2 = saved.sentences[1]

        # Edit first sentence
        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence1)
        viewmodel.unassign_word("saß", 2)
        viewmodel.assign_word("saß", 1)
        alignments1 = viewmodel.to_word_alignments()

        # Can't save invalid alignment (column 2 empty)
        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(
                translation_id=saved.uuid, sentence_uuid=sentence1.uuid, alignments=alignments1
            )

        # Edit second sentence
        viewmodel.load_sentence(sentence2)
        viewmodel.unassign_word("rannte", 2)
        viewmodel.assign_word("rannte", 1)
        viewmodel.assign_word("schnell", 2)  # Add new word
        alignments2 = viewmodel.to_word_alignments()

        translation_service.update_sentence_alignment(
            translation_id=saved.uuid, sentence_uuid=sentence2.uuid, alignments=alignments2
        )

        # Verify only sentence 2 changed
        reloaded = translation_service.get_translation(saved.uuid)
        assert reloaded is not None

        # Sentence 1 unchanged
        assert reloaded.sentences[0].word_alignments == sentence1.word_alignments

        # Sentence 2 updated
        assert reloaded.sentences[1].word_alignments != sentence2.word_alignments
        assert len(reloaded.sentences[1].word_alignments) == 3
