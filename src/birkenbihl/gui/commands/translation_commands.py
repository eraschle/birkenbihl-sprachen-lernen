"""Commands for translation operations."""

from birkenbihl.gui.commands.base import Command, CommandResult
from birkenbihl.models.translation import Translation
from birkenbihl.services.translation_service import TranslationService


class CreateTranslationCommand:
    """Command to create a new translation.

    Validates input and executes translation via service.
    """

    def __init__(
        self,
        service: TranslationService,
        text: str,
        source_lang: str,
        target_lang: str,
        title: str,
    ):
        """Initialize command.

        Args:
            service: TranslationService instance
            text: Source text to translate
            source_lang: Source language code
            target_lang: Target language code
            title: Translation title
        """
        self._service = service
        self._text = text
        self._source_lang = source_lang
        self._target_lang = target_lang
        self._title = title

    def can_execute(self) -> bool:
        """Check if command can execute.

        Returns:
            True if all required fields are present
        """
        return (
            bool(self._text)
            and bool(self._source_lang)
            and bool(self._target_lang)
            and bool(self._title)
        )

    def execute(self) -> CommandResult:
        """Execute translation creation.

        Returns:
            CommandResult with created Translation
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                message="Missing required fields",
            )

        try:
            translation = self._service.translate_and_save(
                self._text,
                self._source_lang,
                self._target_lang,
                self._title,
            )
            return CommandResult(
                success=True,
                message=f"Translation '{self._title}' created successfully",
                data=translation,
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Translation failed: {str(e)}",
            )


class AutoDetectTranslationCommand:
    """Command to create translation with auto-detected source language."""

    def __init__(
        self,
        service: TranslationService,
        text: str,
        target_lang: str,
        title: str,
    ):
        """Initialize command.

        Args:
            service: TranslationService instance
            text: Source text to translate
            target_lang: Target language code
            title: Translation title
        """
        self._service = service
        self._text = text
        self._target_lang = target_lang
        self._title = title

    def can_execute(self) -> bool:
        """Check if command can execute.

        Returns:
            True if all required fields are present
        """
        return bool(self._text) and bool(self._target_lang) and bool(self._title)

    def execute(self) -> CommandResult:
        """Execute translation with auto-detection.

        Returns:
            CommandResult with created Translation
        """
        if not self.can_execute():
            return CommandResult(
                success=False,
                message="Missing required fields",
            )

        try:
            translation = self._service.auto_detect_and_translate(
                self._text,
                self._target_lang,
                self._title,
            )
            return CommandResult(
                success=True,
                message=f"Translation '{self._title}' created successfully",
                data=translation,
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Translation failed: {str(e)}",
            )
