"""Translation creation view."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QGroupBox,
)

from birkenbihl.gui.models.translation_viewmodel import TranslationCreationViewModel
from birkenbihl.gui.widgets.provider_selector import ProviderSelector
from birkenbihl.gui.widgets.language_selector import LanguageSelector
from birkenbihl.gui.widgets.progress_widget import ProgressWidget
from birkenbihl.models.settings import Settings


class TranslationView(QWidget):
    """View for creating new translations.

    Provides UI for entering title, source text, selecting languages and provider.
    Displays progress during translation.
    Delegates business logic to TranslationCreationViewModel.
    """

    def __init__(self, viewmodel: TranslationCreationViewModel, settings: Settings, parent=None):
        """Initialize view.

        Args:
            viewmodel: TranslationCreationViewModel instance
            settings: Settings for providers and default language
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._settings = settings
        self.setup_ui()
        self.bind_viewmodel()
        self._viewmodel.initialize()

    def setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Title input
        title_label = QLabel("<b>Titel:</b>")
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Geben Sie einen Titel ein...")
        self._title_input.textChanged.connect(self._on_title_changed)

        layout.addWidget(title_label)
        layout.addWidget(self._title_input)

        # Main content: text input + settings
        content_layout = QHBoxLayout()

        # Left: Text input
        text_group = QGroupBox("Text eingeben")
        text_layout = QVBoxLayout(text_group)

        self._text_input = QTextEdit()
        self._text_input.setPlaceholderText("Geben Sie hier den zu übersetzenden Text ein...")
        self._text_input.textChanged.connect(self._on_text_changed)

        text_layout.addWidget(self._text_input)
        content_layout.addWidget(text_group, 3)

        # Right: Settings
        settings_group = QGroupBox("Einstellungen")
        settings_layout = QVBoxLayout(settings_group)

        self._source_lang_selector = LanguageSelector(
            label_text="Quellsprache:",
            show_auto_detect=True,
            default_language="auto",
        )
        self._source_lang_selector.language_selected.connect(self._on_source_lang_changed)

        self._target_lang_selector = LanguageSelector(
            label_text="Zielsprache:",
            show_auto_detect=False,
            default_language=self._settings.target_language,
        )
        self._target_lang_selector.language_selected.connect(self._on_target_lang_changed)

        self._provider_selector = ProviderSelector(self._settings.providers)
        self._provider_selector.provider_selected.connect(self._on_provider_changed)

        settings_layout.addWidget(self._source_lang_selector)
        settings_layout.addWidget(self._target_lang_selector)
        settings_layout.addWidget(self._provider_selector)
        settings_layout.addStretch()

        content_layout.addWidget(settings_group, 1)
        layout.addLayout(content_layout)

        # Progress widget (initially hidden)
        self._progress_widget = ProgressWidget()
        self._progress_widget.cancel_requested.connect(self._on_cancel_requested)
        layout.addWidget(self._progress_widget)

        # Translate button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._translate_button = QPushButton("Übersetzen")
        self._translate_button.clicked.connect(self._on_translate_clicked)

        button_layout.addWidget(self._translate_button)
        layout.addLayout(button_layout)

        # Set initial provider if available
        default_provider = self._settings.get_default_provider()
        if default_provider:
            self._viewmodel.set_provider(default_provider)

    def bind_viewmodel(self) -> None:
        """Bind ViewModel signals to View slots."""
        self._viewmodel.state_changed.connect(self._on_state_changed)
        self._viewmodel.translation_started.connect(self._on_translation_started)
        self._viewmodel.translation_completed.connect(self._on_translation_completed)
        self._viewmodel.translation_failed.connect(self._on_translation_failed)

    def _on_title_changed(self, text: str) -> None:
        """Handle title change."""
        self._viewmodel.set_title(text)

    def _on_text_changed(self) -> None:
        """Handle text change."""
        text = self._text_input.toPlainText()
        self._viewmodel.set_source_text(text)

    def _on_source_lang_changed(self, lang: str) -> None:
        """Handle source language change."""
        self._viewmodel.set_source_language(lang if lang != "auto" else None)

    def _on_target_lang_changed(self, lang: str) -> None:
        """Handle target language change."""
        self._viewmodel.set_target_language(lang)

    def _on_provider_changed(self, provider) -> None:
        """Handle provider change."""
        self._viewmodel.set_provider(provider)

    def _on_translate_clicked(self) -> None:
        """Handle translate button click."""
        self._viewmodel.start_translation()

    def _on_cancel_requested(self) -> None:
        """Handle translation cancellation."""
        self._viewmodel.cancel_translation()

    def _on_state_changed(self, state) -> None:
        """Handle state changes.

        Args:
            state: TranslationCreationState
        """
        is_translating = state.is_translating

        self._title_input.setEnabled(not is_translating)
        self._text_input.setEnabled(not is_translating)
        self._source_lang_selector.set_enabled(not is_translating)
        self._target_lang_selector.set_enabled(not is_translating)
        self._provider_selector.set_enabled(not is_translating)
        self._translate_button.setEnabled(not is_translating)

        if is_translating:
            self._progress_widget.set_progress(state.progress)

    def _on_translation_started(self) -> None:
        """Handle translation start."""
        self._progress_widget.start("Übersetze...")

    def _on_translation_completed(self, translation) -> None:
        """Handle translation completion."""
        self._progress_widget.finish()
        # In real app: navigate to editor or show success
        print(f"✓ Translation created: {translation.title}")

    def _on_translation_failed(self, error: str) -> None:
        """Handle translation failure."""
        self._progress_widget.finish()
        # In real app: show error dialog
        print(f"✗ Translation failed: {error}")
