"""Container widget for managing tag widgets and adding new tags."""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget

from birkenbihl.gui.controllers.alignment_controller import AlignmentController
from birkenbihl.gui.widgets.tag_widget import TagWidget


class TagContainer(QWidget):
    """Container for managing a collection of TagWidgets with a ComboBox for adding new tags.

    Features:
    - Displays TagWidgets for currently assigned words
    - ComboBox for selecting and adding available words
    - Auto-refreshes when controller signals changes
    - Updates controller when tags are added/removed
    """

    def __init__(self, source_word: str, controller: AlignmentController, parent: QWidget | None = None):
        """Initialize the tag container.

        Args:
            source_word: The source word this container manages tags for
            controller: The alignment controller managing state
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._source_word = source_word
        self._controller = controller
        self._tags: list[TagWidget] = []

        # Listen to controller
        self._controller.mappings_changed.connect(self._on_mappings_changed)

        self._setup_ui()
        self._refresh_ui()  # Initial render

    def _setup_ui(self):
        """Set up the UI layout and widgets."""
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        # ComboBox
        self._combobox = QComboBox()
        self._combobox.setMinimumWidth(120)
        self._combobox.setMaximumHeight(24)
        self._combobox.currentTextChanged.connect(self._on_word_selected)
        self._layout.addWidget(self._combobox)
        self._layout.addStretch()

    def _on_mappings_changed(self):
        """Handle controller mappings changed signal."""
        self._refresh_ui()

    def _refresh_ui(self):
        """Refresh the UI based on current controller state."""
        # 1. Clear existing tags
        for tag in self._tags:
            self._layout.removeWidget(tag)  # Remove from layout FIRST
            tag.deleteLater()  # Then delete widget
        self._tags.clear()

        # 2. Rebuild tags from controller.get_assigned_words(self._source_word)
        assigned = self._controller.get_assigned_words(self._source_word)
        for i, word in enumerate(assigned):
            tag = TagWidget(word)
            tag.removed.connect(lambda w=word: self._on_tag_removed(w))
            self._layout.insertWidget(i, tag)
            self._tags.append(tag)

        # 3. Rebuild ComboBox
        # All ComboBoxes show the same list: all words minus ALL assigned words
        available = self._controller.get_available_words()
        self._combobox.clear()
        self._combobox.addItem("[+ Wort hinzufügen]", None)
        for word in available:
            self._combobox.addItem(word, word)

        # 4. Disable ComboBox if no words available
        self._combobox.setEnabled(len(available) > 0)

    def _on_word_selected(self, text: str):
        """Handle word selection from ComboBox.

        Args:
            text: The selected text (not used, we use currentData instead)
        """
        word = self._combobox.currentData()
        if word:
            self._controller.add_word(self._source_word, word)
            self._combobox.setCurrentIndex(0)  # Reset to placeholder

    def _on_tag_removed(self, word: str):
        """Handle tag removal.

        Args:
            word: The word to remove
        """
        self._controller.remove_word(self._source_word, word)
