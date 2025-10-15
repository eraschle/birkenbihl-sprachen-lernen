"""Tests for AlignmentController."""

from PySide6.QtCore import QObject
from pytestqt.qtbot import QtBot

from birkenbihl.gui.controllers.alignment_controller import AlignmentController


class TestAlignmentController:
    """Tests for AlignmentController."""

    def test_init_without_mappings(self):
        """Test initialization without initial mappings."""
        target_words = ["Ich", "werde", "dich", "vermissen"]
        controller = AlignmentController(target_words)

        assert controller.get_mappings() == {}
        assert controller.has_available_words() is True
        assert controller.get_available_words() == target_words

    def test_init_with_mappings(self):
        """Test initialization with initial mappings."""
        target_words = ["Ich", "werde", "dich", "vermissen"]
        initial = {"Yo": ["Ich"], "te": ["dich"]}
        controller = AlignmentController(target_words, initial)

        assert controller.get_mappings() == initial
        assert controller.get_assigned_words("Yo") == ["Ich"]
        assert controller.get_assigned_words("te") == ["dich"]

    def test_get_available_words_excludes_mapped(self):
        """Test that get_available_words excludes already mapped words."""
        target_words = ["Ich", "werde", "dich", "vermissen"]
        initial = {"Yo": ["Ich"], "te": ["dich"]}
        controller = AlignmentController(target_words, initial)

        available = controller.get_available_words()

        assert "Ich" not in available
        assert "dich" not in available
        assert "werde" in available
        assert "vermissen" in available

    def test_get_available_words_includes_current_source(self):
        """Test that get_available_words includes words for current source."""
        target_words = ["Ich", "werde", "dich", "vermissen"]
        initial = {"Yo": ["Ich"], "te": ["dich"]}
        controller = AlignmentController(target_words, initial)

        # For "Yo", should include "Ich" even though it's assigned to "Yo"
        available = controller.get_available_words(for_source_word="Yo")

        assert "Ich" in available
        assert "dich" not in available  # Assigned to different source
        assert "werde" in available
        assert "vermissen" in available

    def test_get_available_words_preserves_order(self):
        """Test that available words maintain original order."""
        target_words = ["Ich", "werde", "dich", "vermissen"]
        initial = {"te": ["dich"]}  # Assign middle word
        controller = AlignmentController(target_words, initial)

        available = controller.get_available_words()

        # Should maintain order: Ich, werde, vermissen (dich skipped)
        assert available == ["Ich", "werde", "vermissen"]

    def test_add_word_emits_signal(self, qtbot: QtBot):
        """Test that add_word emits mappings_changed signal."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)

        with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
            controller.add_word("Yo", "Ich")

        assert controller.get_assigned_words("Yo") == ["Ich"]

    def test_add_word_prevents_duplicates(self, qtbot: QtBot):
        """Test that adding same word twice doesn't duplicate."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)

        # First add
        with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
            controller.add_word("Yo", "Ich")

        # Second add should not emit signal (no change)
        with qtbot.assertNotEmitted(controller.mappings_changed, wait=100):
            controller.add_word("Yo", "Ich")

        assert controller.get_assigned_words("Yo") == ["Ich"]  # Only once

    def test_remove_word_emits_signal(self, qtbot: QtBot):
        """Test that remove_word emits mappings_changed signal."""
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)

        with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
            controller.remove_word("Yo", "Ich")

        assert controller.get_assigned_words("Yo") == []

    def test_remove_nonexistent_word_no_signal(self, qtbot: QtBot):
        """Test that removing nonexistent word doesn't emit signal."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)

        # Try to remove word that was never added
        with qtbot.assertNotEmitted(controller.mappings_changed, wait=100):
            controller.remove_word("Yo", "Ich")

    def test_has_available_words_true(self):
        """Test has_available_words returns True when words remain."""
        target_words = ["Ich", "werde", "dich"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)

        assert controller.has_available_words() is True

    def test_has_available_words_false(self):
        """Test has_available_words returns False when all assigned."""
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"], "te": ["werde"]}
        controller = AlignmentController(target_words, initial)

        assert controller.has_available_words() is False

    def test_get_mappings_returns_copy(self):
        """Test that get_mappings returns copy, not reference."""
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)

        mappings = controller.get_mappings()
        mappings["Yo"].append("werde")  # Modify copy

        # Original should be unchanged
        assert controller.get_assigned_words("Yo") == ["Ich"]

    def test_get_assigned_words_returns_copy(self):
        """Test that get_assigned_words returns copy."""
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)

        words = controller.get_assigned_words("Yo")
        words.append("werde")  # Modify copy

        # Original should be unchanged
        assert controller.get_assigned_words("Yo") == ["Ich"]

    def test_get_assigned_words_empty(self):
        """Test get_assigned_words for source with no mappings."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)

        assert controller.get_assigned_words("Yo") == []

    def test_clear_mappings(self, qtbot: QtBot):
        """Test clear_mappings removes all mappings and emits signal."""
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"], "te": ["werde"]}
        controller = AlignmentController(target_words, initial)

        with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
            controller.clear_mappings()

        assert controller.get_mappings() == {}
        assert controller.has_available_words() is True

    def test_clear_empty_mappings_no_signal(self, qtbot: QtBot):
        """Test clear_mappings on empty controller doesn't emit signal."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)

        with qtbot.assertNotEmitted(controller.mappings_changed, wait=100):
            controller.clear_mappings()

    def test_multiple_words_per_source(self):
        """Test that multiple words can be assigned to same source."""
        target_words = ["Ich", "werde", "dich", "vermissen"]
        controller = AlignmentController(target_words)

        controller.add_word("extrañaré", "werde")
        controller.add_word("extrañaré", "vermissen")

        assert controller.get_assigned_words("extrañaré") == ["werde", "vermissen"]
        assert "werde" not in controller.get_available_words()
        assert "vermissen" not in controller.get_available_words()
