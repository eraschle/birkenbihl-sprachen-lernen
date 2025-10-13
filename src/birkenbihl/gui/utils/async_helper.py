"""Async/threading utilities for running long operations in background."""

from collections.abc import Callable

from PySide6.QtCore import QMutex, QMutexLocker, QThread, Signal


class AsyncWorker(QThread):
    """Generic worker for running functions in background thread.

    Emits signals for progress updates, completion, and errors.
    Supports cancellation via stop flag.
    """

    progress_updated = Signal(float, str)  # progress (0-1), message
    task_completed = Signal(object)  # result data
    task_failed = Signal(str)  # error message

    def __init__(self, func: Callable, *args: object, **kwargs: object):
        """Initialize worker with function and arguments.

        Args:
            func: Function to execute in background
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        """
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._stop_flag = False
        self._mutex = QMutex()

    def run(self) -> None:
        """Execute function in background thread."""
        try:
            result = self._func(*self._args, **self._kwargs)
            if not self._stop_flag:
                self.task_completed.emit(result)
        except Exception as e:
            if not self._stop_flag:
                self.task_failed.emit(str(e))

    def stop(self) -> None:
        """Request cancellation of task."""
        with QMutexLocker(self._mutex):
            self._stop_flag = True

    @property
    def is_stopped(self) -> bool:
        """Check if task was cancelled."""
        with QMutexLocker(self._mutex):
            return self._stop_flag


def run_in_background(func: Callable, *args: object, **kwargs: object) -> AsyncWorker:
    """Run function in background thread.

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        AsyncWorker instance (not started yet, call .start())
    """
    return AsyncWorker(func, *args, **kwargs)
