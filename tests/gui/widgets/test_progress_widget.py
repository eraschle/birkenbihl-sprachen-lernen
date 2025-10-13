"""Tests for ProgressWidget."""

from pytestqt.qtbot import QtBot

from birkenbihl.gui.widgets.progress_widget import ProgressWidget


class TestProgressWidget:
    """Test ProgressWidget."""

    def test_widget_creation(self):
        """Test widget creation."""
        widget = ProgressWidget()
        assert widget is not None
        assert not widget.isVisible()

    def test_set_progress(self):
        """Test setting progress value."""
        widget = ProgressWidget()

        widget.set_progress(0.5)
        assert widget._progress_bar.value() == 50

        widget.set_progress(1.0)
        assert widget._progress_bar.value() == 100

    def test_set_message(self):
        """Test setting message."""
        widget = ProgressWidget()
        message = "Processing..."

        widget.set_message(message)
        assert widget._message_label.text() == message

    def test_start(self):
        """Test start method."""
        widget = ProgressWidget()

        widget.start("Starting...")
        assert widget.isVisible()
        assert widget._message_label.text() == "Starting..."
        assert widget._progress_bar.value() == 0

    def test_finish(self):
        """Test finish method."""
        widget = ProgressWidget()
        widget.start()

        widget.finish()
        assert not widget.isVisible()
        assert widget._progress_bar.value() == 100

    def test_cancel_signal(self, qtbot: QtBot):
        """Test cancel button emits signal."""
        widget = ProgressWidget()
        cancelled = []
        widget.cancel_requested.connect(lambda: cancelled.append(True))

        with qtbot.waitSignal(widget.cancel_requested, timeout=1000):
            widget._cancel_button.click()

        assert len(cancelled) == 1

    def test_cancel_enabled(self):
        """Test enable/disable cancel button."""
        widget = ProgressWidget()

        widget.set_cancel_enabled(False)
        assert not widget._cancel_button.isEnabled()

        widget.set_cancel_enabled(True)
        assert widget._cancel_button.isEnabled()
