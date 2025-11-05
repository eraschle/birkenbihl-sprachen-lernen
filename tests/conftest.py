"""Pytest configuration and fixtures."""

import sys

import pytest

# Try to import Qt - if it fails, Qt tests will be skipped
QT_AVAILABLE = True
try:
    from PySide6.QtWidgets import QApplication
    from pytestqt.qtbot import QtBot
except ImportError as e:
    QT_AVAILABLE = False
    _QT_IMPORT_ERROR = str(e)


@pytest.fixture(scope="session")
def qapp():
    """Provide QApplication instance for Qt tests."""
    if not QT_AVAILABLE:
        pytest.skip(f"Qt not available: {_QT_IMPORT_ERROR}")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    if not isinstance(app, QApplication):
        app = QApplication(sys.argv)
    return app
    # Don't quit the app as it may be used by other tests


@pytest.fixture
def qtbot(qapp, request):
    """Provide qtbot fixture with qapp dependency."""
    if not QT_AVAILABLE:
        pytest.skip(f"Qt not available: {_QT_IMPORT_ERROR}")

    skrip_test_when_is_not_valid(qapp)

    # Get qtbot from pytest-qt plugin
    from pytestqt.qtbot import QtBot

    bot = QtBot(request)
    return bot


def skrip_test_when_is_not_valid(object: object | None) -> None:
    """Provide qtbot fixture with qapp dependency."""
    if object is None:
        pytest.skip(f"Object {object} is None")
