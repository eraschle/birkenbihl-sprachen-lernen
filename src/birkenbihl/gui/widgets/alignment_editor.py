"""Manual word alignment editor widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.styles import theme
from birkenbihl.models.translation import Sentence, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete


class AlignmentEditor(QWidget):
    """Manual word-by-word alignment editor with multi-word selection support.

    Allows user to create/modify word alignments by:
    - Assigning multiple target words to a single source word
    - Viewing only available (not yet used) target words in dropdowns
    - Reordering selected words with up/down buttons
    - Removing words from selection

    On save, multiple words are joined with hyphens via the hook system.
    """

    alignment_changed = Signal(list)  # list[WordAlignment]
    validation_failed = Signal(str)  # error message

    def __init__(self, parent: QWidget | None = None, sentence: Sentence | None = None):
        """Initialize widget.

        Args:
            sentence: Sentence to edit alignments for
            parent: Parent widget
        """
        super().__init__(parent)
        self._sentence = sentence
        self._target_words: list[str] = []
        self._source_mappings: dict[str, list[str]] = {}  # source_word -> list[target_word]
        self._selected_word_containers: dict[str, tuple[QWidget, QVBoxLayout]] = {}
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
        """Load sentence data."""
        if not self._sentence:
            return

        self._extract_target_words()
        self._build_mappings()
        self._render_mapping_ui()

    def _extract_target_words(self) -> None:
        """Extract target words from natural translation."""
        if not self._sentence:
            return

        natural = self._sentence.natural_translation
        self._target_words = natural.split()

    def _build_mappings(self) -> None:
        """Build initial mappings from existing alignments.

        Converts WordAlignments with hyphens back to list format:
        - "werde-vermissen" -> ["werde", "vermissen"]
        - "Ich" -> ["Ich"]
        """
        if not self._sentence:
            return

        self._source_mappings = {}
        for alignment in self._sentence.word_alignments:
            # Split hyphenated words back to list
            if "-" in alignment.target_word:
                words = alignment.target_word.split("-")
            else:
                words = [alignment.target_word]

            self._source_mappings[alignment.source_word] = words

    def _render_mapping_ui(self) -> None:
        """Render mapping UI for all source words."""
        self._clear_mapping_layout()
        self._selected_word_containers.clear()  # Clear container references

        if not self._sentence:
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
        """Create mapping row for source word with multi-select UI.

        Creates a row with:
        1. Source word label
        2. Dropdown + Add button (for selecting new words)
        3. List of selected words with up/down/remove buttons

        Args:
            source_word: Source word

        Returns:
            Widget containing complete row UI
        """
        row_widget = QWidget()
        main_layout = QVBoxLayout(row_widget)
        main_layout.setContentsMargins(0, 4, 0, 8)

        # Row 1: Source word label
        source_label = QLabel(f"<b>{source_word}</b> →")
        main_layout.addWidget(source_label)

        # Row 2: Dropdown + Add Button
        controls_layout = QHBoxLayout()

        dropdown = QComboBox()
        dropdown.setStyleSheet(theme.get_default_combobox_style())

        # Populate with available (not yet used) target words
        available = self._get_available_target_words(for_source_word=source_word)
        dropdown.addItem("(Wähle Wort...)", None)
        for word in available:
            dropdown.addItem(word, word)

        add_button = QPushButton("+ Hinzufügen")
        add_button.clicked.connect(lambda: self._add_word_to_source(source_word, dropdown))

        controls_layout.addWidget(dropdown, 1)
        controls_layout.addWidget(add_button)
        main_layout.addLayout(controls_layout)

        # Row 3: Label "Ausgewählte Wörter:"
        selected_label = QLabel("Ausgewählte Wörter:")
        main_layout.addWidget(selected_label)

        # Row 4: List of selected words with up/down/remove buttons
        selected_container = QWidget()
        selected_layout = QVBoxLayout(selected_container)
        selected_layout.setContentsMargins(10, 0, 0, 0)

        # Store reference to update later
        self._selected_word_containers[source_word] = (selected_container, selected_layout)

        # Render current mappings
        self._render_selected_words(source_word, selected_layout)

        main_layout.addWidget(selected_container)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        return row_widget

    def _get_available_target_words(self, for_source_word: str | None = None) -> list[str]:
        """Get list of available (not yet mapped) target words.

        Args:
            for_source_word: If provided, includes words already mapped to this source word

        Returns:
            List of available target words in natural translation order
        """
        # Collect all already mapped words
        mapped = set()
        for source, targets in self._source_mappings.items():
            if source != for_source_word:  # Exclude current source word
                mapped.update(targets)

        # Return only words not yet mapped
        return [word for word in self._target_words if word not in mapped]

    def _add_word_to_source(self, source_word: str, dropdown: QComboBox) -> None:
        """Add selected word to source word mapping.

        Args:
            source_word: Source word
            dropdown: Dropdown with selected word
        """
        target_word = dropdown.currentData()
        if not target_word:
            return

        # Add to mappings
        if source_word not in self._source_mappings:
            self._source_mappings[source_word] = []

        self._source_mappings[source_word].append(target_word)

        # Reset dropdown
        dropdown.setCurrentIndex(0)

        # Re-render UI (both selected words list AND all dropdowns)
        self._refresh_ui()

    def _render_selected_words(self, source_word: str, layout: QVBoxLayout) -> None:
        """Render list of selected words with up/down/remove buttons.

        Args:
            source_word: Source word
            layout: Layout to add widgets to
        """
        # Clear existing widgets
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

        words = self._source_mappings.get(source_word, [])
        if not words:
            no_words_label = QLabel("<i>Keine Wörter ausgewählt</i>")
            layout.addWidget(no_words_label)
            return

        for idx, word in enumerate(words):
            word_row = self._create_selected_word_row(source_word, word, idx, len(words))
            layout.addWidget(word_row)

    def _create_selected_word_row(self, source_word: str, word: str, idx: int, total: int) -> QWidget:
        """Create row for single selected word with controls.

        Args:
            source_word: Source word
            word: Target word
            idx: Index in list (0-based)
            total: Total number of words

        Returns:
            Widget with word label and control buttons
        """
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 2, 0, 2)

        # Label: "1. werde"
        label = QLabel(f"{idx + 1}. {word}")
        label.setMinimumWidth(150)
        layout.addWidget(label)

        layout.addStretch()

        # Up button (disabled if first)
        up_btn = QPushButton("↑")
        up_btn.setMaximumWidth(30)
        up_btn.setEnabled(idx > 0)
        up_btn.clicked.connect(lambda: self._move_word_up(source_word, idx))
        layout.addWidget(up_btn)

        # Down button (disabled if last)
        down_btn = QPushButton("↓")
        down_btn.setMaximumWidth(30)
        down_btn.setEnabled(idx < total - 1)
        down_btn.clicked.connect(lambda: self._move_word_down(source_word, idx))
        layout.addWidget(down_btn)

        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self._remove_word_from_source(source_word, idx))
        layout.addWidget(remove_btn)

        return row

    def _move_word_up(self, source_word: str, idx: int) -> None:
        """Move word up in list (decrease index).

        Args:
            source_word: Source word
            idx: Current index of word
        """
        words = self._source_mappings.get(source_word, [])
        if idx > 0 and idx < len(words):
            words[idx - 1], words[idx] = words[idx], words[idx - 1]
            self._refresh_ui()

    def _move_word_down(self, source_word: str, idx: int) -> None:
        """Move word down in list (increase index).

        Args:
            source_word: Source word
            idx: Current index of word
        """
        words = self._source_mappings.get(source_word, [])
        if idx < len(words) - 1:
            words[idx], words[idx + 1] = words[idx + 1], words[idx]
            self._refresh_ui()

    def _remove_word_from_source(self, source_word: str, idx: int) -> None:
        """Remove word from source word mapping.

        Args:
            source_word: Source word
            idx: Index of word to remove
        """
        words = self._source_mappings.get(source_word, [])
        if 0 <= idx < len(words):
            words.pop(idx)
            self._refresh_ui()

    def _refresh_ui(self) -> None:
        """Refresh entire UI after changes.

        Re-renders:
        1. All dropdowns (to update available words)
        2. All selected word lists
        """
        self._render_mapping_ui()

    def _on_validate(self) -> None:
        """Validate current alignments."""
        alignments = self._build_alignments()

        if not self._sentence:
            return

        is_valid, error = validate_alignment_complete(self._sentence.natural_translation, alignments)

        if is_valid:
            self._show_success("Validierung erfolgreich!")
        else:
            self.validation_failed.emit(error or "Validierung fehlgeschlagen")

    def _on_apply(self) -> None:
        """Apply alignments using hook system."""
        alignments = self._build_alignments()
        self.alignment_changed.emit(alignments)

    def _build_alignments(self) -> list[WordAlignment]:
        """Build alignments from current mappings using hook system.

        Uses AlignmentHookManager to process multi-word mappings.
        Multiple target words are joined with hyphens by the hook.

        Returns:
            List of word alignments with hyphenated multi-word targets
        """
        from birkenbihl.gui.hooks.alignment_hooks import AlignmentHookManager

        hook_manager = AlignmentHookManager()
        alignments = hook_manager.process(self._source_mappings, self._target_words)
        return alignments

    def _show_success(self, message: str) -> None:
        """Show success message.

        Args:
            message: Success message
        """
        QMessageBox.information(self, "Validierung erfolgreich", message)

    def update_data(self, sentence: Sentence) -> None:
        """Update sentence data.

        Args:
            sentence: New sentence
        """
        self._sentence = sentence
        self._load_sentence()
