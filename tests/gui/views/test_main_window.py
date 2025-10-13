"""Tests for MainWindow."""

from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest
from pytestqt.qtbot import QtBot

from birkenbihl.gui.views.main_window import MainWindow
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.models.translation import Sentence, Translation, WordAlignment


@pytest.fixture
def translation():
    """Create test translation."""
    sentence = Sentence(
        uuid=uuid4(),
        source_text="Hello",
        natural_translation="Hallo",
        word_alignments=[WordAlignment(source_word="Hello", target_word="Hallo", position=0)],
    )
    return Translation(
        uuid=uuid4(),
        title="Test Translation",
        source_language=Language(code="en", name_de="Englisch", name_en="English"),
        target_language=Language(code="de", name_de="Deutsch", name_en="German"),
        sentences=[sentence],
    )


@pytest.fixture
def settings():
    """Create test settings."""
    provider = ProviderConfig(
        name="TestProvider",
        provider_type="openai",
        model="gpt-4",
        api_key="test-key",
        is_default=True,
    )
    return Settings(providers=[provider], target_language="de")


@pytest.fixture
def mock_translation_service(translation: Translation):
    """Create mock TranslationService."""
    service = Mock()
    service.translate_and_save.return_value = translation
    service.get_translation.return_value = translation
    service.list_all_translations.return_value = [translation]
    return service


@pytest.fixture
def mock_settings_service(settings: Settings):
    """Create mock SettingsService."""
    service = Mock()
    service.get_settings.return_value = settings
    return service


@pytest.fixture
def main_window(qtbot: QtBot, mock_translation_service: MagicMock, mock_settings_service: MagicMock):
    """Create MainWindow."""
    window = MainWindow(mock_translation_service, mock_settings_service)
    qtbot.addWidget(window)
    return window


def test_window_title(main_window: MainWindow):
    """Test window title is set."""
    assert main_window.windowTitle() == "Birkenbihl Sprachtrainer"


def test_window_geometry(main_window: MainWindow):
    """Test window has correct size."""
    size = main_window.size()
    assert size.width() == 1200
    assert size.height() == 800


def test_window_minimum_size(main_window: MainWindow):
    """Test window has minimum size."""
    min_size = main_window.minimumSize()
    assert min_size.width() == 800
    assert min_size.height() == 600


def test_has_central_widget(main_window: MainWindow):
    """Test main window has central widget."""
    assert main_window.centralWidget() is not None


def test_has_menu_bar(main_window: MainWindow):
    """Test main window has menu bar."""
    menubar = main_window.menuBar()
    assert menubar is not None


def test_has_file_menu(main_window: MainWindow):
    """Test has File menu."""
    menubar = main_window.menuBar()
    actions = menubar.actions()
    assert len(actions) >= 1
    assert any("Datei" in action.text() for action in actions)


def test_has_view_menu(main_window: MainWindow):
    """Test has View menu."""
    menubar = main_window.menuBar()
    actions = menubar.actions()
    assert any("Ansicht" in action.text() for action in actions)


def test_has_help_menu(main_window: MainWindow):
    """Test has Help menu."""
    menubar = main_window.menuBar()
    actions = menubar.actions()
    assert any("Hilfe" in action.text() for action in actions)


def test_show_translation_view(main_window: MainWindow):
    """Test show translation view."""
    main_window.show_translation_view()
    current = main_window._stacked_widget.currentWidget()
    assert current == main_window._translation_view


def test_show_editor_view(main_window: MainWindow):
    """Test show editor view."""
    main_window.show_editor_view()
    current = main_window._stacked_widget.currentWidget()
    assert current == main_window._editor_view


def test_show_settings_view(main_window: MainWindow):
    """Test show settings view."""
    main_window.show_settings_view()
    current = main_window._stacked_widget.currentWidget()
    assert current == main_window._settings_view


def test_default_view_is_translation(main_window: MainWindow):
    """Test default view is translation view."""
    current = main_window._stacked_widget.currentWidget()
    assert current == main_window._translation_view


def test_close_event(main_window: MainWindow):
    """Test close event is accepted."""
    main_window.close()
    # Should close without errors
    assert True


def test_views_initialized(main_window: MainWindow):
    """Test all views are initialized."""
    assert main_window._translation_view is not None
    assert main_window._editor_view is not None
    assert main_window._settings_view is not None


def test_stacked_widget_has_three_widgets(main_window: MainWindow):
    """Test stacked widget has all three views."""
    assert main_window._stacked_widget.count() == 3
