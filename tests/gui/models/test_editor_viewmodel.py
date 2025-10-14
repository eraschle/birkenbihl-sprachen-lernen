"""Tests for TranslationEditorViewModel."""

from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest
from pytestqt.qtbot import QtBot

from birkenbihl.gui.models.editor_viewmodel import TranslationEditorViewModel
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.models.translation import Sentence, Translation, WordAlignment


@pytest.fixture
def translation():
    """Create test translation."""
    sentence1 = Sentence(
        uuid=uuid4(),
        source_text="Hello",
        natural_translation="Hallo",
        word_alignments=[WordAlignment(source_word="Hello", target_word="Hallo", position=0)],
    )
    sentence2 = Sentence(
        uuid=uuid4(),
        source_text="World",
        natural_translation="Welt",
        word_alignments=[WordAlignment(source_word="World", target_word="Welt", position=0)],
    )
    return Translation(
        uuid=uuid4(),
        title="Test Translation",
        source_language=Language(code="en", name_de="Englisch", name_en="English"),
        target_language=Language(code="de", name_de="Deutsch", name_en="German"),
        sentences=[sentence1, sentence2],
    )


@pytest.fixture
def mock_service(translation: Translation):
    """Create mock TranslationService."""
    service = Mock()
    service.get_translation.return_value = translation
    service.update_sentence_natural.return_value = translation
    service.update_sentence_alignment.return_value = translation
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
def viewmodel(mock_service: MagicMock):
    """Create TranslationEditorViewModel."""
    vm = TranslationEditorViewModel(mock_service)
    return vm


def test_initial_state(viewmodel: TranslationEditorViewModel):
    """Test initial state."""
    state = viewmodel.state
    assert state.translation is None
    assert state.selected_sentence_uuid is None
    assert state.edit_mode == "view"
    assert not state.is_saving
    assert not state.has_unsaved_changes


def test_load_translation(
    qtbot: QtBot, viewmodel: TranslationEditorViewModel, mock_service: MagicMock, translation: Translation
):
    """Test load translation."""
    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.load_translation(translation.uuid)

    assert viewmodel.state.translation is not None
    assert viewmodel.state.translation.uuid == translation.uuid
    mock_service.get_translation.assert_called_once_with(translation.uuid)


def test_select_sentence(qtbot: QtBot, viewmodel: TranslationEditorViewModel, translation: Translation):
    """Test select sentence."""
    viewmodel._state.translation = translation
    sentence_uuid = translation.sentences[0].uuid

    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.select_sentence(sentence_uuid)

    assert viewmodel.state.selected_sentence_uuid == sentence_uuid


def test_set_edit_mode(qtbot: QtBot, viewmodel: TranslationEditorViewModel):
    """Test set edit mode."""
    with qtbot.waitSignal(viewmodel.state_changed, timeout=1000):
        viewmodel.set_edit_mode("edit_natural")

    assert viewmodel.state.edit_mode == "edit_natural"


def test_update_natural_translation(
    qtbot: QtBot,
    viewmodel: TranslationEditorViewModel,
    mock_service: MagicMock,
    translation: Translation,
    mock_settings: MagicMock,
):
    """Test update natural translation."""
    viewmodel._state.translation = translation
    viewmodel._state.selected_sentence_uuid = translation.sentences[0].uuid
    provider = mock_settings.providers[0]

    with qtbot.waitSignal(viewmodel.sentence_updated, timeout=1000):
        viewmodel.update_natural_translation("New translation", provider)

    mock_service.update_sentence_natural.assert_called_once()
    assert not viewmodel.state.is_saving


def test_update_alignment(
    qtbot: QtBot, viewmodel: TranslationEditorViewModel, mock_service: MagicMock, translation: Translation
):
    """Test update alignment."""
    viewmodel._state.translation = translation
    viewmodel._state.selected_sentence_uuid = translation.sentences[0].uuid
    new_alignments = [WordAlignment(source_word="Hello", target_word="Hi", position=0)]

    with qtbot.waitSignal(viewmodel.sentence_updated, timeout=1000):
        viewmodel.update_alignment(new_alignments)

    mock_service.update_sentence_alignment.assert_called_once()


def test_update_natural_no_sentence_selected(
    qtbot: QtBot, viewmodel: TranslationEditorViewModel, mock_settings: MagicMock
):
    """Test update natural with no sentence selected."""
    provider = mock_settings.providers[0]

    with qtbot.waitSignal(viewmodel.error_occurred, timeout=1000) as blocker:
        viewmodel.update_natural_translation("New", provider)

    assert blocker.args
    assert "No sentence selected" in blocker.args[0]


def test_update_alignment_no_sentence_selected(qtbot: QtBot, viewmodel: TranslationEditorViewModel):
    """Test update alignment with no sentence selected."""
    alignments = [WordAlignment(source_word="Test", target_word="Test", position=0)]

    with qtbot.waitSignal(viewmodel.error_occurred, timeout=1000) as blocker:
        viewmodel.update_alignment(alignments)

    assert "No sentence selected" in blocker.args[0]  # type: ignore[reportOptionalSubscript]


def test_cleanup(viewmodel: TranslationEditorViewModel):
    """Test cleanup."""
    viewmodel.cleanup()
    # Should not raise any errors
