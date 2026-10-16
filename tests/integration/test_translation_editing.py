"""Integration tests for translation editing workflows.

End-to-end tests covering the full workflow of:
1. Creating translations
2. Editing the natural translation and letting the AI realign it (preview, then save)
3. Manually editing word-by-word alignments
4. Deleting translations

These tests use real storage and provider implementations.
"""

from pathlib import Path

import pytest

from birkenbihl.models.requests import AlignmentRequest, AlignmentUpdateRequest, TranslationRequest
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import AlignmentStatus, Translation, WordAlignment
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.sqlite_storage import SqliteStorageProvider


@pytest.fixture
def storage_provider(tmp_path: Path) -> SqliteStorageProvider:
    """Create temporary SQLite storage for integration tests."""
    db_path = tmp_path / "test_translations.db"
    return SqliteStorageProvider(str(db_path))


@pytest.fixture
def translation_service_with_storage(
    openai_provider_config: ProviderConfig, storage_provider: SqliteStorageProvider
) -> TranslationService:
    """Create TranslationService with real storage and OpenAI provider."""
    translator = PydanticAITranslator(openai_provider_config)
    return TranslationService(translator, storage_provider)


NEW_NATURAL = "Du wirst mir fehlen"


def _realign_and_save(service: TranslationService, translation: Translation, provider: ProviderConfig) -> Translation:
    """What the edit mode does: AI alignment preview for a changed natural translation, then save."""
    sentence = translation.sentences[0]
    request = AlignmentRequest(
        sentence.source_text, NEW_NATURAL, translation.source_language, translation.target_language, provider
    )
    sentence.word_alignments = service.generate_alignment(request)
    sentence.natural_translation = NEW_NATURAL
    return service.save_translation(translation)


@pytest.mark.integration
@pytest.mark.slow
class TestFullWorkflowEditNaturalTranslation:
    """Integration test for editing natural translation workflow."""

    def test_full_workflow_edit_natural_translation(
        self, translation_service_with_storage: TranslationService, openai_provider_config: ProviderConfig
    ) -> None:
        """Create → change natural translation → AI realigns (preview) → save → reload."""
        request = TranslationRequest(
            text="Yo te extrañaré",
            source_lang=get_language_by("es"),
            target_lang=get_language_by("de"),
            title="Test Translation",
        )
        translation = translation_service_with_storage.save_translation(
            translation_service_with_storage.translate(request)
        )

        preview_request = AlignmentRequest(
            "Yo te extrañaré", NEW_NATURAL, get_language_by("es"), get_language_by("de"), openai_provider_config
        )
        preview = translation_service_with_storage.generate_alignment(preview_request)

        stored = translation_service_with_storage.get_translation(translation.uuid)
        assert stored is not None
        assert stored.sentences[0].natural_translation != NEW_NATURAL, "A preview must not be saved"

        _realign_and_save(translation_service_with_storage, translation, openai_provider_config)

        from birkenbihl.models.validation import validate_alignment_complete

        reloaded = translation_service_with_storage.get_translation(translation.uuid)
        assert reloaded is not None
        assert reloaded.sentences[0].natural_translation == NEW_NATURAL
        assert [a.source_index for a in preview] == [0, 1, 2]
        is_valid, error = validate_alignment_complete(reloaded.sentences[0])
        assert is_valid or reloaded.sentences[0].needs_review(), f"Invalid alignment not flagged: {error}"


