"""Theme management for the GUI."""

from pathlib import Path

from PySide6.QtWidgets import QApplication


class Colors:
    """Centralized color palette for the application.

    All UI components should use these constants instead of hardcoded hex values.
    This enables easy theme changes and future dark mode support.
    """

    # Background colors
    BACKGROUND_LIGHT = "#f0f0f0"
    BACKGROUND_LIGHTER = "#f9f9f9"
    BACKGROUND_HOVER = "#e8e8e8"
    BACKGROUND_WHITE = "white"

    # Border colors
    BORDER_NORMAL = "#ccc"
    BORDER_HOVER = "#999"
    BORDER_LIGHT = "#ddd"

    # Accent colors
    ACCENT_BLUE = "#0096ff"
    ACCENT_BLUE_HOVER = "rgba(0, 150, 255, 0.1)"

    # Semantic colors
    ERROR_RED = "#ff0000"
    ERROR_BG = "rgba(255, 0, 0, 0.05)"

    # Text colors
    TEXT_PRIMARY = "black"
    TEXT_SECONDARY = "#666666"


class Spacing:
    """Centralized spacing constants for consistent layout."""

    # Padding
    PADDING_SMALL = "5px 10px"
    PADDING_MEDIUM = "8px"
    PADDING_LARGE = "10px"

    # Border radius
    RADIUS_NORMAL = "4px"

    # Margins
    MARGIN_SMALL = 2
    MARGIN_MEDIUM = 5
    MARGIN_LARGE = 10


def get_word_tag_style(state: str = "normal") -> str:
    """Get stylesheet for draggable word tags.

    Args:
        state: Tag state - "normal" or "hover"

    Returns:
        CSS stylesheet for word tag
    """
    if state == "hover":
        bg_color = Colors.BACKGROUND_HOVER
        border_color = Colors.BORDER_HOVER
    else:
        bg_color = Colors.BACKGROUND_LIGHT
        border_color = Colors.BORDER_NORMAL

    return f"""
        QLabel {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {Spacing.RADIUS_NORMAL};
            padding: {Spacing.PADDING_SMALL};
        }}
    """


def get_drop_zone_style(highlighted: bool = False) -> str:
    """Get stylesheet for drag-and-drop zones.

    Args:
        highlighted: Whether drop zone is currently highlighted (drag hover)

    Returns:
        CSS stylesheet for drop zone
    """
    if highlighted:
        return f"""
            QLabel {{
                background-color: {Colors.ACCENT_BLUE_HOVER};
                border: 2px solid {Colors.ACCENT_BLUE};
                border-radius: {Spacing.RADIUS_NORMAL};
            }}
        """
    return f"""
        QLabel {{
            background-color: transparent;
            border: 2px dashed {Colors.BORDER_LIGHT};
            border-radius: {Spacing.RADIUS_NORMAL};
        }}
    """


def get_error_frame_style() -> str:
    """Get stylesheet for error state frames.

    Returns:
        CSS stylesheet for error state
    """
    return f"""
        QFrame {{
            background-color: {Colors.ERROR_BG};
            border: 1px solid {Colors.ERROR_RED};
            border-radius: {Spacing.RADIUS_NORMAL};
        }}
    """


def get_pool_frame_style(highlighted: bool = False) -> str:
    """Get stylesheet for unassigned word pool frames.

    Args:
        highlighted: Whether pool is currently highlighted (drag hover)

    Returns:
        CSS stylesheet for pool frame
    """
    if highlighted:
        return f"""
            QFrame {{
                background-color: {Colors.ACCENT_BLUE_HOVER};
                border: 2px solid {Colors.ACCENT_BLUE};
                border-radius: {Spacing.RADIUS_NORMAL};
            }}
        """
    return f"""
        QFrame {{
            background-color: {Colors.BACKGROUND_LIGHTER};
            border: 1px solid {Colors.BORDER_LIGHT};
            border-radius: {Spacing.RADIUS_NORMAL};
        }}
    """


def get_error_label_style() -> str:
    """Get stylesheet for error message labels.

    Returns:
        CSS stylesheet for error label
    """
    return f"""
        QLabel {{
            color: {Colors.ERROR_RED};
        }}
    """


def get_default_combobox_style() -> str:
    """Get stylesheet for combo box widgets.

    Returns:
        CSS stylesheet for combo box
    """
    return f"""
        QComboBox {{
            background-color: {Colors.BACKGROUND_WHITE};
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox QAbstractItemView {{
            background-color: {Colors.BACKGROUND_WHITE};
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox QAbstractItemView::item {{
            background-color: {Colors.BACKGROUND_WHITE};
            color: {Colors.TEXT_PRIMARY};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: #0078d4;
            color: white;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: #e5f3ff;
            color: {Colors.TEXT_PRIMARY};
        }}
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
