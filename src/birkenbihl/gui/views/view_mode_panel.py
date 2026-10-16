"""View mode panel for read-only translation display."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter, QVBoxLayout, QWidget

from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.widgets.sentence_list import SentenceList
from birkenbihl.gui.widgets.translation_display import TranslationDisplay
from birkenbihl.models.translation import Translation


class ViewModePanel(QWidget):
    """View mode panel with sentence list and translation display.

    Layout: Horizontal splitter (40% left, 60% right)
    - Left: Numbered sentence list
    - Right: Natural + word-by-word display for selected sentence
    """

    def __init__(self, state: AppState, parent: QWidget | None = None):
        """Initialize view mode panel.

        Args:
            state: Application state
            parent: Parent widget
        """
        super().__init__(parent)
        self._state = state
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = self._create_splitter()
        layout.addWidget(splitter)

    def _create_splitter(self) -> QSplitter:
        """Create horizontal splitter with sentence list and display.

        Returns:
            Splitter with 40/60 split
        """
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._sentence_list = SentenceList()  # type: ignore[reportUninitializedInstanceVariable]
        self._translation_display = TranslationDisplay()  # type: ignore[reportUninitializedInstanceVariable]
        self._empty_label = self._create_empty_label()  # type: ignore[reportUninitializedInstanceVariable]

        splitter.addWidget(self._sentence_list)
        splitter.addWidget(self._empty_label)
        splitter.addWidget(self._translation_display)

        splitter.setStretchFactor(0, 40)
        splitter.setStretchFactor(1, 60)
        splitter.setStretchFactor(2, 60)

        self._translation_display.hide()

        return splitter

    def _create_empty_label(self) -> QLabel:
        """Create label shown when no translation selected.

        Returns:
            Centered empty state label
        """
        label = QLabel("Keine Übersetzung ausgewählt")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _connect_signals(self) -> None:
        """Connect signals to state and widget events."""
        self._state.translation_selected.connect(self._on_translation_selected)
        self._state.sentence_selected.connect(self._on_sentence_selected)
        self._sentence_list.sentence_selected.connect(self._state.select_sentence)

    def _on_translation_selected(self, translation: Translation | None) -> None:
        """Handle translation selection - load sentences.

        Args:
            translation: Selected translation or None
        """
        if translation and translation.sentences:
            self._sentence_list.load_sentences(translation.sentences)
            self._empty_label.hide()
            self._translation_display.show()
            self._display_first_sentence(translation)
        else:
            self._sentence_list.clear()
            self._translation_display.hide()
            self._empty_label.show()

    def _display_first_sentence(self, translation: Translation) -> None:
        """Display first sentence of translation.

        Args:
            translation: Translation with sentences
        """
        if translation.sentences:
            self._translation_display.display_sentence(translation.sentences[0])

    def _on_sentence_selected(self, index: int) -> None:
        """Handle sentence selection - update display.

        Args:
            index: Selected sentence index
        """
        translation = self._state.selected_translation
        if translation and 0 <= index < len(translation.sentences):
            sentence = translation.sentences[index]
            self._translation_display.display_sentence(sentence)
