"""Tests for async/threading utilities."""

import time

import pytest

from birkenbihl.gui.utils.async_helper import AsyncWorker, run_in_background


class TestAsyncWorker:
    """Test AsyncWorker class."""

    @pytest.fixture
    def qapp(self, qapp):
        """Provide QApplication instance."""
        return qapp

    def test_worker_creation(self):
        """Test AsyncWorker creation."""

        def test_func():
            return "result"

        worker = AsyncWorker(test_func)
        assert worker is not None
        assert not worker.isRunning()

    def test_worker_execution_success(self, qtbot):
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

    def test_worker_execution_failure(self, qtbot):
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

    def test_worker_with_arguments(self, qapp, qtbot):
        """Test worker with function arguments."""
        result = []

        def add(a, b):
            return a + b

        worker = AsyncWorker(add, 5, 3)
        worker.task_completed.connect(lambda x: result.append(x))

        with qtbot.waitSignal(worker.task_completed, timeout=1000):
            worker.start()

        assert len(result) == 1
        assert result[0] == 8

    def test_worker_stop(self, qapp):
        """Test worker cancellation."""

        def long_running():
            time.sleep(0.1)
            return "done"

        worker = AsyncWorker(long_running)
        worker.start()
        worker.stop()

        assert worker.is_stopped is True


class TestRunInBackground:
    """Test run_in_background helper function."""

    @pytest.fixture
    def qapp(self, qapp):
        """Provide QApplication instance."""
        return qapp

    def test_run_in_background(self, qapp):
        """Test run_in_background helper."""

        def test_func():
            return "background"

        worker = run_in_background(test_func)
        assert isinstance(worker, AsyncWorker)
        assert not worker.isRunning()

    def test_run_in_background_with_args(self, qapp, qtbot):
        """Test run_in_background with arguments."""
        result = []

        def multiply(x, y):
            return x * y

        worker = run_in_background(multiply, 4, 5)
        worker.task_completed.connect(lambda x: result.append(x))

        with qtbot.waitSignal(worker.task_completed, timeout=1000):
            worker.start()

        assert len(result) == 1
        assert result[0] == 20
