"""Tests for LanguageSelector widget."""

import conftest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from birkenbihl.gui.widgets.language_selector import LanguageSelector


class TestLanguageSelector:
    """Test LanguageSelector widget."""

    def test_widget_creation(self, qapp: QApplication):
        """Test widget creation."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = LanguageSelector()
        assert widget is not None

    def test_widget_with_auto_detect(self, qapp: QApplication):
        """Test widget with auto-detect option."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = LanguageSelector(show_auto_detect=True)
        assert widget._combo.itemData(0) == "auto"
        assert widget._combo.itemText(0) == "Autom. Erkennen"

    def test_default_language_selection(self, qapp: QApplication):
        """Test default language is selected."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = LanguageSelector(default_language="en")
        assert widget.get_selected_language() == "en"

    def test_language_selection_signal(self, qtbot: QtBot):
        """Test language selection emits signal."""
        widget = LanguageSelector()
        selected = []
        widget.language_selected.connect(lambda lang: selected.append(lang))

        # Find index of English
        for i in range(widget._combo.count()):
            if widget._combo.itemData(i) == "en":
                with qtbot.waitSignal(widget.language_selected, timeout=1000):
                    widget._combo.setCurrentIndex(i)
                break

        assert len(selected) == 1
        assert selected[0] == "en"

    def test_set_language(self, qapp: QApplication):
        """Test programmatic language selection."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = LanguageSelector()
        widget.set_language("es")

        assert widget.get_selected_language() == "es"

    def test_enable_disable(self, qapp: QApplication):
        """Test enable/disable functionality."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = LanguageSelector()

        widget.set_enabled(False)
        assert not widget._combo.isEnabled()

        widget.set_enabled(True)
        assert widget._combo.isEnabled()
