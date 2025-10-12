"""Manual word alignment editor widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.models.translation import Sentence, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete


class AlignmentEditor(QWidget):
    """Manual word-by-word alignment editor.

    Allows user to create/modify word alignments by selecting
    target words for each source word using dropdowns.
    Validates alignment completeness.
    """

    alignment_changed = Signal(list)  # list[WordAlignment]
    validation_failed = Signal(str)  # error message

    def __init__(self, sentence: Sentence | None = None, parent=None):
        """Initialize widget.

        Args:
            sentence: Sentence to edit alignments for
            parent: Parent widget
        """
        super().__init__(parent)
        self._sentence = sentence
        self._target_words = []
        self._mappings = {}  # source_word -> target_word
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)

        title_label = QLabel("<b>Wort-für-Wort Zuordnung</b>")
        layout.addWidget(title_label)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)

        self._mapping_widget = QWidget()
        self._mapping_layout = QVBoxLayout(self._mapping_widget)

        self._scroll_area.setWidget(self._mapping_widget)
        layout.addWidget(self._scroll_area)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._validate_button = QPushButton("Validieren")
        self._validate_button.clicked.connect(self._on_validate)

        self._apply_button = QPushButton("Übernehmen")
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
        """Build initial mappings from existing alignments."""
        if not self._sentence:
            return

        self._mappings = {}
        for alignment in self._sentence.word_alignments:
            self._mappings[alignment.source_word] = alignment.target_word

    def _render_mapping_ui(self) -> None:
        """Render mapping dropdowns for each source word."""
        self._clear_mapping_layout()

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
            if item.widget():
                item.widget().deleteLater()

    def _create_mapping_row(self, source_word: str) -> QWidget:
        """Create mapping row for source word.

        Args:
            source_word: Source word

        Returns:
            Widget containing label and dropdown
        """
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 4, 0, 4)

        label = QLabel(f"{source_word} →")
        label.setMinimumWidth(100)

        combo = QComboBox()
        combo.addItem("(nicht zugeordnet)", None)

        for target_word in self._target_words:
            combo.addItem(target_word, target_word)

        current_mapping = self._mappings.get(source_word)
        if current_mapping:
            for i in range(combo.count()):
                if combo.itemData(i) == current_mapping:
                    combo.setCurrentIndex(i)
                    break

        combo.currentIndexChanged.connect(lambda: self._on_mapping_changed(source_word, combo))

        layout.addWidget(label)
        layout.addWidget(combo, 1)

        return row

    def _on_mapping_changed(self, source_word: str, combo: QComboBox) -> None:
        """Handle mapping change.

        Args:
            source_word: Source word
            combo: Combo box
        """
        target_word = combo.currentData()
        if target_word:
            self._mappings[source_word] = target_word
        elif source_word in self._mappings:
            del self._mappings[source_word]

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
        """Apply alignments."""
        alignments = self._build_alignments()
        self.alignment_changed.emit(alignments)

    def _build_alignments(self) -> list[WordAlignment]:
        """Build alignments from current mappings.

        Returns:
            List of word alignments
        """
        alignments = []
        for position, (source_word, target_word) in enumerate(self._mappings.items()):
            alignments.append(
                WordAlignment(
                    source_word=source_word,
                    target_word=target_word,
                    position=position,
                )
            )
        return alignments

    def _show_success(self, message: str) -> None:
        """Show success message.

        Args:
            message: Success message
        """
        # In real implementation, use QMessageBox or status bar
        print(f"✓ {message}")

    def update_data(self, sentence: Sentence) -> None:
        """Update sentence data.

        Args:
            sentence: New sentence
        """
        self._sentence = sentence
        self._load_sentence()
