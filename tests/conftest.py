"""Pytest configuration and fixtures."""

import sys

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Provide QApplication instance for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    if not isinstance(app, QApplication):
        app = QApplication(sys.argv)
    return app
    # Don't quit the app as it may be used by other tests


@pytest.fixture
def qtbot(qapp: QApplication, qtbot: QtBot) -> QtBot:
    """Provide qtbot fixture with qapp dependency."""
    skrip_test_when_is_not_valid(qapp)
    return qtbot


def skrip_test_when_is_not_valid(object: object | None) -> None:
    """Provide qtbot fixture with qapp dependency."""
    if object is None:
        pytest.skip(f"Object {object} is None")
