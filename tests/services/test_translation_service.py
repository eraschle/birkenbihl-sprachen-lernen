"""Unit tests for TranslationService: AI calls (translate, auto-detect, alignment preview) and alignment updates."""

from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from birkenbihl.models import dateutils
from birkenbihl.models.alignment import align_word_pairs
from birkenbihl.models.requests import AlignmentRequest, AlignmentUpdateRequest, AutoDetectRequest, TranslationRequest
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation, WordAlignment
from birkenbihl.protocols import IStorageProvider, ITranslationProvider
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.translation_service import TranslationService


@pytest.fixture
def mock_translator() -> ITranslationProvider:
    """Create mock translation provider."""
    return Mock(spec=ITranslationProvider)


@pytest.fixture
def mock_storage() -> IStorageProvider:
    """Create mock storage provider."""
    return Mock(spec=IStorageProvider)


@pytest.fixture
def translator_factory() -> MagicMock:
    """Factory that builds translators for providers chosen per request."""
    return MagicMock()


@pytest.fixture
def translation_service(
    mock_translator: ITranslationProvider, mock_storage: IStorageProvider, translator_factory: MagicMock
) -> TranslationService:
    """Create TranslationService with mocked dependencies."""
    return TranslationService(mock_translator, mock_storage, translator_factory)


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

    sentence = align_word_pairs(
        "Yo te extrañaré", "Ich werde dich vermissen", [("Yo", "Ich"), ("te", "dich"), ("extrañaré", "werde-vermissen")]
    ).model_copy(update={"uuid": sentence_uuid, "created_at": dateutils.create_now()})

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
class TestAICalls:
    """All AI calls go through the service, with the default translator or one built for a chosen provider."""

    def test_translate_uses_default_translator(
        self, translation_service: TranslationService, mock_translator: Mock, translator_factory: MagicMock
    ) -> None:
        request = TranslationRequest("Hola", get_language_by("es"), get_language_by("de"), "t")

        translation_service.translate(request)

        mock_translator.translate.assert_called_once()  # type: ignore[attr-defined]
        translator_factory.assert_not_called()

    def test_translate_with_chosen_provider(
        self,
        translation_service: TranslationService,
        mock_translator: Mock,
        translator_factory: MagicMock,
        provider_config: ProviderConfig,
    ) -> None:
        request = TranslationRequest("Hola", get_language_by("es"), get_language_by("de"), "t", provider_config)

        result = translation_service.translate(request)

        translator_factory.assert_called_once_with(provider_config)
        assert result is translator_factory.return_value.translate.return_value
        mock_translator.translate.assert_not_called()  # type: ignore[attr-defined]

    def test_translate_without_any_translator_fails(self, mock_storage: IStorageProvider) -> None:
        service = TranslationService(None, mock_storage)
        request = TranslationRequest("Hola", get_language_by("es"), get_language_by("de"))

        with pytest.raises(ValueError, match="No provider given"):
            service.translate(request)

    def test_auto_detect_needs_no_ai_for_detection(
        self, translation_service: TranslationService, mock_translator: Mock
    ) -> None:
        with patch("birkenbihl.services.translation_service.detect_language", return_value=get_language_by("es")):
            translation_service.auto_detect_and_translate(AutoDetectRequest("Hola amigo", get_language_by("de")))

        kwargs = mock_translator.translate.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["source_lang"].code == "es"

    def test_generate_alignment_is_a_preview(
        self,
        translation_service: TranslationService,
        mock_storage: Mock,
        translator_factory: MagicMock,
        provider_config: ProviderConfig,
    ) -> None:
        expected = [WordAlignment(source_index=0, target_indices=[0])]
        translator_factory.return_value.regenerate_alignment.return_value = expected
        request = AlignmentRequest("Hola", "Hallo", get_language_by("es"), get_language_by("de"), provider_config)

        alignments = translation_service.generate_alignment(request)

        assert alignments == expected
        translator_factory.assert_called_once_with(provider_config)
        translator_factory.return_value.regenerate_alignment.assert_called_once_with(
            "Hola", "Hallo", get_language_by("es"), get_language_by("de")
        )
        mock_storage.update.assert_not_called()
        mock_storage.save.assert_not_called()


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
            WordAlignment(source_index=0, target_indices=[0]),  # Yo → Ich
            WordAlignment(source_index=1, target_indices=[2]),  # te → dich
            WordAlignment(source_index=2, target_indices=[1, 3]),  # extrañaré → werde-vermissen
        ]

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]
        mock_storage.update.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act
        request = AlignmentUpdateRequest(
            translation_id=sample_translation.uuid, sentence_uuid=sentence_uuid, alignments=new_alignments
        )
        result = translation_service.update_sentence_alignment(request)

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
        # "te" has no target and "dich" is unused
        invalid_alignments = [
            WordAlignment(source_index=0, target_indices=[0]),
            WordAlignment(source_index=2, target_indices=[1, 3]),
        ]

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act & Assert
        request = AlignmentUpdateRequest(
            translation_id=sample_translation.uuid, sentence_uuid=sentence_uuid, alignments=invalid_alignments
        )
        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(request)

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
            WordAlignment(source_index=0, target_indices=[0]),
            WordAlignment(source_index=1, target_indices=[2]),
            WordAlignment(source_index=2, target_indices=[1]),
        ]

        mock_storage.get.return_value = sample_translation  # type: ignore[reportAttributeAccessIssue]

        # Act & Assert
        request = AlignmentUpdateRequest(
            translation_id=sample_translation.uuid, sentence_uuid=sentence_uuid, alignments=incomplete_alignments
        )
        with pytest.raises(ValueError, match="Invalid alignment"):
            translation_service.update_sentence_alignment(request)


# Local Variables:
# jinx-local-words: "PydanticAITranslator"
# End:
