"""CreateTranslationView for translation creation UI."""

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.components import ProgressWidget, ProviderSelector
from birkenbihl.gui.models.context import ProviderSelectorContext
from birkenbihl.gui.viewmodels.create_vm import CreateTranslationViewModel
from birkenbihl.gui.widgets.language_combo import LanguageCombo
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.services import language_service as ls


class CreateTranslationView(QWidget):
    """View for creating new translations.

    Provides form interface for text input, language selection, and provider configuration.
    Follows MVVM pattern with clean separation from business logic.
    All user interactions are delegated to CreateTranslationViewModel.
    """

    def __init__(self, viewmodel: CreateTranslationViewModel):
        super().__init__()
        self._viewmodel = viewmodel
        self._selected_provider: ProviderConfig | None = None
        self._setup_ui()
        self._connect_signals()
        self._load_initial_data()

    def _setup_ui(self) -> None:
        """Initialize UI components and layout."""
        layout = QVBoxLayout(self)

        form_layout = self._create_form()
        button_layout = self._create_buttons()

        self._progress_widget = ProgressWidget()  # type: ignore[reportUninitializedInstanceVariable]

        layout.addLayout(form_layout)
        layout.addWidget(self._progress_widget)
        layout.addLayout(button_layout)

    def _create_form(self) -> QFormLayout:
        """Create form layout with input fields."""
        form = QFormLayout()

        self._title_input = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self._title_input.setPlaceholderText("Enter translation title...")

        self._text_input = QTextEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self._text_input.setPlaceholderText("Enter text to translate...")

        self._source_lang_combo = self._create_language_combo()  # type: ignore[reportUninitializedInstanceVariable]
        self._provider_selector = self._create_provider_selector()  # type: ignore[reportUninitializedInstanceVariable]

        form.addRow("Title:", self._title_input)
        form.addRow("Text:", self._text_input)
        form.addRow("Source Language:", self._source_lang_combo)
        form.addRow("Provider:", self._provider_selector)

        return form

    def _create_language_combo(self) -> LanguageCombo:
        """Create combo box for source language selection."""
        combo = LanguageCombo()
        languages = ls.get_languages()
        combo.add_languages(languages)
        combo.setCurrentIndex(0)
        return combo

    def _create_provider_selector(self) -> ProviderSelector:
        """Create provider selector component."""
        context = ProviderSelectorContext(
            providers=self._viewmodel.providers,
            default_provider=self._viewmodel.selected_provider,
            disabled=False,
        )
        return ProviderSelector(context)

    def _create_buttons(self) -> QHBoxLayout:
        """Create button layout with action buttons."""
        layout = QHBoxLayout()

        self._detect_button = QPushButton("Detect Language")  # type: ignore[reportUninitializedInstanceVariable]
        self._translate_button = QPushButton("Translate")  # type: ignore[reportUninitializedInstanceVariable]

        self._translate_button.setDefault(True)

        layout.addStretch()
        layout.addWidget(self._detect_button)
        layout.addWidget(self._translate_button)

        return layout

    def _connect_signals(self) -> None:
        """Connect view signals to viewmodel slots."""
        self._translate_button.clicked.connect(self._on_translate_clicked)
        self._detect_button.clicked.connect(self._on_detect_clicked)
        self._provider_selector.provider_changed.connect(self._on_provider_changed)

        self._viewmodel.translation_completed.connect(self._on_translation_completed)
        self._viewmodel.language_detected.connect(self._on_language_detected)
        self._viewmodel.error_occurred.connect(self._on_error_occurred)
        self._viewmodel.loading_changed.connect(self._on_loading_changed)
        self._viewmodel.progress_updated.connect(self._on_progress_updated)

    def _load_initial_data(self) -> None:
        """Load initial settings and provider data."""
        self._viewmodel.load_settings()
        self._selected_provider = self._viewmodel.selected_provider

    def showEvent(self, event) -> None:  # type: ignore
        """Handle show event by refreshing UI without reloading settings."""
        super().showEvent(event)
        self._refresh_ui_from_cached_settings()

    def _refresh_ui_from_cached_settings(self) -> None:
        """Refresh UI components from already loaded settings without file I/O."""
        self._selected_provider = self._viewmodel.selected_provider
        self._refresh_provider_selector()

    def _refresh_provider_selector(self) -> None:
        """Refresh provider selector with updated providers."""
        context = ProviderSelectorContext(
            providers=self._viewmodel.providers,
            default_provider=self._viewmodel.selected_provider,
            disabled=False,
        )
        self._provider_selector.update_context(context)

    def _on_translate_clicked(self) -> None:
        """Handle translate button click."""
        text = self._text_input.toPlainText()
        title = self._title_input.text() or "Untitled Translation"
        source_lang = self._source_lang_combo.current_language()

        if not self._selected_provider:
            self._viewmodel._emit_error("No provider selected")
            return

        if not source_lang:
            self._viewmodel._emit_error("No source language selected")
            return

        if ls.is_auto_detect(source_lang.code):
            self._start_auto_detect_translation(text, title)
        else:
            self._start_translation(text, source_lang, title)

    def _start_auto_detect_translation(self, text: str, title: str) -> None:
        """Start translation with auto-detected language."""
        if not self._selected_provider:
            return

        from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator

        try:
            translator = PydanticAITranslator(self._selected_provider)
            detected_lang = translator.detect_language(text)
            self._start_translation(text, detected_lang, title)
        except Exception as e:
            self._viewmodel._emit_error(f"Language detection failed: {e}")

    def _start_translation(self, text: str, source_lang: Language, title: str) -> None:
        """Start translation with known source language."""
        if not self._selected_provider:
            return
        self._viewmodel.translate(text, source_lang, title, self._selected_provider)

    def _on_detect_clicked(self) -> None:
        """Handle detect language button click."""
        text = self._text_input.toPlainText()
        self._viewmodel.detect_language(text)

    def _on_provider_changed(self, provider: ProviderConfig) -> None:
        """Handle provider selection change."""
        self._selected_provider = provider

    def _on_translation_completed(self, _: Translation) -> None:
        """Handle successful translation completion."""
        self._progress_widget.finish()

    def _on_language_detected(self, language: str) -> None:
        """Handle successful language detection."""
        self._source_lang_combo.set_language(language)

    def _on_error_occurred(self, _: str) -> None:
        """Handle error from viewmodel."""
        self._progress_widget.finish()

    def _on_loading_changed(self, loading: bool) -> None:
        """Handle loading state change."""
        self._translate_button.setEnabled(not loading)
        self._detect_button.setEnabled(not loading)
        if loading:
            self._progress_widget.start("Processing...")

    def _on_progress_updated(self, progress: int, message: str) -> None:
        """Handle progress update from viewmodel."""
        self._progress_widget.update_progress(progress)
        self._progress_widget.set_message(message)
