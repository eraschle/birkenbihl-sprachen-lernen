"""Edit mode panel for editing natural translations with AI support."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.utils.async_helper import AsyncWorker
from birkenbihl.gui.widgets.interleaved_grid_editable import InterleavedGridEditable
from birkenbihl.gui.widgets.natural_editor import NaturalEditor
from birkenbihl.gui.widgets.sentence_list import SentenceList
from birkenbihl.models import dateutils
from birkenbihl.models.translation import Translation, WordAlignment
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class EditModePanel(QWidget):
    """Panel for editing natural translations with AI generation support.

    Layout: Splitter with sentence list (40%) and editor/preview (60%).
    Supports manual editing and AI-powered regeneration of translations.
    """

    def __init__(
        self,
        service: TranslationService,
        settings_service: SettingsService,
        state: AppState,
        parent: QWidget | None = None,
    ):
        """Initialize edit mode panel.

        Args:
            service: Translation service for operations
            settings_service: Settings service for provider access
            state: Application state
            parent: Parent widget
        """
        super().__init__(parent)
        self._service = service
        self._settings_service = settings_service
        self._state = state
        self._current_translation: Translation | None = None
        self._current_sentence_index = 0
        self._has_unsaved_changes = False
        self._worker: AsyncWorker | None = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.addWidget(self._create_splitter())
        layout.addLayout(self._create_bottom_bar())

    def _create_splitter(self) -> QSplitter:
        """Create splitter with sentence list and editor/preview.

        Returns:
            Configured splitter widget
        """
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_sentence_list_group())
        splitter.addWidget(self._create_editor_group())
        splitter.setSizes([400, 600])
        return splitter

    def _create_sentence_list_group(self) -> QGroupBox:
        """Create sentence list group box.

        Returns:
            Group box with sentence list
        """
        group = QGroupBox("Originalsätze")
        layout = QVBoxLayout(group)

        self._sentence_list = SentenceList()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addWidget(self._sentence_list)

        return group

    def _create_editor_group(self) -> QWidget:
        """Create editor group with natural editor and preview.

        Returns:
            Widget containing editor and preview
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(self._create_natural_group())
        layout.addWidget(self._create_preview_group())

        return widget

    def _create_natural_group(self) -> QGroupBox:
        """Create natural translation editor group.

        Returns:
            Group box with natural editor
        """
        group = QGroupBox("Natürliche Übersetzung")
        layout = QVBoxLayout(group)

        self._natural_editor = NaturalEditor()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addWidget(self._natural_editor)

        return group

    def _create_preview_group(self) -> QGroupBox:
        """Create word-by-word editable grid group.

        Returns:
            Group box with interleaved grid editor
        """
        group = QGroupBox("Wort-für-Wort (Bearbeiten)")
        layout = QVBoxLayout(group)

        self._interleaved_grid = InterleavedGridEditable()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addWidget(self._interleaved_grid)

        return group

    def _create_bottom_bar(self) -> QHBoxLayout:
        """Create bottom bar with save button.

        Returns:
            Layout with save button
        """
        layout = QHBoxLayout()
        layout.addStretch()

        self._save_button = QPushButton("Speichern")  # type: ignore[reportUninitializedInstanceVariable]
        self._save_button.setToolTip("Save changes to storage")
        self._save_button.setEnabled(False)
        layout.addWidget(self._save_button)

        return layout

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self._state.translation_selected.connect(self._on_translation_loaded)
        self._sentence_list.sentence_selected.connect(self._on_sentence_selected)
        self._natural_editor.text_changed.connect(self._on_text_changed)
        self._natural_editor.generate_requested.connect(self._on_generate_clicked)
        self._interleaved_grid.alignments_changed.connect(self._on_alignments_changed)
        self._interleaved_grid.validation_error.connect(self._on_validation_error)
        self._save_button.clicked.connect(self._on_save_clicked)

    def _on_translation_loaded(self, translation: Translation | None) -> None:
        """Handle translation selection from state.

        Args:
            translation: Selected translation or None
        """
        self._current_translation = translation
        self._current_sentence_index = 0
        self._has_unsaved_changes = False
        self._save_button.setEnabled(False)

        if translation and translation.sentences:
            self._sentence_list.load_sentences(translation.sentences)
            self._load_sentence(0)
        else:
            self._show_empty_state()

    def _on_sentence_selected(self, index: int) -> None:
        """Handle sentence selection from list.

        Args:
            index: Selected sentence index (0-based)
        """
        if self._current_translation:
            self._load_sentence(index)

    def _load_sentence(self, index: int) -> None:
        """Load sentence for editing.

        Args:
            index: Sentence index (0-based)
        """
        if not self._current_translation:
            return

        sentence = self._current_translation.sentences[index]

        self._natural_editor.set_text(sentence.natural_translation)
        self._interleaved_grid.build_grid(sentence)

        self._current_sentence_index = index

    def _on_text_changed(self, new_text: str) -> None:
        """Handle manual text change.

        Args:
            new_text: New natural translation text
        """
        self._has_unsaved_changes = True
        self._save_button.setEnabled(True)

    def _on_alignments_changed(self, alignments: list[WordAlignment]) -> None:
        """Handle word alignments changed via drag&drop.

        Args:
            alignments: New word alignments from grid
        """
        if not self._current_translation:
            return

        sentence = self._current_translation.sentences[self._current_sentence_index]
        sentence.word_alignments = alignments
        self._current_translation.updated_at = dateutils.create_now()

        self._has_unsaved_changes = True

    def _on_validation_error(self, error_msg: str) -> None:
        """Handle validation error from grid.

        Args:
            error_msg: Error message (empty if valid)
        """
        has_error = bool(error_msg)
        self._save_button.setEnabled(self._has_unsaved_changes and not has_error)

    def _on_generate_clicked(self) -> None:
        """Handle AI generation request."""
        if not self._current_translation:
            return

        provider_config = self._settings_service.get_default_provider()
        if not provider_config:
            self._show_error("Kein Standard-Provider konfiguriert")
            return

        self._start_ai_generation(provider_config)

    def _start_ai_generation(self, provider_config: object) -> None:
        """Start AI generation in background thread.

        Args:
            provider_config: Provider configuration for AI translation
        """
        if not self._current_translation:
            return

        self._natural_editor.set_loading(True)

        sentence = self._current_translation.sentences[self._current_sentence_index]

        self._worker = AsyncWorker(
            self._regenerate_alignments,
            sentence.source_text,
            self._natural_editor.get_text(),
            self._current_translation.source_language,
            self._current_translation.target_language,
            provider_config,
        )
        self._worker.task_completed.connect(self._on_generation_success)
        self._worker.task_failed.connect(self._on_generation_error)
        self._worker.start()

    def _regenerate_alignments(
        self,
        source_text: str,
        natural_translation: str,
        source_lang: str,
        target_lang: str,
        provider_config: object,
    ) -> list[WordAlignment]:
        """Regenerate word alignments using AI.

        Args:
            source_text: Source sentence text
            natural_translation: Natural translation text
            source_lang: Source language code
            target_lang: Target language code
            provider_config: Provider configuration

        Returns:
            List of word alignments
        """
        translator = PydanticAITranslator(provider_config)  # type: ignore
        return translator.regenerate_alignment(source_text, natural_translation, source_lang, target_lang)  # type: ignore

    def _on_generation_success(self, new_alignments: list[WordAlignment]) -> None:
        """Handle successful AI generation.

        Args:
            new_alignments: New word alignments from AI
        """
        self._natural_editor.set_loading(False)

        if not self._current_translation:
            return

        sentence = self._current_translation.sentences[self._current_sentence_index]
        sentence.natural_translation = self._natural_editor.get_text()
        sentence.word_alignments = new_alignments
        self._current_translation.updated_at = dateutils.create_now()

        self._interleaved_grid.build_grid(sentence)

        self._has_unsaved_changes = True
        self._save_button.setEnabled(True)
        self._worker = None

    def _on_generation_error(self, error_message: str) -> None:
        """Handle AI generation error.

        Args:
            error_message: Error message from worker
        """
        self._natural_editor.set_loading(False)
        self._show_error(f"AI-Generierung fehlgeschlagen: {error_message}")
        self._worker = None

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        if not self._has_unsaved_changes or not self._current_translation:
            return

        try:
            self._service.save_translation(self._current_translation)
            self._has_unsaved_changes = False
            self._save_button.setEnabled(False)
            self._show_success("Änderungen gespeichert")
        except Exception as e:
            self._show_error(f"Speichern fehlgeschlagen: {e}")

    def _show_empty_state(self) -> None:
        """Show empty state message."""
        self._natural_editor.set_text("")
        self._natural_editor.set_edit_enabled(False)

    def _show_error(self, message: str) -> None:
        """Show error message dialog.

        Args:
            message: Error message
        """
        QMessageBox.critical(self, "Fehler", message)

    def _show_success(self, message: str) -> None:
        """Show success message dialog.

        Args:
            message: Success message
        """
        QMessageBox.information(self, "Erfolg", message)
