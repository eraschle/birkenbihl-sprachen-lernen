"""Theme management for the GUI."""

from pathlib import Path

from PySide6.QtWidgets import QApplication


def get_default_combobox_style() -> str:
    """Return the default combo box style.

    Returns: Combo box style
    """
    return """
        QComboBox {
            background-color: white;
            color: black;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            color: black;
        }
        QComboBox QAbstractItemView::item {
            background-color: white;
            color: black;
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: #0078d4;
            color: white;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: #e5f3ff;
            color: black;
        }
    """


class ThemeManager:
    """Manages application theming and stylesheets.

    Singleton pattern for centralized theme management.
    Loads and applies Qt stylesheets (.qss files).
    """

    _instance: "ThemeManager | None" = None
    _current_theme: str = "default"

    def __new__(cls):
        """Singleton instance creation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def apply_theme(self, app: QApplication, theme_name: str = "default") -> None:
        """Apply theme to application.

        Args:
            app: QApplication instance
            theme_name: Name of theme (default, dark, light)
        """
        self._current_theme = theme_name
        stylesheet = self._load_stylesheet(theme_name)
        app.setStyleSheet(stylesheet)

    def _load_stylesheet(self, theme_name: str) -> str:
        """Load stylesheet from file.

        Args:
            theme_name: Theme name

        Returns:
            Stylesheet content as string
        """
        styles_dir = Path(__file__).parent
        stylesheet_path = styles_dir / f"{theme_name}.qss"

        if stylesheet_path.exists():
            return stylesheet_path.read_text()

        return self._get_default_stylesheet()

    def _get_default_stylesheet(self) -> str:
        """Get default stylesheet if file not found."""
        return """
        /* Default Birkenbihl Theme */
        QMainWindow {
            background-color: #f5f5f5;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        QLineEdit, QTextEdit {
            border: 1px solid #ddd;
            padding: 8px;
            border-radius: 4px;
            background-color: white;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #4CAF50;
        }
        """


def get_theme_manager() -> ThemeManager:
    """Get ThemeManager singleton instance."""
    return ThemeManager()
