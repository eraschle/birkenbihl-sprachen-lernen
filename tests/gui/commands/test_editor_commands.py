"""Tests for editor commands."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from birkenbihl.gui.commands.editor_commands import (
    UpdateAlignmentCommand,
    UpdateNaturalTranslationCommand,
)
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
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
def mock_service(translation):
    """Create mock TranslationService."""
    service = Mock()
    service.update_sentence_natural.return_value = translation
    service.update_sentence_alignment.return_value = translation
    return service


@pytest.fixture
def provider():
    """Create test provider."""
    return ProviderConfig(
        name="Test",
        provider_type="openai",
        model="gpt-4",
        api_key="test-key",
    )


def test_update_natural_can_execute_success(mock_service, translation, provider):
    """Test can execute with valid data."""
    cmd = UpdateNaturalTranslationCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        new_natural="New translation",
        provider=provider,
    )
    assert cmd.can_execute()


def test_update_natural_can_execute_empty_text(mock_service, translation, provider):
    """Test can execute with empty text."""
    cmd = UpdateNaturalTranslationCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        new_natural="",
        provider=provider,
    )
    assert not cmd.can_execute()


def test_update_natural_execute_success(mock_service, translation, provider):
    """Test successful natural translation update."""
    cmd = UpdateNaturalTranslationCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        new_natural="New translation",
        provider=provider,
    )
    result = cmd.execute()

    assert result.success
    assert result.data is not None
    mock_service.update_sentence_natural.assert_called_once()


def test_update_natural_execute_cannot_execute(mock_service, translation, provider):
    """Test execute when cannot execute."""
    cmd = UpdateNaturalTranslationCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        new_natural="",
        provider=provider,
    )
    result = cmd.execute()

    assert not result.success
    mock_service.update_sentence_natural.assert_not_called()


def test_update_natural_execute_service_error(mock_service, translation, provider):
    """Test execute with service error."""
    mock_service.update_sentence_natural.side_effect = Exception("Update failed")

    cmd = UpdateNaturalTranslationCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        new_natural="New",
        provider=provider,
    )
    result = cmd.execute()

    assert not result.success
    assert "Update failed" in result.message


def test_update_alignment_can_execute_success(mock_service, translation):
    """Test can execute with valid alignments."""
    alignments = [WordAlignment(source_word="Hello", target_word="Hi", position=0)]
    cmd = UpdateAlignmentCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        alignments=alignments,
    )
    assert cmd.can_execute()


def test_update_alignment_can_execute_empty(mock_service, translation):
    """Test can execute with empty alignments."""
    cmd = UpdateAlignmentCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        alignments=[],
    )
    assert not cmd.can_execute()


def test_update_alignment_execute_success(mock_service, translation):
    """Test successful alignment update."""
    alignments = [WordAlignment(source_word="Hello", target_word="Hi", position=0)]
    cmd = UpdateAlignmentCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        alignments=alignments,
    )
    result = cmd.execute()

    assert result.success
    assert result.data is not None
    mock_service.update_sentence_alignment.assert_called_once()


def test_update_alignment_execute_cannot_execute(mock_service, translation):
    """Test execute when cannot execute."""
    cmd = UpdateAlignmentCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        alignments=[],
    )
    result = cmd.execute()

    assert not result.success
    mock_service.update_sentence_alignment.assert_not_called()


def test_update_alignment_execute_service_error(mock_service, translation):
    """Test execute with service error."""
    mock_service.update_sentence_alignment.side_effect = Exception("Alignment failed")
    alignments = [WordAlignment(source_word="Hello", target_word="Hi", position=0)]

    cmd = UpdateAlignmentCommand(
        service=mock_service,
        translation_id=translation.uuid,
        sentence_uuid=translation.sentences[0].uuid,
        alignments=alignments,
    )
    result = cmd.execute()

    assert not result.success
    assert "Alignment failed" in result.message
