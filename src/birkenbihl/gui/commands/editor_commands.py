"""Commands for editor operations."""

from uuid import UUID

from birkenbihl.gui.commands.base import CommandResult
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import WordAlignment
from birkenbihl.services.translation_service import TranslationService


class UpdateNaturalTranslationCommand:
    """Command to update natural translation of a sentence."""

    def __init__(
        self,
        service: TranslationService,
        translation_id: UUID,
        sentence_uuid: UUID,
        new_natural: str,
        provider: ProviderConfig,
    ):
        """Initialize command."""
        self._service = service
        self._translation_id = translation_id
        self._sentence_uuid = sentence_uuid
        self._new_natural = new_natural
        self._provider = provider

    def can_execute(self) -> bool:
        """Check if command can execute."""
        return bool(self._new_natural)

    def execute(self) -> CommandResult:
        """Execute update."""
        if not self.can_execute():
            return CommandResult(success=False, message="Natural translation cannot be empty")

        try:
            translation = self._service.update_sentence_natural(
                self._translation_id,
                self._sentence_uuid,
                self._new_natural,
                self._provider,
            )
            return CommandResult(
                success=True,
                message="Natural translation updated successfully",
                data=translation,
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))


class UpdateAlignmentCommand:
    """Command to update word-by-word alignment."""

    def __init__(
        self,
        service: TranslationService,
        translation_id: UUID,
        sentence_uuid: UUID,
        alignments: list[WordAlignment],
    ):
        """Initialize command."""
        self._service = service
        self._translation_id = translation_id
        self._sentence_uuid = sentence_uuid
        self._alignments = alignments

    def can_execute(self) -> bool:
        """Check if command can execute."""
        return len(self._alignments) > 0

    def execute(self) -> CommandResult:
        """Execute update."""
        if not self.can_execute():
            return CommandResult(success=False, message="Alignments cannot be empty")

        try:
            translation = self._service.update_sentence_alignment(
                self._translation_id,
                self._sentence_uuid,
                self._alignments,
            )
            return CommandResult(
                success=True,
                message="Alignment updated successfully",
                data=translation,
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))
