"""Main window for Birkenbihl GUI application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.gui.views.settings_view import SettingsView
from birkenbihl.gui.views.translation_view import TranslationView
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class MainWindow(QMainWindow):
    """Main application window with view navigation."""

    def __init__(
        self, translation_service: TranslationService, settings_service: SettingsService, parent: QWidget | None = None
    ):
        """Initialize main window.

        Args:
            translation_service: TranslationService instance
            settings_service: SettingsService instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._translation_service = translation_service
        self._settings_service = settings_service
        self._app_state = AppState(parent=self)
        self._init_ui()
        self._create_menu_bar()
        self._apply_geometry()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("Birkenbihl Sprachtrainer")
        self._create_tabbed_views()

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
        message_lines = [
            "Birkenbihl Sprachtrainer",
            "Digitale Umsetzung der Vera F. Birkenbihl Sprachlernmethode.",
            "Version 1.0",
        ]
        QMessageBox.about(self, "Über Birkenbihl", "\n\n".join(message_lines))

    def _apply_geometry(self) -> None:
        """Apply window geometry."""
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

    def closeEvent(self, event) -> None:  # type: ignore
        """Handle window close event - save settings."""
        self._settings_viewmodel.save_settings()
        event.accept()
