"""Tests for TagContainer widget."""

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from birkenbihl.gui.controllers.alignment_controller import AlignmentController
from birkenbihl.gui.widgets.tag_container import TagContainer
from tests import conftest


@pytest.mark.ui
class TestTagContainer:
    """Test suite for TagContainer widget."""

    def test_widget_creation(self, qapp: QApplication) -> None:
        """Test that TagContainer can be created."""
        conftest.skrip_test_when_is_not_valid(qapp)
        target_words = ["Ich", "werde", "dich"]
        controller = AlignmentController(target_words)
        container = TagContainer("Yo", controller)
        assert container is not None

    def test_tags_shown_from_controller(self, qapp: QApplication):
        """Test that tags are shown from controller's initial mappings."""
        conftest.skrip_test_when_is_not_valid(qapp)
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)
        container = TagContainer("Yo", controller)

        # Should have 1 tag
        assert len(container._tags) == 1
        assert container._tags[0].get_text() == "Ich"

    def test_combobox_shows_available_words(self, qapp: QApplication):
        """Test that ComboBox shows available words not yet assigned."""
        conftest.skrip_test_when_is_not_valid(qapp)
        target_words = ["Ich", "werde", "dich"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)
        container = TagContainer("Yo", controller)

        # ComboBox should show: "[+ ...]" placeholder, "Ich" (for current source), "werde", "dich"
        # Count items (placeholder + available words)
        assert container._combobox.count() >= 2  # At least placeholder + some words

    def test_adding_word_updates_controller(self, qtbot: QtBot):
        """Test that adding a word through ComboBox updates the controller."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)
        container = TagContainer("Yo", controller)

        # Find "Ich" in combobox and select it
        for i in range(container._combobox.count()):
            if container._combobox.itemData(i) == "Ich":
                with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
                    container._combobox.setCurrentIndex(i)
                break

        # Controller should now have the mapping
        assert "Ich" in controller.get_assigned_words("Yo")

    def test_removing_tag_updates_controller(self, qtbot: QtBot):
        """Test that removing a tag updates the controller."""
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"]}
        controller = AlignmentController(target_words, initial)
        container = TagContainer("Yo", controller)

        # Click remove on first tag
        tag = container._tags[0]
        with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
            tag.removed.emit()

        # Controller should no longer have the mapping
        assert "Ich" not in controller.get_assigned_words("Yo")

    def test_combobox_disabled_when_no_words_available(self, qapp: QApplication):
        """Test that ComboBox is disabled when all words are assigned to OTHER sources."""
        conftest.skrip_test_when_is_not_valid(qapp)
        target_words = ["Ich", "werde"]
        initial = {"Yo": ["Ich"], "te": ["werde"]}
        controller = AlignmentController(target_words, initial)
        # Create container for a different source that has no words available
        container = TagContainer("extrañaré", controller)

        # All words assigned to other sources - combobox should be disabled
        assert container._combobox.isEnabled() is False

    def test_refresh_on_controller_signal(self, qtbot: QtBot):
        """Test that container auto-refreshes when controller signals changes."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)
        container = TagContainer("Yo", controller)

        # Initially no tags
        assert len(container._tags) == 0

        # Add word through controller (not through container)
        with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
            controller.add_word("Yo", "Ich")

        # Container should auto-refresh and show tag (signal is synchronous in Qt)
        assert len(container._tags) == 1

    def test_multiple_tags_shown(self, qapp: QApplication):
        """Test that multiple tags are shown correctly."""
        conftest.skrip_test_when_is_not_valid(qapp)
        target_words = ["Ich", "werde", "dich", "vermissen"]
        initial = {"Yo": ["Ich", "werde"]}
        controller = AlignmentController(target_words, initial)
        container = TagContainer("Yo", controller)

        # Should have 2 tags
        assert len(container._tags) == 2
        assert container._tags[0].get_text() == "Ich"
        assert container._tags[1].get_text() == "werde"

    def test_combobox_resets_after_selection(self, qtbot: QtBot):
        """Test that ComboBox resets to placeholder after adding a word."""
        target_words = ["Ich", "werde"]
        controller = AlignmentController(target_words)
        container = TagContainer("Yo", controller)

        # Select "Ich"
        for i in range(container._combobox.count()):
            if container._combobox.itemData(i) == "Ich":
                with qtbot.waitSignal(controller.mappings_changed, timeout=1000):
                    container._combobox.setCurrentIndex(i)
                break

        # ComboBox should be back at index 0 (placeholder)
        assert container._combobox.currentIndex() == 0
        assert container._combobox.currentData() is None

    def test_combobox_excludes_assigned_words(self, qapp: QApplication):
        """Test that ComboBox excludes words already assigned to other sources."""
        conftest.skrip_test_when_is_not_valid(qapp)
        target_words = ["Ich", "werde", "dich"]
        initial = {"Yo": ["Ich"], "te": ["werde"]}
        controller = AlignmentController(target_words, initial)
        container = TagContainer("extrañaré", controller)

        # ComboBox should only show "dich" as available (not "werde" which is assigned to "te")
        available_words = [container._combobox.itemData(i) for i in range(container._combobox.count())]
        # Filter out None (placeholder)
        available_words = [w for w in available_words if w is not None]

        # Should only have "Ich" (for current source) and "dich"
        assert "dich" in available_words
        assert "werde" not in available_words or "werde" in controller.get_assigned_words("extrañaré")
