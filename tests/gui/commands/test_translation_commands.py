"""Tests for translation commands."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from birkenbihl.gui.commands.translation_commands import (
    AutoDetectTranslationCommand,
    CreateTranslationCommand,
)
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation, WordAlignment


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
    service.auto_detect_and_translate.return_value = translation
    return service


def test_create_translation_can_execute_success(mock_service):
    """Test can execute with valid data."""
    cmd = CreateTranslationCommand(
        service=mock_service,
        text="Hello World",
        source_lang="en",
        target_lang="de",
        title="Test",
    )
    assert cmd.can_execute()


def test_create_translation_can_execute_missing_text(mock_service):
    """Test can execute with missing text."""
    cmd = CreateTranslationCommand(
        service=mock_service,
        text="",
        source_lang="en",
        target_lang="de",
        title="Test",
    )
    assert not cmd.can_execute()


def test_create_translation_can_execute_missing_lang(mock_service):
    """Test can execute with missing language."""
    cmd = CreateTranslationCommand(
        service=mock_service,
        text="Hello",
        source_lang="",
        target_lang="de",
        title="Test",
    )
    assert not cmd.can_execute()


def test_create_translation_can_execute_missing_title(mock_service):
    """Test can execute with missing title."""
    cmd = CreateTranslationCommand(
        service=mock_service,
        text="Hello",
        source_lang="en",
        target_lang="de",
        title="",
    )
    assert not cmd.can_execute()


def test_create_translation_execute_success(mock_service):
    """Test successful translation creation."""
    cmd = CreateTranslationCommand(
        service=mock_service,
        text="Hello World",
        source_lang="en",
        target_lang="de",
        title="Test",
    )
    result = cmd.execute()

    assert result.success
    assert result.data is not None
    assert isinstance(result.data, Translation)
    mock_service.translate_and_save.assert_called_once()


def test_create_translation_execute_cannot_execute(mock_service):
    """Test execute when cannot execute."""
    cmd = CreateTranslationCommand(
        service=mock_service,
        text="",
        source_lang="en",
        target_lang="de",
        title="Test",
    )
    result = cmd.execute()

    assert not result.success
    assert "required" in result.message.lower()
    mock_service.translate_and_save.assert_not_called()


def test_create_translation_execute_service_error(mock_service):
    """Test execute with service error."""
    mock_service.translate_and_save.side_effect = Exception("Service error")

    cmd = CreateTranslationCommand(
        service=mock_service,
        text="Hello",
        source_lang="en",
        target_lang="de",
        title="Test",
    )
    result = cmd.execute()

    assert not result.success
    assert "Service error" in result.message


def test_auto_detect_can_execute_success(mock_service):
    """Test auto detect can execute with valid data."""
    cmd = AutoDetectTranslationCommand(
        service=mock_service,
        text="Hello World",
        target_lang="de",
        title="Test",
    )
    assert cmd.can_execute()


def test_auto_detect_can_execute_missing_text(mock_service):
    """Test auto detect can execute with missing text."""
    cmd = AutoDetectTranslationCommand(
        service=mock_service,
        text="",
        target_lang="de",
        title="Test",
    )
    assert not cmd.can_execute()


def test_auto_detect_execute_success(mock_service):
    """Test auto detect execute success."""
    cmd = AutoDetectTranslationCommand(
        service=mock_service,
        text="Hello World",
        target_lang="de",
        title="Test",
    )
    result = cmd.execute()

    assert result.success
    assert result.data is not None
    assert isinstance(result.data, Translation)
    mock_service.auto_detect_and_translate.assert_called_once()


def test_auto_detect_execute_cannot_execute(mock_service):
    """Test auto detect execute when cannot execute."""
    cmd = AutoDetectTranslationCommand(
        service=mock_service,
        text="",
        target_lang="de",
        title="Test",
    )
    result = cmd.execute()

    assert not result.success
    mock_service.auto_detect_and_translate.assert_not_called()


def test_auto_detect_execute_service_error(mock_service):
    """Test auto detect execute with service error."""
    mock_service.auto_detect_and_translate.side_effect = Exception("Detection failed")

    cmd = AutoDetectTranslationCommand(
        service=mock_service,
        text="Hello",
        target_lang="de",
        title="Test",
    )
    result = cmd.execute()

    assert not result.success
    assert "Detection failed" in result.message
