"""Interleaved alignment editor view."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QToolBar, QVBoxLayout, QWidget

from birkenbihl.gui.viewmodels.alignment_editor_vm import AlignmentEditorViewModel, AlignmentState
from birkenbihl.gui.widgets.alignment import AlignmentGrid, UnassignedWordsPool
from birkenbihl.models.translation import Sentence


class InterleavedAlignmentEditor(QWidget):
    """Complete word alignment editor with interleaved grid.

    Composes AlignmentGrid, UnassignedWordsPool, toolbar, and validation
    panel into single widget. Follows MVVM pattern.

    Signals:
        save_requested(list[WordAlignment]): Emitted when save clicked
        cancel_requested(): Emitted when cancel clicked
        regenerate_requested(Sentence): Emitted when regenerate clicked
    """

    save_requested = Signal(list)
    cancel_requested = Signal()
    regenerate_requested = Signal(object)

    def __init__(self, viewmodel: AlignmentEditorViewModel, parent: QWidget | None = None):
        """Initialize editor with viewmodel.

        Args:
            viewmodel: ViewModel managing state
            parent: Parent widget
        """
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._current_sentence: Sentence | None = None

        self._toolbar: QToolBar
        self._save_button: QPushButton
        self._reset_button: QPushButton
        self._regenerate_button: QPushButton
        self._grid: AlignmentGrid
        self._unassigned_pool: UnassignedWordsPool
        self._validation_panel: QLabel

        self._setup_ui()
        self._bind_viewmodel()

    def _setup_ui(self) -> None:
        """Build UI layout and widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)

        # Alignment grid (scrollable)
        self._grid = AlignmentGrid()
        self._grid.setMinimumHeight(200)
        layout.addWidget(self._grid, stretch=1)

        # Unassigned words pool
        self._unassigned_pool = UnassignedWordsPool()
        layout.addWidget(self._unassigned_pool)

        # Validation panel
        self._validation_panel = QLabel()
        self._validation_panel.setWordWrap(True)
        self._validation_panel.setStyleSheet("padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
        layout.addWidget(self._validation_panel)

    def _create_toolbar(self) -> QToolBar:
        """Create toolbar with action buttons.

        Returns:
            Configured toolbar
        """
        toolbar = QToolBar()
        toolbar.setMovable(False)

        self._save_button = QPushButton("💾 Save")
        self._save_button.clicked.connect(self.on_save_clicked)
        self._save_button.setEnabled(False)
        toolbar.addWidget(self._save_button)

        self._reset_button = QPushButton("↺ Reset")
        self._reset_button.clicked.connect(self.on_reset_clicked)
        toolbar.addWidget(self._reset_button)

        self._regenerate_button = QPushButton("🤖 Regenerate AI")
        self._regenerate_button.clicked.connect(self.on_regenerate_clicked)
        toolbar.addWidget(self._regenerate_button)

        return toolbar

    def _bind_viewmodel(self) -> None:
        """Connect ViewModel signals to view slots."""
        self._viewmodel.state_changed.connect(self._on_state_changed)
        self._viewmodel.validation_changed.connect(self._on_validation_changed)

        # Connect grid signals to viewmodel
        self._grid.word_moved.connect(lambda w, from_col, to_col: self._on_word_moved(w, from_col, to_col))

    def load_sentence(self, sentence: Sentence) -> None:
        """Load sentence into editor.

        Args:
            sentence: Sentence to edit
        """
        self._current_sentence = sentence
        self._viewmodel.load_sentence(sentence)

    def on_save_clicked(self) -> None:
        """Handle save button click."""
        is_valid, _ = self._viewmodel.validate()
        if not is_valid:
            return

        alignments = self._viewmodel.to_word_alignments()
        self.save_requested.emit(alignments)

    def on_reset_clicked(self) -> None:
        """Handle reset button click."""
        self._viewmodel.reset()

    def on_regenerate_clicked(self) -> None:
        """Handle regenerate button click."""
        if self._current_sentence:
            self.regenerate_requested.emit(self._current_sentence)

    def _on_state_changed(self, state: AlignmentState) -> None:
        """Handle state changed from viewmodel.

        Args:
            state: New alignment state
        """
        # Update grid
        self._grid.build_grid(state.source_words, state.assigned_words)

        # Update unassigned pool
        self._unassigned_pool.set_words(state.unassigned_words)

        # Update save button
        self._save_button.setEnabled(state.is_valid)

    def _on_validation_changed(self, is_valid: bool, errors: list[str]) -> None:
        """Handle validation changed from viewmodel.

        Args:
            is_valid: Whether current state is valid
            errors: List of error messages
        """
        if is_valid:
            self._validation_panel.setText("✅ All words assigned. Ready to save.")
            self._validation_panel.setStyleSheet(
                "padding: 8px; background-color: #e8f5e9; color: #2e7d32; border-radius: 4px;"
            )
        else:
            error_text = "\n".join(f"⚠️ {err}" for err in errors)
            self._validation_panel.setText(error_text)
            self._validation_panel.setStyleSheet(
                "padding: 8px; background-color: #fff3cd; color: #856404; border-radius: 4px;"
            )

        # Trigger grid validation to highlight errors
        self._grid.validate()

    def _on_word_moved(self, word: str, from_column: int, to_column: int) -> None:
        """Handle word moved between columns.

        Args:
            word: Word that was moved
            from_column: Source column index
            to_column: Destination column index
        """
        # Update viewmodel state
        self._viewmodel.unassign_word(word, from_column)
        self._viewmodel.assign_word(word, to_column)
