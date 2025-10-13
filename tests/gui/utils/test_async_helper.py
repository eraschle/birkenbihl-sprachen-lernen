"""Tests for async/threading utilities."""

import time

from pytestqt.qtbot import QtBot

from birkenbihl.gui.utils.async_helper import AsyncWorker, run_in_background


class TestAsyncWorker:
    """Test AsyncWorker class."""

    def test_worker_creation(self):
        """Test AsyncWorker creation."""

        def test_func():
            return "result"

        worker = AsyncWorker(test_func)
        assert worker is not None
        assert not worker.isRunning()

    def test_worker_execution_success(self, qtbot: QtBot):
        """Test successful worker execution."""
        result = []

        def test_func():
            return "success"

        worker = AsyncWorker(test_func)
        worker.task_completed.connect(lambda x: result.append(x))

        with qtbot.waitSignal(worker.task_completed, timeout=1000):
            worker.start()

        assert len(result) == 1
        assert result[0] == "success"

    def test_worker_execution_failure(self, qtbot: QtBot):
        """Test worker execution with exception."""
        errors = []

        def test_func():
            raise ValueError("Test error")

        worker = AsyncWorker(test_func)
        worker.task_failed.connect(lambda x: errors.append(x))

        with qtbot.waitSignal(worker.task_failed, timeout=1000):
            worker.start()

        assert len(errors) == 1
        assert "Test error" in errors[0]

    def test_worker_with_arguments(self, qtbot: QtBot):
        """Test worker with function arguments."""
        result = []

        def add(a: float, b: float):
            return a + b

        worker = AsyncWorker(add, 5, 3)
        worker.task_completed.connect(lambda x: result.append(x))

        with qtbot.waitSignal(worker.task_completed, timeout=1000):
            worker.start()

        assert len(result) == 1
        assert result[0] == 8

    def test_worker_stop(self):
        """Test worker cancellation."""

        def long_running():
            time.sleep(0.1)
            return "done"

        worker = AsyncWorker(long_running)
        worker.start()
        worker.stop()
        worker.wait()  # Wait for thread to finish

        assert worker.is_stopped is True


class TestRunInBackground:
    """Test run_in_background helper function."""

    def test_run_in_background(self):
        """Test run_in_background helper."""

        def test_func():
            return "background"

        worker = run_in_background(test_func)
        assert isinstance(worker, AsyncWorker)
        assert not worker.isRunning()

    def test_run_in_background_with_args(self, qtbot: QtBot):
        """Test run_in_background with arguments."""
        result = []

        def multiply(x: float, y: float):
            return x * y

        worker = run_in_background(multiply, 4, 5)
        worker.task_completed.connect(lambda x: result.append(x))

        with qtbot.waitSignal(worker.task_completed, timeout=1000):
            worker.start()

        assert len(result) == 1
        assert result[0] == 20
