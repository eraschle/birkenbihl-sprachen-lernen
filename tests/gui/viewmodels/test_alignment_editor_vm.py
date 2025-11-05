"""Integration tests for AlignmentEditorViewModel."""

import pytest

from birkenbihl.gui.viewmodels.alignment_editor_vm import AlignmentEditorViewModel
from birkenbihl.models.translation import Sentence, WordAlignment


class TestAlignmentEditorViewModel:
    """Test AlignmentEditorViewModel state management."""

    @pytest.fixture
    def viewmodel(self):
        """Create fresh ViewModel for each test."""
        return AlignmentEditorViewModel()

    @pytest.fixture
    def sample_sentence(self):
        """Create sample sentence with alignment."""
        return Sentence(
            source_text="The cat sat",
            natural_translation="Die Katze saß",
            word_alignments=[
                WordAlignment(source_word="The", target_word="Die", position=0),
                WordAlignment(source_word="cat", target_word="Katze", position=1),
                WordAlignment(source_word="sat", target_word="saß", position=2),
            ],
        )

    def test_load_sentence_populates_state(self, viewmodel, sample_sentence):
        """Test loading sentence populates state correctly."""
        viewmodel.load_sentence(sample_sentence)

        state = viewmodel.get_state()
        assert state.source_words == ["The", "cat", "sat"]
        assert state.assigned_words == {0: ["Die"], 1: ["Katze"], 2: ["saß"]}
        assert state.unassigned_words == []
        assert state.is_valid is True
        assert state.validation_errors == []
        assert state.is_dirty is False

    def test_load_sentence_with_hyphenated_words(self, viewmodel):
        """Test loading sentence with hyphenated alignments."""
        sentence = Sentence(
            source_text="I miss you",
            natural_translation="Ich werde dich vermissen",
            word_alignments=[
                WordAlignment(source_word="I", target_word="Ich", position=0),
                WordAlignment(source_word="miss", target_word="werde-vermissen", position=1),
                WordAlignment(source_word="you", target_word="dich", position=2),
            ],
        )

        viewmodel.load_sentence(sentence)

        state = viewmodel.get_state()
        # Hyphenated words should be split
        assert state.assigned_words == {0: ["Ich"], 1: ["werde", "vermissen"], 2: ["dich"]}

    def test_assign_word_updates_state(self, viewmodel, sample_sentence):
        """Test assigning word to column updates state."""
        viewmodel.load_sentence(sample_sentence)

        # Remove "Die" from position 0
        viewmodel.unassign_word("Die", 0)
        state = viewmodel.get_state()
        assert "Die" in state.unassigned_words
        assert 0 not in state.assigned_words

        # Assign it back
        viewmodel.assign_word("Die", 0)
        state = viewmodel.get_state()
        assert "Die" not in state.unassigned_words
        assert state.assigned_words[0] == ["Die"]
        assert state.is_dirty is True

    def test_unassign_word_moves_to_pool(self, viewmodel, sample_sentence):
        """Test unassigning word moves it to unassigned pool."""
        viewmodel.load_sentence(sample_sentence)

        viewmodel.unassign_word("Katze", 1)

        state = viewmodel.get_state()
        assert "Katze" in state.unassigned_words
        assert 1 not in state.assigned_words
        assert state.is_dirty is True

    def test_validation_detects_empty_columns(self, viewmodel, sample_sentence):
        """Test validation detects empty columns."""
        viewmodel.load_sentence(sample_sentence)

        # Remove word from column 1
        viewmodel.unassign_word("Katze", 1)

        is_valid, errors = viewmodel.validate()
        assert is_valid is False
        assert any("cat" in err for err in errors)
        assert any("1 words not assigned" in err for err in errors)

    def test_validation_passes_when_all_assigned(self, viewmodel, sample_sentence):
        """Test validation passes when all words assigned."""
        viewmodel.load_sentence(sample_sentence)

        is_valid, errors = viewmodel.validate()
        assert is_valid is True
        assert errors == []

    def test_to_word_alignments_creates_domain_models(self, viewmodel, sample_sentence):
        """Test converting state to WordAlignment list."""
        viewmodel.load_sentence(sample_sentence)

        alignments = viewmodel.to_word_alignments()

        assert len(alignments) == 3
        assert alignments[0].source_word == "The"
        assert alignments[0].target_word == "Die"
        assert alignments[0].position == 0

    def test_to_word_alignments_joins_multiple_words(self, viewmodel, sample_sentence):
        """Test multiple words in column are joined with hyphens."""
        viewmodel.load_sentence(sample_sentence)

        # Add another word to column 1
        viewmodel.assign_word("schwarze", 1)

        alignments = viewmodel.to_word_alignments()

        alignment_1 = next(a for a in alignments if a.position == 1)
        assert alignment_1.target_word == "Katze-schwarze"

    def test_reset_restores_original_alignment(self, viewmodel, sample_sentence):
        """Test reset restores original state."""
        viewmodel.load_sentence(sample_sentence)

        # Make changes
        viewmodel.unassign_word("Katze", 1)
        assert viewmodel.get_state().is_dirty is True

        # Reset
        viewmodel.reset()

        state = viewmodel.get_state()
        assert state.assigned_words == {0: ["Die"], 1: ["Katze"], 2: ["saß"]}
        assert state.unassigned_words == []
        assert state.is_dirty is False

    def test_load_sentence_with_unassigned_words(self, viewmodel):
        """Test loading sentence where not all target words are in alignment."""
        sentence = Sentence(
            source_text="The cat",
            natural_translation="Die schwarze Katze",
            word_alignments=[
                WordAlignment(source_word="The", target_word="Die", position=0),
                WordAlignment(source_word="cat", target_word="Katze", position=1),
            ],
        )

        viewmodel.load_sentence(sentence)

        state = viewmodel.get_state()
        # "schwarze" is not aligned, should be in unassigned
        assert "schwarze" in state.unassigned_words

    def test_assign_multiple_words_to_same_column(self, viewmodel, sample_sentence):
        """Test assigning multiple words to same column."""
        viewmodel.load_sentence(sample_sentence)

        # Unassign and then assign to different column
        viewmodel.unassign_word("saß", 2)
        viewmodel.assign_word("saß", 1)  # Assign to column 1 instead

        state = viewmodel.get_state()
        assert state.assigned_words[1] == ["Katze", "saß"]
        assert 2 not in state.assigned_words

    def test_validation_changed_signal_emitted(self, viewmodel, sample_sentence):
        """Test validation_changed signal is emitted."""
        received_signals = []

        def on_validation_changed(is_valid, errors):
            received_signals.append((is_valid, errors))

        viewmodel.validation_changed.connect(on_validation_changed)
        viewmodel.load_sentence(sample_sentence)

        # Should have been called on load
        assert len(received_signals) >= 1
        is_valid, errors = received_signals[-1]
        assert is_valid is True
        assert errors == []

    def test_state_changed_signal_emitted(self, viewmodel, sample_sentence):
        """Test state_changed signal is emitted on changes."""
        received_states = []

        def on_state_changed(state):
            received_states.append(state)

        viewmodel.state_changed.connect(on_state_changed)
        viewmodel.load_sentence(sample_sentence)

        # Should have been called on load
        assert len(received_states) >= 1

        # Make a change
        viewmodel.assign_word("test", 0)

        # Should be called again
        assert len(received_states) >= 2


