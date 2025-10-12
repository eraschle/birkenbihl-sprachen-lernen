"""Pytest configuration and fixtures."""

import sys

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Provide QApplication instance for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
    # Don't quit the app as it may be used by other tests


@pytest.fixture
def qtbot(qapp: QApplication, qtbot):
    """Provide qtbot fixture with qapp dependency."""
    return qtbot
