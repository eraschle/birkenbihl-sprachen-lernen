"""Main window for Birkenbihl GUI application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.gui.views.settings_view import SettingsView
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class MainWindow(QMainWindow):
    """Main application window with view navigation."""

    def __init__(
        self,
        translation_service: TranslationService,
        settings_service: SettingsService,
        parent: QWidget | None = None,
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
        self._settings = settings_service.get_settings()
        self._init_ui()
        self._create_menu_bar()
        self._apply_geometry()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("Birkenbihl Sprachtrainer")
        self._stacked_widget = QStackedWidget()
        self.setCentralWidget(self._stacked_widget)
        self._previous_view_index = -1
        self._settings_view_index = -1
        self._create_views()
        self._stacked_widget.currentChanged.connect(self._on_view_changed)

    def _create_views(self) -> None:
        """Create and add all views."""
        self._create_settings_view()

    def _create_settings_view(self) -> None:
        """Create settings view."""
        self._settings_viewmodel = SettingsViewModel(self._settings_service, parent=self)
        self._settings_view = SettingsView(self._settings_viewmodel, parent=self)
        self._stacked_widget.addWidget(self._settings_view)
        self._settings_view_index = self._stacked_widget.count() - 1

    def _on_view_changed(self, current_index: int) -> None:
        """Handle view change - auto-save settings when leaving settings view.

        Args:
            current_index: Index of the newly active view
        """
        if self._previous_view_index == self._settings_view_index:
            self._settings_viewmodel.save_settings()

        self._previous_view_index = current_index

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()
        self._create_file_menu(menubar)
        self._create_view_menu(menubar)
        self._create_help_menu(menubar)

    def _create_file_menu(self, menubar: QMenuBar) -> None:
        """Create File menu."""
        file_menu = menubar.addMenu("&Datei")
        file_menu.addAction("&Einstellungen", self.show_settings_view)
        file_menu.addSeparator()
        file_menu.addAction("&Beenden", self.close)

    def _create_view_menu(self, menubar: QMenuBar) -> None:
        """Create View menu."""
        view_menu = menubar.addMenu("&Ansicht")
        view_menu.addAction("&Einstellungen", self.show_settings_view)

    def _create_help_menu(self, menubar: QMenuBar) -> None:
        """Create Help menu."""
        help_menu = menubar.addMenu("&Hilfe")
        help_menu.addAction("Über &Birkenbihl", self._show_about)

    def show_settings_view(self) -> None:
        """Show settings view."""
        self._stacked_widget.setCurrentWidget(self._settings_view)

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Über Birkenbihl",
            "Birkenbihl Sprachtrainer\n\n"
            "Digitale Umsetzung der Vera F. Birkenbihl "
            "Sprachlernmethode.\n\nVersion 1.0",
        )

    def _apply_geometry(self) -> None:
        """Apply window geometry."""
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

    def closeEvent(self, event) -> None:  # type: ignore
        """Handle window close event - save settings if in settings view."""
        current_idx = self._stacked_widget.currentIndex()
        if current_idx == self._settings_view_index:
            self._settings_viewmodel.save_settings()
        event.accept()
