"""Tests for TranslationCreationViewModel."""

import pytest
from pytestqt.qtbot import QtBot
from unittest.mock import MagicMock, Mock
from uuid import uuid4

from birkenbihl.gui.models.translation_viewmodel import TranslationCreationViewModel
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services.translation_service import TranslationService


@pytest.fixture
def mock_service():
    """Create mock TranslationService."""
    service = Mock()
    translation = Translation(
        uuid=uuid4(),
        title="Test Translation",
        source_language=Language(code="en", name_de="Englisch", name_en="English"),
        target_language=Language(code="de", name_de="Deutsch", name_en="German"),
        sentences=[
            Sentence(
                uuid=uuid4(),
                source_text="Hello",
                natural_translation="Hallo",
                word_alignments=[WordAlignment(source_word="Hello", target_word="Hallo", position=0)],
            )
        ],
    )
    service.translate_and_save.return_value = translation
    return service


@pytest.fixture
def mock_settings():
    """Create mock Settings."""
    provider = ProviderConfig(
        name="Test",
        provider_type="openai",
        model="gpt-4",
        api_key="test-key",
    )
    return Settings(providers=[provider], target_language="de")


@pytest.fixture
def viewmodel(mock_service: TranslationService):
    """Create TranslationCreationViewModel."""
    vm = TranslationCreationViewModel(mock_service)
    return vm


def test_initial_state(viewmodel: TranslationCreationViewModel):
    """Test initial state."""
    state = viewmodel.state
    assert state.title == ""
    assert state.source_text == ""
    assert state.source_language.code == "auto"
    assert state.target_language.code == "de"
    assert state.selected_provider is None
    assert not state.is_translating
    assert state.progress == 0.0


def test_set_title(qtbot: QtBot, viewmodel: TranslationCreationViewModel):
    """Test set title."""
    signals = []
    viewmodel.state_changed.connect(lambda s: signals.append(s))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_title("Test Title")

    assert viewmodel.state.title == "Test Title"
    assert len(signals) == 1


def test_set_source_text(qtbot: QtBot, viewmodel: TranslationCreationViewModel):
    """Test set source text."""
    signals = []
    viewmodel.state_changed.connect(lambda s: signals.append(s))

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_source_text("Hello World")

    assert viewmodel.state.source_text == "Hello World"
    assert len(signals) == 1


def test_set_source_language(qtbot: QtBot, viewmodel: TranslationCreationViewModel):
    """Test set source language."""
    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_source_language("en")

    assert viewmodel.state.source_language.code == "en"


def test_set_target_language(qtbot: QtBot, viewmodel: TranslationCreationViewModel):
    """Test set target language."""
    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_target_language("es")

    assert viewmodel.state.target_language.code == "es"


def test_set_provider(qtbot: QtBot, viewmodel: TranslationCreationViewModel, mock_settings: Settings):
    """Test set provider."""
    provider = mock_settings.providers[0]

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_provider(provider)

    assert viewmodel.state.selected_provider == provider


def test_can_translate_success(viewmodel: TranslationCreationViewModel, mock_settings: Settings):
    """Test can translate with valid data."""
    viewmodel.set_title("Test")
    viewmodel.set_source_text("Hello")
    viewmodel.set_source_language("en")
    viewmodel.set_target_language("de")
    viewmodel.set_provider(mock_settings.providers[0])

    assert viewmodel.can_translate()


def test_can_translate_missing_text(viewmodel: TranslationCreationViewModel, mock_settings: Settings):
    """Test can translate with missing text."""
    viewmodel.set_source_language("en")
    viewmodel.set_target_language("de")
    viewmodel.set_provider(mock_settings.providers[0])

    assert not viewmodel.can_translate()


def test_can_translate_missing_provider(viewmodel: TranslationCreationViewModel):
    """Test can translate with missing provider."""
    viewmodel.set_source_text("Hello")
    viewmodel.set_source_language("en")
    viewmodel.set_target_language("de")

    assert not viewmodel.can_translate()


def test_start_translation_emits_started(
    qtbot: QtBot, viewmodel: TranslationCreationViewModel, mock_settings: Settings
):
    """Test start translation emits started signal."""
    viewmodel.set_title("Test")
    viewmodel.set_source_text("Hello")
    viewmodel.set_source_language("en")
    viewmodel.set_target_language("de")
    viewmodel.set_provider(mock_settings.providers[0])

    with qtbot.waitSignal(viewmodel.translation_started, timeout=1000):
        viewmodel.start_translation()

    assert viewmodel.state.is_translating


def test_start_translation_success(
    qtbot: QtBot, viewmodel: TranslationCreationViewModel, mock_settings: Settings, mock_service: MagicMock
):
    """Test successful translation."""
    viewmodel.set_title("Test")
    viewmodel.set_source_text("Hello")
    viewmodel.set_source_language("en")
    viewmodel.set_target_language("de")
    viewmodel.set_provider(mock_settings.providers[0])

    with qtbot.waitSignal(viewmodel.translation_completed, timeout=5000):
        viewmodel.start_translation()

    mock_service.translate_and_save.assert_called_once()
    assert not viewmodel.state.is_translating


def test_reset(qtbot: QtBot, viewmodel: TranslationCreationViewModel, mock_settings: MagicMock):
    """Test reset state."""
    viewmodel.set_title("Test")
    viewmodel.set_source_text("Hello")
    viewmodel.set_provider(mock_settings.providers[0])

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.reset()

    state = viewmodel.state
    assert state.title == ""
    assert state.source_text == ""
    assert state.selected_provider is None
    assert not state.is_translating
