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


class EditorView(QWidget):
    """View for editing existing translations.

    Shows sentence list and edit panel with different modes.
    Delegates business logic to TranslationEditorViewModel.
    """

    def __init__(
        self,
        viewmodel: TranslationEditorViewModel | None = None,
        settings: Settings | None = None,
        parent: QWidget | None = None,
    ):
        """Initialize view.

        Args:
            viewmodel: TranslationEditorViewModel instance
            settings: Settings for providers
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel or TranslationEditorViewModel(None, Settings())  # type: ignore
        self._settings = settings or Settings()
        self._sentence_cards = {}
        self.setup_ui()
        self.bind_viewmodel()
        self._viewmodel.initialize()

    def setup_ui(self) -> None:
        """Setup UI components."""
        layout = QHBoxLayout(self)

        # Left: Sentence list
        self._sentence_list = QListWidget()  # type: ignore[reportUninitializedInstanceVariable]
        self._sentence_list.currentRowChanged.connect(self._on_sentence_selected)
        layout.addWidget(self._sentence_list, 1)

        # Right: Edit panel
        edit_panel = QWidget()
        edit_layout = QVBoxLayout(edit_panel)

        self._mode_label = QLabel("<b>Ansicht</b>")  # type: ignore[reportUninitializedInstanceVariable]
        edit_layout.addWidget(self._mode_label)

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

        button_layout.addStretch()
        button_layout.addWidget(self._back_button)
        button_layout.addWidget(self._edit_button)

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
        self._viewmodel.error_occurred.connect(self._on_error)

    def showEvent(self, event) -> None:  # type: ignore
        """Handle show event by reloading settings."""
        super().showEvent(event)
        self._reload_settings()

    def _reload_settings(self) -> None:
        """Reload settings and update UI components."""
        from birkenbihl.services.settings_service import SettingsService

        settings_service = SettingsService.get_instance()
        self._settings = settings_service.get_settings()

    def load_translation(self, translation_id: UUID) -> None:
        """Load translation into editor.

        Args:
            translation_id: Translation UUID
        """
        self._viewmodel.load_translation(translation_id)

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

    def _on_state_changed(self, state: TranslationEditorState) -> None:
        """Handle state changes."""
        if state.translation:
            self._update_sentence_list(state.translation)

        if state.selected_sentence_uuid and state.translation:
            sentence = next(
                (s for s in state.translation.sentences if s.uuid == state.selected_sentence_uuid),
                None,
            )
            if sentence:
                self._update_edit_panel(sentence, state.edit_mode)

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

    def _on_error(self, error: str) -> None:
        """Handle error."""
        print(f"✗ Error: {error}")
