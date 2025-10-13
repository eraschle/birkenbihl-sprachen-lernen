"""Language selection widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from birkenbihl.services import language_service as ls


class LanguageSelector(QWidget):
    """Language selection dropdown widget.

    Displays language options with German names.
    Supports auto-detection option.
    Emits signal when language is selected.
    """

    language_selected = Signal(str)  # Language code or "auto"

    def __init__(
        self,
        label_text: str = "Sprache:",
        show_auto_detect: bool = False,
        default_language: str = "de",
        parent: QWidget | None = None,
    ):
        """Initialize widget.

        Args:
            label_text: Label text for dropdown
            show_auto_detect: Show "Automatisch" option
            default_language: Default selected language code
            parent: Parent widget
        """
        super().__init__(parent)
        self._show_auto_detect = show_auto_detect
        self._default_language = default_language
        self._label_text = label_text
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self._label_text)
        self._combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        self._combo.setStyleSheet("""
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e5f3ff;
                color: black;
            }
        """)

        layout.addWidget(label)
        layout.addWidget(self._combo)

        self._populate_combo()

    def _populate_combo(self) -> None:
        """Populate combo box with languages."""
        self._combo.clear()

        if self._show_auto_detect:
            source_lang = ls.get_default_source_language()
            self._combo.addItem(source_lang.name_de, source_lang.code)

        for lang in ls.get_languages(self._show_auto_detect):
            self._combo.addItem(lang.name_de, lang.code)

        self._select_default()

    def _select_default(self) -> None:
        """Select default language."""
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == self._default_language:
                self._combo.setCurrentIndex(i)
                break

    def _on_selection_changed(self, index: int) -> None:
        """Handle selection change.

        Args:
            index: Selected index
        """
        lang_code = self._combo.itemData(index)
        if lang_code:
            self.language_selected.emit(lang_code)

    def get_selected_language(self) -> str:
        """Get currently selected language code.

        Returns:
            Language code or "auto"
        """
        return self._combo.currentData()

    def set_language(self, lang_code: str) -> None:
        """Set selected language.

        Args:
            lang_code: Language code to select
        """
        for idx in range(self._combo.count()):
            if self._combo.itemData(idx) == lang_code:
                self._combo.setCurrentIndex(idx)
                break

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable widget.

        Args:
            enabled: Enable state
        """
        self._combo.setEnabled(enabled)
