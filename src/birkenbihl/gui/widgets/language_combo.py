"""Language selection ComboBox widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QWidget

from birkenbihl.gui.styles import theme
from birkenbihl.models.languages import Language


class LanguageCombo(QComboBox):
    """ComboBox for Language selection."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(theme.get_default_combobox_style())

    def add_language(self, language: Language) -> None:
        """Add a language to the combo box.

        Args:
            language: Language object to add
        """
        self.addItem(language.name_de, userData=language)

    def add_languages(self, languages: list[Language]) -> None:
        """Add multiple languages to the combo box.

        Args:
            languages: List of Language objects to add
        """
        for language in languages:
            self.add_language(language)

    def current_language(self) -> Language | None:
        """Get currently selected language.

        Returns:
            Selected Language object or None
        """
        return self.currentData(Qt.ItemDataRole.UserRole)

    def set_language(self, code: str) -> bool:
        """Set selected language by code.

        Args:
            code: Language code to select

        Returns:
            True if language was found and selected, False otherwise
        """
        for i in range(self.count()):
            language = self.itemData(i, Qt.ItemDataRole.UserRole)
            if language and language.code == code:
                self.setCurrentIndex(i)
                return True
        return False
