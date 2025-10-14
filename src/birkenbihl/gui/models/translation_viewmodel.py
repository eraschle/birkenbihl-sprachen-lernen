"""ViewModel for translation creation."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from birkenbihl.gui.models.ui_state import TranslationCreationState
from birkenbihl.gui.utils.async_helper import AsyncWorker
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.services import language_service as ls
from birkenbihl.services.translation_service import TranslationService


class TranslationCreationViewModel(QObject):
    """ViewModel for translation creation workflow.

    Manages state for creating new translations.
    Coordinates TranslationService for AI translation.
    Emits signals for state changes and completion.
    """

    state_changed = Signal(object)  # TranslationCreationState
    translation_started = Signal()
    translation_completed = Signal(object)  # Translation
    translation_failed = Signal(str)  # error message
    translation_progress = Signal(float, str)  # progress, message

    def __init__(self, service: TranslationService, parent: QWidget | None = None):
        """Initialize ViewModel.

        Args:
            service: TranslationService instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = service
        self._state = TranslationCreationState()
        self._worker: AsyncWorker | None = None

    def initialize(self) -> None:
        """Initialize ViewModel."""
        self._emit_state()

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._worker:
            self._worker.stop()
            self._worker.wait()

    def reset(self) -> None:
        """Reset state to initial values."""
        self._state = TranslationCreationState()
        self._emit_state()

    @property
    def state(self) -> TranslationCreationState:
        """Get current state."""
        return self._state

    def set_title(self, title: str) -> None:
        """Set translation title.

        Args:
            title: Title text
        """
        self._state.title = title
        self._emit_state()

    def set_source_text(self, text: str) -> None:
        """Set source text.

        Args:
            text: Source text
        """
        self._state.source_text = text
        self._emit_state()

    def set_source_language(self, lang: str | None) -> None:
        """Set source language.

        Args:
            lang: Language code or None for auto-detect
        """
        if lang is None:
            language = ls.get_default_source_language()
        else:
            language = ls.get_language_by(lang)

        self._state.source_language = language
        self._emit_state()

    def set_target_language(self, lang: str) -> None:
        """Set target language.

        Args:
            lang: Language code
        """
        self._state.target_language = ls.get_language_by(lang)
        self._emit_state()

    def set_provider(self, provider: ProviderConfig) -> None:
        """Set selected provider.

        Args:
            provider: Provider config
        """
        self._state.selected_provider = provider
        self._emit_state()

    def start_translation(self) -> None:
        """Start translation in background."""
        if not self.can_translate():
            return

        self._state.is_translating = True
        self._state.progress = 0.0
        self._emit_state()
        self.translation_started.emit()

        self._worker = AsyncWorker(self._execute_translation)
        self._worker.task_completed.connect(self._on_translation_completed)
        self._worker.task_failed.connect(self._on_translation_failed)
        self._worker.start()

    def cancel_translation(self) -> None:
        """Cancel ongoing translation."""
        if self._worker:
            self._worker.stop()
            self._state.is_translating = False
            self._state.progress = 0.0
            self._emit_state()

    def can_translate(self) -> bool:
        """Check if translation can be started.

        Returns:
            True if ready to translate
        """
        return (
            bool(self._state.title)
            and bool(self._state.source_text)
            and bool(self._state.target_language)
            and self._state.selected_provider is not None
            and not self._state.is_translating
        )

    def _execute_translation(self) -> Translation:
        """Execute translation (runs in background thread).

        Returns:
            Translation result
        """
        from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator

        source_lang = self._state.source_language
        target_lang = self._state.target_language
        text = self._state.source_text
        title = self._state.title
        provider = self._state.selected_provider

        if not provider:
            raise ValueError("No provider selected")

        translator = PydanticAITranslator(provider)
        temp_service = TranslationService(translator, self._service._storage)

        if ls.is_auto_detect(source_lang.code):
            return temp_service.auto_detect_and_translate(text, target_lang, title)
        else:
            return temp_service.translate_and_save(text, source_lang, target_lang, title)

    def _on_translation_completed(self, translation: Translation) -> None:
        """Handle translation completion.

        Args:
            translation: Completed translation
        """
        self._state.is_translating = False
        self._state.progress = 1.0
        self._emit_state()
        self.translation_completed.emit(translation)

    def _on_translation_failed(self, error: str) -> None:
        """Handle translation failure.

        Args:
            error: Error message
        """
        self._state.is_translating = False
        self._state.progress = 0.0
        self._emit_state()
        self.translation_failed.emit(error)

    def _emit_state(self) -> None:
        """Emit state changed signal."""
        self.state_changed.emit(self._state)
