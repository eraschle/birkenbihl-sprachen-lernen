"""Manual word alignment editor widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.controllers.alignment_controller import AlignmentController
from birkenbihl.gui.widgets.tag_container import TagContainer
from birkenbihl.models.translation import Sentence, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete


class AlignmentEditor(QWidget):
    """Manual word-by-word alignment editor with tag-based UI.

    Features:
    - Tag-based UI (like email/social media tags)
    - Central controller prevents duplicate assignments
    - All UI components stay synchronized automatically
    - ComboBox disabled when no words available
    - Hover effects on tags (× button appears)
    """

    alignment_changed = Signal(list)  # list[WordAlignment]
    validation_succeeded = Signal(str)  # success message
    validation_failed = Signal(str)  # error message

    def __init__(self, parent: QWidget | None = None, sentence: Sentence | None = None):
        """Initialize widget.

        Args:
            sentence: Sentence to edit alignments for
            parent: Parent widget
        """
        super().__init__(parent)
        self._sentence = sentence
        self._controller: AlignmentController | None = None
        self._scroll_area = QScrollArea()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        title_label = QLabel("<b>Wort-für-Wort Zuordnung</b>")
        layout.addWidget(title_label)

        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self._mapping_widget = QWidget()  # type: ignore[reportUninitializedInstanceVariable]
        self._mapping_layout = QVBoxLayout(self._mapping_widget)  # type: ignore[reportUninitializedInstanceVariable]

        self._scroll_area.setWidget(self._mapping_widget)
        layout.addWidget(self._scroll_area)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._validate_button = QPushButton("Validieren")  # type: ignore[reportUninitializedInstanceVariable]
        self._validate_button.clicked.connect(self._on_validate)

        self._apply_button = QPushButton("Übernehmen")  # type: ignore[reportUninitializedInstanceVariable]
        self._apply_button.clicked.connect(self._on_apply)

        button_layout.addWidget(self._validate_button)
        button_layout.addWidget(self._apply_button)

        layout.addLayout(button_layout)

        if self._sentence:
            self._load_sentence()

    def _load_sentence(self) -> None:
        """Load sentence data and create controller."""
        if not self._sentence:
            return

        # Extract target words from natural translation
        target_words = self._sentence.natural_translation.split()

        # Build initial mappings (WITH BUG FIX!)
        initial_mappings = self._build_mappings_from_alignments()

        # Create controller
        self._controller = AlignmentController(target_words, initial_mappings)

        # Render UI
        self._render_mapping_ui()

    def _build_mappings_from_alignments(self) -> dict[str, list[str]]:
        """Build mappings from sentence alignments.

        Converts WordAlignments with hyphens back to list format:
        - "werde-vermissen" -> ["werde", "vermissen"]
        - "Ich" -> ["Ich"]

        **BUG FIX:** Uses extend() instead of = to avoid overwriting
        when multiple alignments exist for the same source word.

        Returns:
            Dictionary mapping source words to lists of target words
        """
        if not self._sentence:
            return {}

        mappings: dict[str, list[str]] = {}
        for alignment in self._sentence.word_alignments:
            # Split hyphenated words back to list
            if "-" in alignment.target_word:
                words = alignment.target_word.split("-")
            else:
                words = [alignment.target_word]

            # FIX: Extend instead of overwrite!
            if alignment.source_word not in mappings:
                mappings[alignment.source_word] = []
            mappings[alignment.source_word].extend(words)

        return mappings

    def _render_mapping_ui(self) -> None:
        """Render mapping UI for all source words."""
        self._clear_mapping_layout()

        if not self._sentence or not self._controller:
            return

        source_words = self._sentence.source_text.split()

        for source_word in source_words:
            row = self._create_mapping_row(source_word)
            self._mapping_layout.addWidget(row)

    def _clear_mapping_layout(self) -> None:
        """Clear mapping layout."""
        while self._mapping_layout.count():
            item = self._mapping_layout.takeAt(0)
            if item.widget() and hasattr(item.widget(), "deleteLater"):
                item.widget().deleteLater()  # type: ignore[reportOptionalMemberAccess]

    def _create_mapping_row(self, source_word: str) -> QWidget:
        """Create mapping row with source label + TagContainer.

        Much simpler than before - TagContainer handles everything!

        Args:
            source_word: Source word

        Returns:
            Widget containing source label and tag container
        """
        if not self._controller:
            return QWidget()

        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 2, 0, 2)

        # Source word label
        source_label = QLabel(f"<b>{source_word}</b> →")
        source_label.setMinimumWidth(100)
        layout.addWidget(source_label)

        # Tag container (handles all the rest!)
        tag_container = TagContainer(source_word, self._controller)
        layout.addWidget(tag_container, 1)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        # Container widget with vertical layout
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(row_widget)
        main_layout.addWidget(separator)

        return container

    def _on_validate(self) -> None:
        """Validate current alignments."""
        alignments = self._build_alignments()

        if not self._sentence:
            return

        is_valid, error = validate_alignment_complete(self._sentence.natural_translation, alignments)

        if is_valid:
            self.validation_succeeded.emit("Validierung erfolgreich!")
        else:
            self.validation_failed.emit(error or "Validierung fehlgeschlagen")

    def _on_apply(self) -> None:
        """Apply alignments using hook system."""
        alignments = self._build_alignments()
        self.alignment_changed.emit(alignments)

    def _build_alignments(self) -> list[WordAlignment]:
        """Build alignments from controller state using hook system.

        Uses AlignmentHookManager to process multi-word mappings.
        Multiple target words are joined with hyphens by the hook.

        Returns:
            List of word alignments with hyphenated multi-word targets
        """
        from birkenbihl.gui.hooks.alignment_hooks import AlignmentHookManager

        if not self._controller:
            return []

        mappings = self._controller.get_mappings()
        target_words = self._controller._target_words

        hook_manager = AlignmentHookManager()
        alignments = hook_manager.process(mappings, target_words)
        return alignments

    def update_data(self, sentence: Sentence) -> None:
        """Update sentence data.

        Args:
            sentence: New sentence
        """
        self._sentence = sentence
        self._load_sentence()
