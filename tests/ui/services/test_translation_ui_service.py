"""Tests for TranslationUIService."""

from datetime import UTC
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.services import language_service as ls
from birkenbihl.ui.services.translation_ui_service import TranslationUIServiceImpl


@pytest.fixture(autouse=True)
def reset_service():
    """Reset service instances before and after each test."""
    TranslationUIServiceImpl.reset()
    yield
    TranslationUIServiceImpl.reset()


@pytest.fixture
def sample_translation() -> Translation:
    """Create a sample translation for testing."""
    sentence = Sentence(source_text="Hello", natural_translation="Hallo", word_alignments=[])
    return Translation(
        title="Test Translation",
        source_language=ls.get_language_by(name_or_code="es"),
        target_language=ls.get_language_by(name_or_code="de"),
        sentences=[sentence],
    )


class TestTranslationUIServiceImpl:
    """Tests for TranslationUIServiceImpl."""

    def test_storage_method_initializes_lazily(self):
        """Test that get_storage initializes on first access."""
        # Initially None
        assert TranslationUIServiceImpl._storage is None

        # Access method
        storage = TranslationUIServiceImpl.get_storage()

        # Should be initialized
        assert storage is not None
        assert TranslationUIServiceImpl._storage is not None

    def test_service_method_initializes_lazily(self):
        """Test that get_service initializes on first access."""
        # Initially None
        assert TranslationUIServiceImpl._service is None

        # Access method
        service = TranslationUIServiceImpl.get_service()

        # Should be initialized
        assert service is not None
        assert TranslationUIServiceImpl._service is not None

    def test_service_is_initialized_with_storage(self):
        """Test that service is initialized properly."""
        storage = TranslationUIServiceImpl.get_storage()
        service = TranslationUIServiceImpl.get_service()

        # Both should be initialized
        assert storage is not None
        assert service is not None

    def test_multiple_access_returns_same_instance(self):
        """Test that multiple accesses return the same instances (singleton)."""
        storage1 = TranslationUIServiceImpl.get_storage()
        storage2 = TranslationUIServiceImpl.get_storage()

        assert storage1 is storage2

        service1 = TranslationUIServiceImpl.get_service()
        service2 = TranslationUIServiceImpl.get_service()

        assert service1 is service2

    def test_reset_clears_instances(self):
        """Test that reset clears service instances."""
        # Initialize
        _ = TranslationUIServiceImpl.get_storage()
        _ = TranslationUIServiceImpl.get_service()

        assert TranslationUIServiceImpl._storage is not None
        assert TranslationUIServiceImpl._service is not None

        # Reset
        TranslationUIServiceImpl.reset()

        # Should be cleared
        assert TranslationUIServiceImpl._storage is None
        assert TranslationUIServiceImpl._service is None

    @patch("birkenbihl.ui.services.translation_ui_service.TranslationService")
    @patch("birkenbihl.ui.services.translation_ui_service.JsonStorageProvider")
    def test_get_translation_calls_service(
        self, mock_storage_cls: MagicMock, mock_service_cls: MagicMock, sample_translation: Translation
    ):
        """Test that get_translation delegates to service."""
        # Setup mocks
        mock_storage = Mock()
        mock_service = Mock()
        mock_storage_cls.return_value = mock_storage
        mock_service_cls.return_value = mock_service
        mock_service.get_translation.return_value = sample_translation

        # Reset to use mocks
        TranslationUIServiceImpl.reset()

        # Call get_translation
        translation_id = uuid4()
        result = TranslationUIServiceImpl.get_translation(translation_id)

        # Should call service.get_translation
        mock_service.get_translation.assert_called_once_with(translation_id)
        assert result == sample_translation

    @patch("birkenbihl.ui.services.translation_ui_service.TranslationService")
    @patch("birkenbihl.ui.services.translation_ui_service.JsonStorageProvider")
    def test_get_translation_returns_none_for_nonexistent(
        self, mock_storage_cls: MagicMock, mock_service_cls: MagicMock
    ):
        """Test that get_translation returns None for nonexistent translation."""
        # Setup mocks
        mock_storage = Mock()
        mock_service = Mock()
        mock_storage_cls.return_value = mock_storage
        mock_service_cls.return_value = mock_service
        mock_service.get_translation.return_value = None

        # Reset to use mocks
        TranslationUIServiceImpl.reset()

        # Call get_translation
        translation_id = uuid4()
        result = TranslationUIServiceImpl.get_translation(translation_id)

        # Should return None
        assert result is None

    @patch("birkenbihl.ui.services.translation_ui_service.TranslationService")
    @patch("birkenbihl.ui.services.translation_ui_service.JsonStorageProvider")
    def test_get_translation_raises_on_error(self, mock_storage_cls: MagicMock, mock_service_cls: MagicMock):
        """Test that get_translation raises exception on error."""
        # Setup mocks
        mock_storage = Mock()
        mock_service = Mock()
        mock_storage_cls.return_value = mock_storage
        mock_service_cls.return_value = mock_service
        mock_service.get_translation.side_effect = Exception("Test error")

        # Reset to use mocks
        TranslationUIServiceImpl.reset()

        # Call should raise
        with pytest.raises(Exception, match="Test error"):
            TranslationUIServiceImpl.get_translation(uuid4())

    @patch("birkenbihl.ui.services.translation_ui_service.TranslationService")
    @patch("birkenbihl.ui.services.translation_ui_service.JsonStorageProvider")
    def test_list_translations_sorts_by_date(self, mock_storage_cls: MagicMock, mock_service_cls: MagicMock):
        """Test that list_translations sorts by updated_at descending."""
        from datetime import datetime, timedelta

        # Create translations with different dates
        now = datetime.now(UTC)

        # Create mock translations with proper updated_at attribute
        trans1 = Mock(spec=Translation)
        trans1.title = "Old"
        trans1.updated_at = now - timedelta(days=2)

        trans2 = Mock(spec=Translation)
        trans2.title = "Recent"
        trans2.updated_at = now - timedelta(hours=1)

        trans3 = Mock(spec=Translation)
        trans3.title = "Oldest"
        trans3.updated_at = now - timedelta(days=5)

        # Setup mocks
        mock_storage = Mock()
        mock_service = Mock()
        mock_storage_cls.return_value = mock_storage
        mock_service_cls.return_value = mock_service
        # Return in unsorted order
        mock_service.list_all_translations.return_value = [trans1, trans2, trans3]

        # Reset to use mocks
        TranslationUIServiceImpl.reset()

        # Call list_translations
        result = TranslationUIServiceImpl.list_translations()

        # Should be sorted by most recent first
        assert len(result) == 3
        assert result[0].title == "Recent"
        assert result[1].title == "Old"
        assert result[2].title == "Oldest"

    @patch("birkenbihl.ui.services.translation_ui_service.TranslationService")
    @patch("birkenbihl.ui.services.translation_ui_service.JsonStorageProvider")
    def test_list_translations_raises_on_error(self, mock_storage_cls: MagicMock, mock_service_cls: MagicMock):
        """Test that list_translations raises exception on error."""
        # Setup mocks
        mock_storage = Mock()
        mock_service = Mock()
        mock_storage_cls.return_value = mock_storage
        mock_service_cls.return_value = mock_service
        mock_service.list_all_translations.side_effect = Exception("Test error")

        # Reset to use mocks
        TranslationUIServiceImpl.reset()

        # Call should raise
        with pytest.raises(Exception, match="Test error"):
            TranslationUIServiceImpl.list_translations()
