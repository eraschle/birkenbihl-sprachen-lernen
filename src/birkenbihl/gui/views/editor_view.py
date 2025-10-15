"""Translation editor view."""

from uuid import UUID

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.models.editor_viewmodel import TranslationEditorViewModel
from birkenbihl.gui.models.ui_state import TranslationEditorState
from birkenbihl.gui.widgets.alignment_editor import AlignmentEditor
from birkenbihl.gui.widgets.alignment_preview import AlignmentPreview
from birkenbihl.models.settings import Settings
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services.settings_service import SettingsService


class EditorView(QWidget):
    """View for editing existing translations.

    Shows sentence list and edit panel with different modes.
    Delegates business logic to TranslationEditorViewModel.
    """

    def __init__(
        self,
        viewmodel: TranslationEditorViewModel | None = None,
        settings: Settings | None = None,
        settings_service: SettingsService | None = None,
        parent: QWidget | None = None,
    ):
        """Initialize view.

        Args:
            viewmodel: TranslationEditorViewModel instance
            settings: Settings for providers
            settings_service: Optional SettingsService for reloading settings
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel or TranslationEditorViewModel(None, Settings())  # type: ignore[reportArgumentType,reportArgumentType]
        self._settings = settings or Settings()
        self._settings_service = settings_service
        self._sentence_cards = {}
        self.setup_ui()
        self.bind_viewmodel()
        self._viewmodel.initialize()

    def setup_ui(self) -> None:
        """Setup UI components."""
        layout = QHBoxLayout(self)

        # Left column: Translation list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        translations_label = QLabel("<b>Gespeicherte Übersetzungen</b>")
        left_layout.addWidget(translations_label)

        self._translation_list = QListWidget()  # type: ignore[reportUninitializedInstanceVariable]
        self._translation_list.currentRowChanged.connect(self._on_translation_selected)
        left_layout.addWidget(self._translation_list)

        layout.addWidget(left_panel, 1)

        # Middle column: Sentence list
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)

        sentences_label = QLabel("<b>Sätze</b>")
        middle_layout.addWidget(sentences_label)

        self._sentence_list = QListWidget()  # type: ignore[reportUninitializedInstanceVariable]
        self._sentence_list.currentRowChanged.connect(self._on_sentence_selected)
        middle_layout.addWidget(self._sentence_list)

        layout.addWidget(middle_panel, 1)

        # Right: Edit panel
        edit_panel = QWidget()
        edit_layout = QVBoxLayout(edit_panel)

        self._mode_label = QLabel("<b>Ansicht</b>")  # type: ignore[reportUninitializedInstanceVariable]
        edit_layout.addWidget(self._mode_label)

        # Validation error display
        self._validation_error_label = QLabel()  # type: ignore[reportUninitializedInstanceVariable]
        self._validation_error_label.setStyleSheet("color: red; font-weight: bold;")
        self._validation_error_label.setWordWrap(True)
        self._validation_error_label.setVisible(False)
        edit_layout.addWidget(self._validation_error_label)

        self._stacked_widget = QStackedWidget()  # type: ignore[reportUninitializedInstanceVariable]
        edit_layout.addWidget(self._stacked_widget, 1)

        # Mode 1: View mode (AlignmentPreview)
        self._view_widget = self._create_view_widget()  # type: ignore[reportUninitializedInstanceVariable]
        self._stacked_widget.addWidget(self._view_widget)

        # Mode 2: Edit natural mode
        self._edit_natural_widget = self._create_edit_natural_widget()  # type: ignore[reportUninitializedInstanceVariable]
        self._stacked_widget.addWidget(self._edit_natural_widget)

        # Mode 3: Edit alignment mode
        self._edit_alignment_widget = self._create_edit_alignment_widget()  # type: ignore[reportUninitializedInstanceVariable]
        self._stacked_widget.addWidget(self._edit_alignment_widget)

        # Action buttons
        button_layout = QHBoxLayout()
        self._edit_button = QPushButton("Bearbeiten")  # type: ignore[reportUninitializedInstanceVariable]
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._back_button = QPushButton("Zurück")  # type: ignore[reportUninitializedInstanceVariable]
        self._back_button.clicked.connect(self._on_back_clicked)
        self._save_button = QPushButton("Speichern")  # type: ignore[reportUninitializedInstanceVariable]
        self._save_button.clicked.connect(self._on_save_clicked)

        button_layout.addStretch()
        button_layout.addWidget(self._back_button)
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._save_button)

        edit_layout.addLayout(button_layout)

        layout.addWidget(edit_panel, 2)

    def _create_view_widget(self) -> QWidget:
        """Create view mode widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._alignment_preview = AlignmentPreview()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addWidget(self._alignment_preview)

        return widget

    def _create_edit_natural_widget(self) -> QWidget:
        """Create edit natural mode widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._natural_edit = QTextEdit()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addWidget(self._natural_edit)

        save_button = QPushButton("Speichern")
        save_button.clicked.connect(self._on_save_natural)
        layout.addWidget(save_button)

        return widget

    def _create_edit_alignment_widget(self) -> QWidget:
        """Create edit alignment mode widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._alignment_editor = AlignmentEditor()  # type: ignore[reportUninitializedInstanceVariable]
        self._alignment_editor.alignment_changed.connect(self._on_alignment_changed)
        layout.addWidget(self._alignment_editor)

        return widget

    def bind_viewmodel(self) -> None:
        """Bind ViewModel signals to View slots."""
        self._viewmodel.state_changed.connect(self._on_state_changed)
        self._viewmodel.sentence_updated.connect(self._on_sentence_updated)
        self._viewmodel.translation_saved.connect(self._on_translation_saved)
        self._viewmodel.error_occurred.connect(self._on_error)

    def showEvent(self, event) -> None:  # type: ignore
        """Handle show event by reloading settings and translations list."""
        super().showEvent(event)
        self._reload_settings()
        self._load_translations_list()

    def _reload_settings(self) -> None:
        """Reload settings and update UI components."""
        if self._settings_service is None:
            return

        self._settings = self._settings_service.get_settings()

    def _load_translations_list(self) -> None:
        """Load list of all translations from storage."""
        try:
            translations = self._viewmodel._service.list_all_translations()
            self._translation_list.clear()

            if not translations:
                self._translation_list.addItem("Keine Übersetzungen vorhanden")
                self._translation_list.setEnabled(False)
                return

            self._translation_list.setEnabled(True)
            self._translation_ids = []  # type: ignore[reportUninitializedInstanceVariable]

            for translation in translations:
                title = translation.title or "Ohne Titel"
                item_text = f"{title} ({len(translation.sentences)} Sätze)"
                self._translation_list.addItem(item_text)
                self._translation_ids.append(translation.uuid)

        except Exception as e:
            print(f"✗ Error loading translations: {e}")
            self._translation_list.clear()
            self._translation_list.addItem("Fehler beim Laden")
            self._translation_list.setEnabled(False)

    def _on_translation_selected(self, row: int) -> None:
        """Handle translation selection from list.

        Args:
            row: Selected row index
        """
        if row < 0 or not hasattr(self, "_translation_ids"):
            return

        if row >= len(self._translation_ids):
            return

        translation_id = self._translation_ids[row]
        self.load_translation(translation_id)

    def load_translation(self, translation_id: UUID) -> None:
        """Load translation into editor from storage.

        Args:
            translation_id: Translation UUID
        """
        self._viewmodel.load_translation(translation_id)

    def set_translation(self, translation: Translation) -> None:
        """Load translation object directly into editor (may be unsaved).

        Args:
            translation: Translation object
        """
        self._viewmodel.set_translation(translation)

    def _on_sentence_selected(self, row: int) -> None:
        """Handle sentence selection."""
        state = self._viewmodel.state
        if state.translation and 0 <= row < len(state.translation.sentences):
            sentence = state.translation.sentences[row]
            self._viewmodel.select_sentence(sentence.uuid)

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        self._viewmodel.set_edit_mode("edit_natural")

    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        self._viewmodel.set_edit_mode("view")

    def _on_save_natural(self) -> None:
        """Handle save natural translation."""
        new_text = self._natural_edit.toPlainText()
        provider = self._settings.get_default_provider()
        if provider:
            self._viewmodel.update_natural_translation(new_text, provider)

    def _on_alignment_changed(self, alignments: list[WordAlignment]) -> None:
        """Handle alignment change."""
        self._viewmodel.update_alignment(alignments)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        self._viewmodel.save_translation()

    def _on_state_changed(self, state: TranslationEditorState) -> None:
        """Handle state changes."""
        if state.translation:
            self._update_sentence_list(state.translation)

            # Select first sentence in list if one is selected
            # Block signals to prevent infinite loop
            if state.selected_sentence_uuid:
                for idx, sentence in enumerate(state.translation.sentences):
                    if sentence.uuid == state.selected_sentence_uuid:
                        # Only update if different to avoid triggering signal
                        if self._sentence_list.currentRow() != idx:
                            self._sentence_list.blockSignals(True)
                            self._sentence_list.setCurrentRow(idx)
                            self._sentence_list.blockSignals(False)
                        break

        if state.selected_sentence_uuid and state.translation:
            sentence = next(
                (s for s in state.translation.sentences if s.uuid == state.selected_sentence_uuid),
                None,
            )
            if sentence:
                self._update_edit_panel(sentence, state.edit_mode)

        # Update button states and validation display
        self._update_button_states(state)
        self._update_validation_display(state)

    def _update_sentence_list(self, translation: Translation) -> None:
        """Update sentence list."""
        self._sentence_list.clear()
        for sentence in translation.sentences:
            self._sentence_list.addItem(sentence.source_text[:50] + "...")

    def _update_edit_panel(self, sentence: Sentence, mode: str) -> None:
        """Update edit panel based on mode."""
        if mode == "view":
            self._mode_label.setText("<b>Ansicht</b>")
            self._alignment_preview.update_data(sentence.word_alignments)
            self._stacked_widget.setCurrentIndex(0)
            self._edit_button.setVisible(True)
            self._back_button.setVisible(False)

        elif mode == "edit_natural":
            self._mode_label.setText("<b>Natürliche Übersetzung bearbeiten</b>")
            self._natural_edit.setText(sentence.natural_translation)
            self._stacked_widget.setCurrentIndex(1)
            self._edit_button.setVisible(False)
            self._back_button.setVisible(True)

        elif mode == "edit_alignment":
            self._mode_label.setText("<b>Zuordnung bearbeiten</b>")
            self._alignment_editor.update_data(sentence)
            self._stacked_widget.setCurrentIndex(2)
            self._edit_button.setVisible(False)
            self._back_button.setVisible(True)

    def _on_sentence_updated(self) -> None:
        """Handle sentence update."""
        print("✓ Sentence updated")

    def _on_translation_saved(self) -> None:
        """Handle translation saved."""
        print("✓ Translation saved to storage")
        # Reload translations list to show newly saved translation
        self._load_translations_list()

        # Select the saved translation in the list
        if hasattr(self, "_translation_ids") and self._viewmodel.state.translation:
            translation_id = self._viewmodel.state.translation.uuid
            try:
                idx = self._translation_ids.index(translation_id)
                self._translation_list.blockSignals(True)
                self._translation_list.setCurrentRow(idx)
                self._translation_list.blockSignals(False)
            except (ValueError, AttributeError):
                pass

    def _update_button_states(self, state: TranslationEditorState) -> None:
        """Update button enabled/disabled states based on validation.

        Args:
            state: Current editor state
        """
        # Save button only enabled when:
        # - Translation exists
        # - No validation errors
        # - Not currently saving
        can_save = (
            state.translation is not None
            and not state.has_validation_errors
            and not state.is_saving
        )
        self._save_button.setEnabled(can_save)

        # Set tooltip to show validation errors or saving status
        if state.is_saving:
            self._save_button.setToolTip("Speichert...")
        elif state.has_validation_errors:
            self._save_button.setToolTip(
                f"Kann nicht speichern: {state.validation_error_message}"
            )
        else:
            self._save_button.setToolTip("Translation speichern")

    def _update_validation_display(self, state: TranslationEditorState) -> None:
        """Update validation error display.

        Args:
            state: Current editor state
        """
        if state.has_validation_errors and state.validation_error_message:
            self._validation_error_label.setText(f"⚠ {state.validation_error_message}")
            self._validation_error_label.setVisible(True)
        else:
            self._validation_error_label.setVisible(False)

    def _on_error(self, error: str) -> None:
        """Handle error."""
        print(f"✗ Error: {error}")
