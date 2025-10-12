"""CreateTranslationViewModel for managing translation creation in MVVM pattern."""

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from birkenbihl.gui.services.translation_ui_service import TranslationUIService
from birkenbihl.gui.viewmodels.base import BaseViewModel
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.services.settings_service import SettingsService


class TranslationWorker(QRunnable):
    """Worker thread for async translation operations.

    Executes translation in background thread to avoid blocking UI.
    Emits signals for completion and errors through callback functions.
    """

    def __init__(
        self,
        callback: Callable[[Translation], None],
        error_callback: Callable[[str], None],
        text: str,
        source_lang: str,
        target_lang: str,
        title: str,
        provider: ProviderConfig,
    ):
        super().__init__()
        self._callback = callback
        self._error_callback = error_callback
        self._text = text
        self._source_lang = source_lang
        self._target_lang = target_lang
        self._title = title
        self._provider = provider
        self._service = TranslationUIService.get_instance()

    def run(self) -> None:
        """Execute translation in background thread."""
        try:
            translation = self._service.translate_and_save(
                self._text, self._source_lang, self._target_lang, self._title, self._provider
            )
            self._callback(translation)
        except Exception as e:
            self._error_callback(str(e))


class LanguageDetectionWorker(QRunnable):
    """Worker thread for async language detection.

    Executes language detection in background thread to avoid blocking UI.
    Emits signals for completion and errors through callback functions.
    """

    def __init__(
        self,
        callback: Callable[[str], None],
        error_callback: Callable[[str], None],
        text: str,
        provider: ProviderConfig,
    ):
        super().__init__()
        self._callback = callback
        self._error_callback = error_callback
        self._text = text
        self._provider = provider

    def run(self) -> None:
        """Execute language detection in background thread."""
        try:
            from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator

            translator = PydanticAITranslator(self._provider)
            detected_lang = translator.detect_language(self._text)
            self._callback(detected_lang)
        except Exception as e:
            self._error_callback(str(e))


class CreateTranslationViewModel(BaseViewModel):
    """ViewModel for creating new translations.

    Orchestrates translation operations using TranslationUIService and SettingsService.
    Provides async translation and language detection via QThreadPool.
    Follows MVVM pattern with clean separation of concerns.
    """

    translation_completed = Signal(Translation)
    progress_updated = Signal(int, str)
    language_detected = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._settings_service = SettingsService.get_instance()
        self._thread_pool = QThreadPool.globalInstance()

    @property
    def providers(self) -> list[ProviderConfig]:
        """Get list of configured providers."""
        settings = self._settings_service.get_settings()
        return settings.providers

    @property
    def target_language(self) -> str:
        """Get default target language from settings."""
        settings = self._settings_service.get_settings()
        return settings.target_language

    @property
    def selected_provider(self) -> ProviderConfig | None:
        """Get currently selected provider from settings."""
        return self._settings_service.get_current_provider()

    def load_settings(self) -> None:
        """Load settings from SettingsService.

        Triggers settings reload and emits appropriate signals.
        """
        try:
            self._set_loading(True)
            self._settings_service.load_settings()
        except Exception as e:
            self._emit_error(f"Failed to load settings: {e}")
        finally:
            self._set_loading(False)

    def translate(self, text: str, source_lang: str, title: str, provider: ProviderConfig) -> None:
        """Start async translation operation.

        Executes translation in background thread and emits signals on completion.
        Progress is tracked and emitted via progress_updated signal.

        Args:
            text: Source text to translate
            source_lang: Source language code (en, es, or 'auto')
            title: Title for translation document
            provider: Provider configuration to use
        """
        if not text.strip():
            self._emit_error("Text cannot be empty")
            return

        self._set_loading(True)
        self.progress_updated.emit(0, "Starting translation...")

        target_lang = self.target_language
        worker = TranslationWorker(
            self._on_translation_complete, self._on_translation_error, text, source_lang, target_lang, title, provider
        )
        self._thread_pool.start(worker)

    def detect_language(self, text: str) -> None:
        """Start async language detection.

        Executes language detection in background thread and emits language_detected signal.

        Args:
            text: Text to analyze for language detection
        """
        if not text.strip():
            self._emit_error("Text cannot be empty")
            return

        provider = self.selected_provider
        if not provider:
            self._emit_error("No provider configured")
            return

        self._set_loading(True)
        worker = LanguageDetectionWorker(self._on_language_detected, self._on_detection_error, text, provider)
        self._thread_pool.start(worker)

    @Slot(Translation)
    def _on_translation_complete(self, translation: Translation) -> None:
        """Handle successful translation completion."""
        self._set_loading(False)
        self.progress_updated.emit(100, "Translation complete")
        self.translation_completed.emit(translation)

    @Slot(str)
    def _on_translation_error(self, error: str) -> None:
        """Handle translation error."""
        self._set_loading(False)
        self._emit_error(f"Translation failed: {error}")

    @Slot(str)
    def _on_language_detected(self, language: str) -> None:
        """Handle successful language detection."""
        self._set_loading(False)
        self.language_detected.emit(language)

    @Slot(str)
    def _on_detection_error(self, error: str) -> None:
        """Handle language detection error."""
        self._set_loading(False)
        self._emit_error(f"Language detection failed: {error}")
