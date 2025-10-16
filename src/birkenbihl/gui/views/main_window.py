"""Main window for Birkenbihl GUI application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QWidget,
)

from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.gui.views.settings_view import SettingsView
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class MainWindow(QMainWindow):
    """Main application window with view navigation."""

    def __init__(
        self, translation_service: TranslationService, settings_service: SettingsService, parent: QWidget | None = None
    ):
        """Initialize main window.

        Args:
            translation_service: TranslationService instance (unused, kept for compatibility)
            settings_service: SettingsService instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._settings_service = settings_service
        self._init_ui()
        self._create_menu_bar()
        self._apply_geometry()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("Birkenbihl Sprachtrainer - Einstellungen")
        self._create_settings_view()

    def _create_settings_view(self) -> None:
        """Create settings view."""
        self._settings_viewmodel = SettingsViewModel(  # type: ignore[reportUninitializedInstanceVariable]
            self._settings_service, parent=self
        )
        self._settings_view = SettingsView(  # type: ignore[reportUninitializedInstanceVariable]
            self._settings_viewmodel, parent=self
        )
        self.setCentralWidget(self._settings_view)

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()
        self._create_file_menu(menubar)
        self._create_help_menu(menubar)

    def _create_file_menu(self, menubar: QMenuBar) -> None:
        """Create File menu."""
        file_menu = menubar.addMenu("&Datei")
        file_menu.addAction("&Beenden", self.close)

    def _create_help_menu(self, menubar: QMenuBar) -> None:
        """Create Help menu."""
        help_menu = menubar.addMenu("&Hilfe")
        help_menu.addAction("Über &Birkenbihl", self._show_about)

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Über Birkenbihl",
            "Birkenbihl Sprachtrainer\n\nDigitale Umsetzung der Vera F. Birkenbihl Sprachlernmethode.\n\nVersion 1.0",
        )

    def _apply_geometry(self) -> None:
        """Apply window geometry."""
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

    def closeEvent(self, event) -> None:  # type: ignore
        """Handle window close event - save settings."""
        self._settings_viewmodel.save_settings()
        event.accept()