@pytest.mark.integration
@pytest.mark.slow
class TestFullWorkflowEditAlignmentManually:
    """Integration test for manually editing word-by-word alignment workflow."""

    def test_full_workflow_edit_alignment_manually(self, translation_service_with_storage: TranslationService) -> None:
        """Test complete workflow: create → create manual alignments → validate → update → verify saved.

        Workflow:
        1. Create a translation
        2. Manually create new word-by-word alignments
        3. Validate alignments
        4. Update sentence with new alignments
        5. Verify changes were saved to storage
        """
        # Step 1: Create translation
        original_text = "Hello world"
        request = TranslationRequest(
            text=original_text,
            source_lang=get_language_by("en"),
            target_lang=get_language_by("de"),
            title="Manual Edit Test",
        )
        translation = translation_service_with_storage.translate(request)

        assert translation is not None
        assert len(translation.sentences) == 1
        original_sentence = translation.sentences[0]
        natural_translation = original_sentence.natural_translation  # e.g., "Hallo Welt"

        # Step 2: Manually create new alignments: "Hello" gets every word except the last, "world" the last
        target_count = len(original_sentence.target_tokens)
        assert target_count >= 2, f"Expected at least two words in {natural_translation!r}"
        new_alignments = [
            WordAlignment(
                source_index=0, target_indices=list(range(target_count - 1)), status=AlignmentStatus.CONFIRMED
            ),
            WordAlignment(source_index=1, target_indices=[target_count - 1], status=AlignmentStatus.CONFIRMED),
        ]

        # Step 3: Validate alignments
        from birkenbihl.models.validation import validate_alignment_complete

        is_valid, error = validate_alignment_complete(
            original_sentence.model_copy(update={"word_alignments": new_alignments})
        )
        assert is_valid, f"Manual alignments are invalid: {error}"

        # Step 4: Update sentence with new alignments
        alignment_request = AlignmentUpdateRequest(
            translation_id=translation.uuid, sentence_uuid=original_sentence.uuid, alignments=new_alignments
        )
        updated_translation = translation_service_with_storage.update_sentence_alignment(alignment_request)

        # Verify update succeeded
        updated_sentence = updated_translation.sentences[0]
        assert updated_sentence.word_alignments == new_alignments
        assert updated_translation.updated_at > translation.updated_at

        # Step 5: Verify changes were saved to storage
        retrieved_translation = translation_service_with_storage.get_translation(translation.uuid)
        assert retrieved_translation is not None
        assert retrieved_translation.sentences[0].word_alignments == new_alignments


@pytest.mark.integration
@pytest.mark.slow
class TestDeleteTranslation:
    """Integration test for translation deletion workflow."""

    def test_delete_translation(self, translation_service_with_storage: TranslationService) -> None:
        """Test complete workflow: create → delete → verify not in storage.

        Workflow:
        1. Create a translation
        2. Delete translation via service
        3. Verify translation no longer in storage
        """
        # Step 1: Create translation
        original_text = "Test deletion"
        request = TranslationRequest(
            text=original_text,
            source_lang=get_language_by("en"),
            target_lang=get_language_by("de"),
            title="To Be Deleted",
        )
        translation = translation_service_with_storage.translate(request)

        assert translation is not None
        translation_id = translation.uuid

        # Verify translation exists in storage
        retrieved = translation_service_with_storage.get_translation(translation_id)
        assert retrieved is not None

        # Step 2: Delete translation
        deleted = translation_service_with_storage.delete_translation(translation_id)
        assert deleted is True

        # Step 3: Verify not in storage
        retrieved_after_delete = translation_service_with_storage.get_translation(translation_id)
        assert retrieved_after_delete is None

        # Verify it's not in list_all either
        all_translations = translation_service_with_storage.list_all_translations()
        assert translation_id not in [t.uuid for t in all_translations]


@pytest.mark.integration
@pytest.mark.slow
class TestMultipleEditsWorkflow:
    """Integration test for multiple sequential edits."""

    def test_multiple_edits_preserve_data_integrity(
        self, translation_service_with_storage: TranslationService, openai_provider_config: ProviderConfig
    ) -> None:
        """Test that multiple sequential edits maintain data integrity.

        Workflow:
        1. Create translation
        2. Edit natural translation
        3. Edit alignment manually
        4. Verify all changes persisted correctly
        """
        # Step 1: Create translation
        original_text = "Yo te extrañaré"
        request = TranslationRequest(
            text=original_text,
            source_lang=get_language_by("es"),
            target_lang=get_language_by("de"),
            title="Multiple Edits Test",
        )
        translation = translation_service_with_storage.translate(request)

        sentence_uuid = translation.sentences[0].uuid
        original_updated_at = translation.updated_at

        # Step 2: Edit natural translation and let the AI realign it
        translation = _realign_and_save(translation_service_with_storage, translation, openai_provider_config)
        new_natural = NEW_NATURAL

        assert translation.sentences[0].natural_translation == new_natural
        assert translation.updated_at >= original_updated_at
        after_natural_update = translation.updated_at

        # Step 3: Edit alignment manually (add extra mapping)
        current_alignments = translation.sentences[0].word_alignments
        # Just verify we can update with current alignments (no-op change)
        alignment_request = AlignmentUpdateRequest(
            translation_id=translation.uuid, sentence_uuid=sentence_uuid, alignments=current_alignments
        )
        translation = translation_service_with_storage.update_sentence_alignment(alignment_request)

        assert translation.updated_at >= after_natural_update

        # Step 4: Verify final state
        final_translation = translation_service_with_storage.get_translation(translation.uuid)
        assert final_translation is not None
        assert final_translation.sentences[0].natural_translation == new_natural
        assert final_translation.sentences[0].word_alignments == current_alignments
