"""CREATE mode panel for creating new translations."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.models.app_state import AppMode, AppState
from birkenbihl.gui.widgets.language_selector import LanguageSelector
from birkenbihl.gui.widgets.provider_selector import ProviderSelector
from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class CreateModePanel(QWidget):
    """Panel for creating new translations with AI or manually.

    Provides form interface for entering title, text, languages,
    and provider selection. Supports both AI translation and manual entry.
    """

    def __init__(
        self,
        translation_service: TranslationService,
        settings_service: SettingsService,
        app_state: AppState,
        parent: QWidget | None = None,
    ):
        """Initialize CREATE mode panel.

        Args:
            translation_service: Service for translation operations
            settings_service: Service for settings and provider access
            app_state: Global application state
            parent: Parent widget
        """
        super().__init__(parent)
        self._service = translation_service
        self._settings_service = settings_service
        self._state = app_state
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.addWidget(self._create_title_field())
        layout.addWidget(self._create_text_field())
        layout.addLayout(self._create_selectors())
        layout.addStretch()
        layout.addLayout(self._create_buttons())
        self._connect_signals()

    def _create_title_field(self) -> QWidget:
        """Create title input field.

        Returns:
            Widget containing title label and input
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10)

        label = QLabel("Titel:")
        self._title_input: QLineEdit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self._title_input.setPlaceholderText("Titel der Übersetzung eingeben...")

        layout.addWidget(label)
        layout.addWidget(self._title_input)

        return container

    def _create_text_field(self) -> QWidget:
        """Create text input field.

        Returns:
            Widget containing text label and input
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10)

        label = QLabel("Originaltext:")
        self._text_input: QTextEdit = QTextEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self._text_input.setPlaceholderText("Text zum Übersetzen eingeben...")
        self._text_input.setMinimumHeight(150)

        layout.addWidget(label)
        layout.addWidget(self._text_input)

        return container

    def _create_selectors(self) -> QHBoxLayout:
        """Create language and provider selectors.

        Returns:
            Layout with source, target, and provider selectors
        """
        layout = QHBoxLayout()

        self._source_selector: LanguageSelector = LanguageSelector(  # type: ignore[reportUninitializedInstanceVariable]
            label_text="Ausgangssprache:",
            show_auto_detect=True,
            default_language="auto",
            parent=self,
        )
        self._target_selector: LanguageSelector = LanguageSelector(  # type: ignore[reportUninitializedInstanceVariable]
            label_text="Zielsprache:",
            show_auto_detect=False,
            default_language="de",
            parent=self,
        )

        providers = self._get_providers_with_manual()
        self._provider_selector: ProviderSelector = ProviderSelector(  # type: ignore[reportUninitializedInstanceVariable]
            providers, parent=self
        )

        layout.addWidget(self._source_selector)
        layout.addWidget(self._target_selector)
        layout.addWidget(self._provider_selector)

        return layout

    def _create_buttons(self) -> QHBoxLayout:
        """Create action buttons.

        Returns:
            Layout with cancel and create buttons
        """
        layout = QHBoxLayout()
        layout.addStretch()

        self._cancel_button: QPushButton = QPushButton("Abbrechen")  # type: ignore[reportUninitializedInstanceVariable]
        self._create_button: QPushButton = QPushButton("Erstellen")  # type: ignore[reportUninitializedInstanceVariable]
        self._create_button.setEnabled(False)

        layout.addWidget(self._cancel_button)
        layout.addWidget(self._create_button)

        return layout

    def _connect_signals(self) -> None:
        """Connect signals to handlers."""
        self._title_input.textChanged.connect(self._validate_form)
        self._text_input.textChanged.connect(self._validate_form)
        self._cancel_button.clicked.connect(self._on_cancel_clicked)
        self._create_button.clicked.connect(self._on_create_clicked)

    def _validate_form(self) -> None:
        """Validate form and update create button state."""
        is_valid = bool(self._title_input.text().strip() and self._text_input.toPlainText().strip())
        self._create_button.setEnabled(is_valid)

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self._clear_form()
        self._state.set_mode(AppMode.VIEW)

    def _on_create_clicked(self) -> None:
        """Handle create button click."""
        try:
            translation = self._create_translation()
            saved = self._service.save_translation(translation)
            self._state.select_translation(saved)
            self._state.set_mode(AppMode.EDIT)
            self._clear_form()
        except Exception as e:
            self._show_error(str(e))

    def _create_translation(self) -> Translation:
        """Create translation from form data.

        Returns:
            Translation object (AI-generated or manual)
        """
        title = self._title_input.text().strip()
        text = self._text_input.toPlainText().strip()
        source_lang = self._get_source_language()
        target_lang = self._get_target_language()
        provider = self._provider_selector.get_selected_provider()

        if self._is_manual_mode(provider):
            return self._create_manual_translation(title, text, source_lang, target_lang)
        if not provider:
            raise ValueError("No provider selected")
        return self._create_ai_translation(title, text, source_lang, target_lang, provider)

    def _create_ai_translation(
        self, title: str, text: str, source_lang: Language, target_lang: Language, provider: ProviderConfig
    ) -> Translation:
        """Create AI-generated translation.

        Args:
            title: Translation title
            text: Source text
            source_lang: Source language
            target_lang: Target language
            provider: AI provider config

        Returns:
            AI-generated Translation
        """
        translator = PydanticAITranslator(provider)
        return translator.translate(text, source_lang, target_lang, title)

    def _create_manual_translation(
        self, title: str, text: str, source_lang: Language, target_lang: Language
    ) -> Translation:
        """Create empty translation for manual entry.

        Args:
            title: Translation title
            text: Source text
            source_lang: Source language
            target_lang: Target language

        Returns:
            Empty Translation with single sentence
        """
        sentence = Sentence(source_text=text, natural_translation="", word_alignments=[])
        return Translation(
            title=title, source_language=source_lang, target_language=target_lang, sentences=[sentence]
        )

    def _get_source_language(self) -> Language:
        """Get selected source language.

        Returns:
            Source Language object
        """
        code = self._source_selector.get_selected_language()
        if code == "auto":
            text = self._text_input.toPlainText().strip()
            provider = self._get_default_provider()
            translator = PydanticAITranslator(provider)
            detected = translator.detect_language(text)
            return detected
        return self._language_from_code(code)

    def _get_target_language(self) -> Language:
        """Get selected target language.

        Returns:
            Target Language object
        """
        code = self._target_selector.get_selected_language()
        return self._language_from_code(code)

    def _language_from_code(self, code: str) -> Language:
        """Convert language code to Language object.

        Args:
            code: Language code

        Returns:
            Language object
        """
        from birkenbihl.services import language_service as ls

        lang = ls.get_language_by(code)
        return lang

    def _get_providers_with_manual(self) -> list[ProviderConfig]:
        """Get providers list with manual option.

        Returns:
            List of providers including manual option
        """
        providers = self._settings_service.get_settings().providers.copy()
        manual = ProviderConfig(name="Manual", provider_type="manual", model="", api_key="")
        providers.append(manual)
        return providers

    def _get_default_provider(self) -> ProviderConfig:
        """Get default provider for auto-detection.

        Returns:
            Default provider config
        """
        provider = self._settings_service.get_default_provider()
        if not provider:
            raise ValueError("No default provider configured")
        return provider

    def _is_manual_mode(self, provider: ProviderConfig | None) -> bool:
        """Check if manual mode is selected.

        Args:
            provider: Selected provider

        Returns:
            True if manual mode selected
        """
        return provider is not None and provider.provider_type == "manual"

    def _clear_form(self) -> None:
        """Clear all form inputs."""
        self._title_input.clear()
        self._text_input.clear()

    def _show_error(self, message: str) -> None:
        """Show error message dialog.

        Args:
            message: Error message to display
        """
        QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen der Übersetzung:\n\n{message}")
