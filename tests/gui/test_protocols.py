"""Tests for base protocols."""

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from birkenbihl.gui.commands.base import CommandResult


# Test Command Protocol Implementation
class TestCommandProtocol:
    """Test Command protocol and CommandResult."""

    def test_command_result_creation(self):
        """Test CommandResult dataclass creation."""
        result = CommandResult(success=True, message="Success", data={"key": "value"})

        assert result.success is True
        assert result.message == "Success"
        assert result.data == {"key": "value"}

    def test_command_result_defaults(self):
        """Test CommandResult default values."""
        result = CommandResult(success=False)

        assert result.success is False
        assert result.message == ""
        assert result.data is None

    def test_command_protocol_implementation(self):
        """Test Command protocol implementation."""

        class TestCommand:
            def execute(self) -> CommandResult:
                return CommandResult(success=True, message="Executed")

            def can_execute(self) -> bool:
                return True

        cmd = TestCommand()
        assert cmd.can_execute() is True

        result = cmd.execute()
        assert result.success is True
        assert result.message == "Executed"


# Test ViewModel Protocol Implementation
class TestViewModelProtocol:
    """Test ViewModel protocol."""

    @pytest.fixture
    def qapp(self, qapp):
        """Provide QApplication instance."""
        return qapp

    def test_viewmodel_protocol_implementation(self, qapp):
        """Test ViewModel protocol implementation."""

        class TestViewModel(QObject):
            state_changed = Signal()

            def initialize(self) -> None:
                pass

            def cleanup(self) -> None:
                pass

        vm = TestViewModel()
        assert isinstance(vm, QObject)
        assert hasattr(vm, "initialize")
        assert hasattr(vm, "cleanup")
        assert hasattr(vm, "state_changed")

        vm.initialize()
        vm.cleanup()


# Test View Protocol Implementation
class TestViewProtocol:
    """Test View protocol."""

    @pytest.fixture
    def qapp(self, qapp):
        """Provide QApplication instance."""
        return qapp

    def test_view_protocol_implementation(self, qapp):
        """Test View protocol implementation."""

        class TestView(QWidget):
            def setup_ui(self) -> None:
                pass

            def bind_viewmodel(self) -> None:
                pass

        view = TestView()
        assert isinstance(view, QWidget)
        assert hasattr(view, "setup_ui")
        assert hasattr(view, "bind_viewmodel")

        view.setup_ui()
        view.bind_viewmodel()
