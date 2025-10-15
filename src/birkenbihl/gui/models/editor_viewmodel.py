"""ViewModel for translation editing."""

from uuid import UUID

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from birkenbihl.gui.models.ui_state import TranslationEditorState
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.services.translation_service import TranslationService


class TranslationEditorViewModel(QObject):
    """ViewModel for translation editor.

    Manages state for editing existing translations.
    Coordinates TranslationService for updates.
    """

    state_changed = Signal(object)  # TranslationEditorState
    sentence_updated = Signal()
    translation_saved = Signal()
    suggestions_loaded = Signal(list)  # list[str]
    error_occurred = Signal(str)  # error message

    def __init__(self, service: TranslationService, parent: QWidget | None = None):
        """Initialize ViewModel.

        Args:
            service: TranslationService instance
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = service
        self._state = TranslationEditorState()

    def initialize(self) -> None:
        """Initialize ViewModel."""
        self._emit_state()

    def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    @property
    def state(self) -> TranslationEditorState:
        """Get current state."""
        return self._state

    def load_translation(self, translation_id: UUID) -> None:
        """Load translation for editing from storage.

        Args:
            translation_id: Translation UUID
        """
        try:
            translation = self._service.get_translation(translation_id)
            if translation:
                self._state.translation = translation
                self._state.has_unsaved_changes = False

                # Auto-select first sentence
                if translation.sentences:
                    self._state.selected_sentence_uuid = translation.sentences[0].uuid
                    self._state.edit_mode = "view"
                    self._validate_current_sentence()

                self._emit_state()
            else:
                self.error_occurred.emit(f"Translation {translation_id} not found")
        except Exception as e:
            self.error_occurred.emit(str(e))

    def set_translation(self, translation: Translation) -> None:
        """Load translation object directly (may be unsaved).

        Args:
            translation: Translation object to load
        """
        self._state.translation = translation
        self._state.has_unsaved_changes = True

        # Auto-select first sentence
        if translation.sentences:
            self._state.selected_sentence_uuid = translation.sentences[0].uuid
            self._state.edit_mode = "view"
            self._validate_current_sentence()

        self._emit_state()

    def select_sentence(self, sentence_uuid: UUID) -> None:
        """Select sentence for editing.

        Args:
            sentence_uuid: Sentence UUID
        """
        self._state.selected_sentence_uuid = sentence_uuid
        self._state.edit_mode = "view"
        self._validate_current_sentence()
        self._emit_state()

    def set_edit_mode(self, mode: str) -> None:
        """Set edit mode.

        Args:
            mode: Edit mode (view, edit_natural, edit_alignment)
        """
        self._state.edit_mode = mode
        self._emit_state()

    def update_natural_translation(self, new_natural: str, provider: ProviderConfig) -> None:
        """Update natural translation and regenerate alignment.

        Args:
            new_natural: New natural translation text
            provider: Provider for alignment regeneration
        """
        if not self._state.translation or not self._state.selected_sentence_uuid:
            self.error_occurred.emit("No sentence selected")
            return

        self._state.is_saving = True
        self._emit_state()

        try:
            updated = self._service.update_sentence_natural(
                self._state.translation.uuid, self._state.selected_sentence_uuid, new_natural, provider
            )
            self._state.translation = updated
            self._state.has_unsaved_changes = False
            self._state.is_saving = False
            self._emit_state()
            self.sentence_updated.emit()
        except Exception as e:
            self._state.is_saving = False
            self._emit_state()
            self.error_occurred.emit(str(e))

    def update_alignment(self, alignments: list[WordAlignment]) -> None:
        """Update word alignments in local state (does not save to storage).

        Args:
            alignments: New alignments
        """
        if not self._state.translation or not self._state.selected_sentence_uuid:
            self.error_occurred.emit("No sentence selected")
            return

        # Find sentence and update alignments
        sentence = next(
            (s for s in self._state.translation.sentences if s.uuid == self._state.selected_sentence_uuid),
            None,
        )

        if not sentence:
            self.error_occurred.emit("Sentence not found")
            return

        sentence.word_alignments = alignments
        self._state.has_unsaved_changes = True

        # Validate after update
        self._validate_current_sentence()
        self._emit_state()

    def generate_suggestions(self, provider: ProviderConfig, count: int = 3) -> None:
        """Generate alternative translation suggestions.

        Args:
            provider: Provider config
            count: Number of suggestions
        """
        if not self._state.translation or not self._state.selected_sentence_uuid:
            return

        try:
            suggestions = self._service.get_sentence_suggestions(
                self._state.translation.uuid, self._state.selected_sentence_uuid, provider, count
            )
            self.suggestions_loaded.emit(suggestions)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def save_translation(self) -> None:
        """Save current translation to storage.

        Automatically decides whether to create new or update existing.
        """
        if not self._state.translation:
            self.error_occurred.emit("No translation to save")
            return

        if self._state.has_validation_errors:
            self.error_occurred.emit(
                f"Cannot save translation with validation errors: {self._state.validation_error_message}"
            )
            return

        self._state.is_saving = True
        self._emit_state()

        try:
            saved = self._service.save_translation(self._state.translation)
            self._state.translation = saved
            self._state.has_unsaved_changes = False
            self._state.is_saving = False
            self._emit_state()
            self.translation_saved.emit()
        except Exception as e:
            self._state.is_saving = False
            self._emit_state()
            self.error_occurred.emit(str(e))

    def _validate_current_sentence(self) -> None:
        """Validate current sentence alignments."""
        if not self._state.translation or not self._state.selected_sentence_uuid:
            self._state.has_validation_errors = False
            self._state.validation_error_message = ""
            return

        sentence = next(
            (s for s in self._state.translation.sentences if s.uuid == self._state.selected_sentence_uuid),
            None,
        )

        if not sentence:
            self._state.has_validation_errors = False
            self._state.validation_error_message = ""
            return

        is_valid, error_msg = validate_alignment_complete(sentence.natural_translation, sentence.word_alignments)

        self._state.has_validation_errors = not is_valid
        self._state.validation_error_message = error_msg or ""

    def _emit_state(self) -> None:
        """Emit state changed signal."""
        self.state_changed.emit(self._state)
