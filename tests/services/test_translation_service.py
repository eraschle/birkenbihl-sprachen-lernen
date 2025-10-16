"""Unit tests for TranslationService editing features.

Tests cover the new editing workflows introduced in Phase 1:
- get_sentence_suggestions
- update_sentence_natural
- update_sentence_alignment
"""

from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest

from birkenbihl.models import dateutils
from birkenbihl.models.requests import SentenceUpdateRequest
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.protocols import IStorageProvider, ITranslationProvider
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.exceptions import NotFoundError


@pytest.fixture
def mock_translator() -> ITranslationProvider:
    """Create mock translation provider."""
    return Mock(spec=ITranslationProvider)


@pytest.fixture
def mock_storage() -> IStorageProvider:
    """Create mock storage provider."""
    return Mock(spec=IStorageProvider)


@pytest.fixture
def translation_service(mock_translator: ITranslationProvider, mock_storage: IStorageProvider) -> TranslationService:
    """Create TranslationService with mocked dependencies."""
    return TranslationService(mock_translator, mock_storage)


@pytest.fixture
def provider_config() -> ProviderConfig:
    """Create test provider configuration."""
    return ProviderConfig(
        name="Test Provider",
        provider_type="openai",
        model="gpt-4o",
        api_key="sk-test-key",
        is_default=True,
    )


@pytest.fixture
def sample_translation() -> Translation:
    """Create sample translation for testing."""
    sentence_uuid = uuid4()
    translation_id = uuid4()

    sentence = Sentence(
        uuid=sentence_uuid,
        source_text="Yo te extrañaré",
        natural_translation="Ich werde dich vermissen",
        word_alignments=[
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
        ],
        created_at=dateutils.create_now(),
    )

    return Translation(
        uuid=translation_id,
        title="Test Translation",
        source_language=get_language_by("es"),
        target_language=get_language_by("de"),
        sentences=[sentence],
        created_at=dateutils.create_now(),
        updated_at=dateutils.create_now(),
    )


@pytest.mark.unit
class TestGetSentenceSuggestions:
    """Tests for get_sentence_suggestions method."""

    def test_get_sentence_suggestions_success(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        provider_config: ProviderConfig,
        sample_translation: Translation,
    ) -> None:
        """Test successful generation of alternative translations."""
        # Arrange
        sentence_uuid = sample_translation.sentences[0].uuid
        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        expected_alternatives = [
            "Ich werde dich vermissen",
            "Du wirst mir fehlen",
            "Ich vermisse dich",
        ]

        # Mock PydanticAITranslator.generate_alternatives
        with MagicMock() as mock_pydantic:
            mock_pydantic.return_value.generate_alternatives.return_value = expected_alternatives

            # We need to patch the actual import
            from unittest.mock import patch

            with patch("birkenbihl.services.translation_service.PydanticAITranslator") as mock_translator_class:
                mock_translator_class.return_value.generate_alternatives.return_value = expected_alternatives

                # Act
                alternatives = translation_service.get_sentence_suggestions(
                    sample_translation.uuid, sentence_uuid, provider_config, count=3
                )

                # Assert
                assert alternatives == expected_alternatives
                mock_storage.get.assert_called_once_with(sample_translation.uuid)  # type: ignore[reportAttributeAccessIssue]
                mock_translator_class.assert_called_once_with(provider_config)

    def test_get_sentence_suggestions_translation_not_found(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        provider_config: ProviderConfig,
    ) -> None:
        """Test error when translation not found."""
        # Arrange
        translation_id = uuid4()
        sentence_uuid = uuid4()
        mock_storage.get.return_value = None  # type: ignore[reportAttributeAccessIssue]

        # Act & Assert
        with pytest.raises(NotFoundError, match=f"Translation {translation_id} not found"):
            translation_service.get_sentence_suggestions(translation_id, sentence_uuid, provider_config)

    def test_get_sentence_suggestions_sentence_not_found(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        provider_config: ProviderConfig,
        sample_translation: Translation,
    ) -> None:
        """Test error when sentence not found in translation."""
        # Arrange
        wrong_sentence_uuid = uuid4()
        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act & Assert
        with pytest.raises(
            NotFoundError,
            match=f"Sentence {wrong_sentence_uuid} not found in translation {sample_translation.uuid}",
        ):
            translation_service.get_sentence_suggestions(sample_translation.uuid, wrong_sentence_uuid, provider_config)


