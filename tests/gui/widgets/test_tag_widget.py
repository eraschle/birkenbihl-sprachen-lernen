"""Tests for TagWidget."""

from PySide6.QtCore import QEvent, QPointF
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from birkenbihl.gui.widgets.tag_widget import TagWidget
from tests import conftest


class TestTagWidget:
    """Test TagWidget."""

    def test_widget_creation(self, qapp: QApplication):
        """Test widget can be created."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = TagWidget("test")
        assert widget is not None

    def test_get_text_returns_correct_text(self, qapp: QApplication):
        """Test get_text() returns the text passed in __init__."""
        conftest.skrip_test_when_is_not_valid(qapp)
        text = "My Tag"
        widget = TagWidget(text)
        assert widget.get_text() == text

    def test_close_button_initially_hidden(self, qapp: QApplication):
        """Test _close_btn is hidden initially."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = TagWidget("test")
        widget.show()
        assert widget._close_btn.isHidden()

    def test_hover_shows_close_button(self, qapp: QApplication):
        """Test that enterEvent shows the close button."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = TagWidget("test")
        widget.show()

        # Trigger enter event
        event = QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
        widget.enterEvent(event)

        assert not widget._close_btn.isHidden()

    def test_leave_hides_close_button(self, qapp: QApplication):
        """Test that leaveEvent hides the close button after enterEvent."""
        conftest.skrip_test_when_is_not_valid(qapp)
        widget = TagWidget("test")
        widget.show()

        # First show the button
        enter_event = QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
        widget.enterEvent(enter_event)
        assert not widget._close_btn.isHidden()

        # Then hide it
        leave_event = QEvent(QEvent.Type.Leave)
        widget.leaveEvent(leave_event)
        assert widget._close_btn.isHidden()

    def test_close_button_emits_removed_signal(self, qtbot: QtBot):
        """Test that clicking _close_btn emits removed signal."""
        widget = TagWidget("test")
        removed_count = []
        widget.removed.connect(lambda: removed_count.append(True))

        with qtbot.waitSignal(widget.removed, timeout=1000):
            widget._close_btn.click()

        assert len(removed_count) == 1

    def test_label_displays_text(self, qapp: QApplication):
        """Test that _label.text() matches input text."""
        conftest.skrip_test_when_is_not_valid(qapp)
        text = "Sample Tag Text"
        widget = TagWidget(text)
        assert widget._label.text() == text