@pytest.mark.integration
class TestAlignmentEditorWorkflow:
    """Test complete alignment editing workflow."""

    def test_complete_manual_alignment_workflow(self):
        """Test complete workflow: load -> edit -> validate -> save."""
        # Create sentence with no alignments
        sentence = Sentence(
            source_text="The cat sat",
            natural_translation="Die Katze saß",
            word_alignments=[],
        )

        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # Initial state: all words unassigned
        state = viewmodel.get_state()
        assert state.unassigned_words == ["Die", "Katze", "saß"]
        assert state.assigned_words == {}

        # Validate - should fail
        is_valid, errors = viewmodel.validate()
        assert is_valid is False
        assert len(errors) == 4  # 3 empty columns + 3 unassigned words

        # Assign words one by one
        viewmodel.assign_word("Die", 0)  # The -> Die
        viewmodel.assign_word("Katze", 1)  # cat -> Katze
        viewmodel.assign_word("saß", 2)  # sat -> saß

        # Validate - should pass
        is_valid, errors = viewmodel.validate()
        assert is_valid is True
        assert errors == []

        # Convert to alignments for saving
        alignments = viewmodel.to_word_alignments()
        assert len(alignments) == 3
        assert all(isinstance(a, WordAlignment) for a in alignments)

    def test_edit_existing_alignment_workflow(self):
        """Test editing existing alignment."""
        # Start with existing alignment
        sentence = Sentence(
            source_text="I like cats",
            natural_translation="Ich mag Katzen",
            word_alignments=[
                WordAlignment(source_word="I", target_word="Ich", position=0),
                WordAlignment(source_word="like", target_word="mag", position=1),
                WordAlignment(source_word="cats", target_word="Katzen", position=2),
            ],
        )

        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # User realizes "mag" should be with "cats" instead
        viewmodel.unassign_word("mag", 1)
        viewmodel.assign_word("mag", 2)

        # Now column 2 has two words
        state = viewmodel.get_state()
        assert state.assigned_words[2] == ["Katzen", "mag"]
        assert 1 not in state.assigned_words  # Column 1 now empty

        # Validation should fail (column 1 empty)
        is_valid, _ = viewmodel.validate()
        assert is_valid is False

    def test_complex_alignment_with_word_order_changes(self):
        """Test alignment with word order changes."""
        sentence = Sentence(
            source_text="I will miss you",
            natural_translation="Ich werde dich vermissen",
            word_alignments=[
                WordAlignment(source_word="I", target_word="Ich", position=0),
                WordAlignment(source_word="will", target_word="werde", position=1),
                WordAlignment(source_word="miss", target_word="vermissen", position=2),
                WordAlignment(source_word="you", target_word="dich", position=3),
            ],
        )

        viewmodel = AlignmentEditorViewModel()
        viewmodel.load_sentence(sentence)

        # User decides "dich" and "vermissen" should be together
        viewmodel.unassign_word("dich", 3)
        viewmodel.assign_word("dich", 2)  # Move to "miss" column

        state = viewmodel.get_state()
        assert state.assigned_words[2] == ["vermissen", "dich"]
        assert 3 not in state.assigned_words

        # Convert to alignments
        alignments = viewmodel.to_word_alignments()
        miss_alignment = next(a for a in alignments if a.source_word == "miss")
        assert miss_alignment.target_word == "vermissen-dich"