@pytest.mark.unit
class TestUpdateSentenceNatural:
    """Tests for update_sentence_natural method."""

    def test_update_sentence_natural_success(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        provider_config: ProviderConfig,
        sample_translation: Translation,
    ) -> None:
        """Test successful update of natural translation and alignment regeneration."""
        # Arrange
        new_natural = "Du wirst mir fehlen"
        new_alignments = [
            WordAlignment(source_word="Yo", target_word="Du", position=0),
            WordAlignment(source_word="te", target_word="mir", position=1),
            WordAlignment(source_word="extrañaré", target_word="wirst-fehlen", position=2),
        ]

        request = SentenceUpdateRequest(
            translation_id=sample_translation.uuid,
            sentence_idx=0,
            new_text=new_natural,
            provider=provider_config,
        )

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]
        mock_storage.update.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        from unittest.mock import patch

        with patch("birkenbihl.services.translation_service.PydanticAITranslator") as mock_translator_class:
            mock_translator_class.return_value.regenerate_alignment.return_value = new_alignments

            # Act
            result = translation_service.update_sentence_natural(request)

            # Assert
            assert result.sentences[0].natural_translation == new_natural
            assert result.sentences[0].word_alignments == new_alignments
            mock_storage.update.assert_called_once()  # type: ignore[reportAttributeAccessIssue]
            mock_translator_class.return_value.regenerate_alignment.assert_called_once()

    def test_update_sentence_natural_regenerates_alignment(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        provider_config: ProviderConfig,
        sample_translation: Translation,
    ) -> None:
        """Test that update_sentence_natural calls regenerate_alignment."""
        # Arrange
        new_natural = "Neuer Text"
        request = SentenceUpdateRequest(
            translation_id=sample_translation.uuid,
            sentence_idx=0,
            new_text=new_natural,
            provider=provider_config,
        )

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]
        mock_storage.update.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        from unittest.mock import patch

        with patch("birkenbihl.services.translation_service.PydanticAITranslator") as mock_translator_class:
            mock_translator_class.return_value.regenerate_alignment.return_value = []

            # Act
            translation_service.update_sentence_natural(request)

            # Assert
            mock_translator_class.return_value.regenerate_alignment.assert_called_once_with(
                sample_translation.sentences[0].source_text,
                new_natural,
                sample_translation.source_language,
                sample_translation.target_language,
            )

    def test_update_sentence_natural_updates_timestamp(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        provider_config: ProviderConfig,
        sample_translation: Translation,
    ) -> None:
        """Test that update_sentence_natural updates updated_at timestamp."""
        # Arrange
        new_natural = "Neuer Text"
        old_updated_at = sample_translation.updated_at

        request = SentenceUpdateRequest(
            translation_id=sample_translation.uuid,
            sentence_idx=0,
            new_text=new_natural,
            provider=provider_config,
        )

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]
        mock_storage.update.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        from unittest.mock import patch

        with patch("birkenbihl.services.translation_service.PydanticAITranslator") as mock_translator_class:
            mock_translator_class.return_value.regenerate_alignment.return_value = []

            # Act
            result = translation_service.update_sentence_natural(request)

            # Assert
            assert result.updated_at > old_updated_at or result.updated_at != old_updated_at


@pytest.mark.unit
class TestUpdateSentenceAlignment:
    """Tests for update_sentence_alignment method."""

    def test_update_sentence_alignment_valid(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        sample_translation: Translation,
    ) -> None:
        """Test successful update of word-by-word alignment."""
        # Arrange
        sentence_uuid = sample_translation.sentences[0].uuid
        new_alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde", position=2),
            WordAlignment(source_word="extrañaré", target_word="vermissen", position=3),
        ]

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]
        mock_storage.update.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act
        result = translation_service.update_sentence_alignment(sample_translation.uuid, sentence_uuid, new_alignments)

        # Assert
        assert result.sentences[0].word_alignments == new_alignments
        mock_storage.update.assert_called_once()  # type: ignore[reportAttributeAccessIssue]

    def test_update_sentence_alignment_invalid_fails(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        sample_translation: Translation,
    ) -> None:
        """Test that invalid alignment raises ValueError."""
        # Arrange
        sentence_uuid = sample_translation.sentences[0].uuid
        # Missing "dich" from natural translation
        invalid_alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=1),
        ]

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(sample_translation.uuid, sentence_uuid, invalid_alignments)

    def test_update_sentence_alignment_missing_words_fails(
        self,
        translation_service: TranslationService,
        mock_storage: IStorageProvider,
        sample_translation: Translation,
    ) -> None:
        """Test that alignments with missing words raise ValueError."""
        # Arrange
        sentence_uuid = sample_translation.sentences[0].uuid
        # Missing "vermissen" from natural translation
        incomplete_alignments = [
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde", position=2),
        ]

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(sample_translation.uuid, sentence_uuid, incomplete_alignments)
