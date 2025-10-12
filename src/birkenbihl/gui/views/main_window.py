"""Main window for Birkenbihl GUI application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStackedWidget,
)

from birkenbihl.gui.models.editor_viewmodel import TranslationEditorViewModel
from birkenbihl.gui.models.settings_viewmodel import SettingsViewModel
from birkenbihl.gui.models.translation_viewmodel import TranslationCreationViewModel
from birkenbihl.gui.views.editor_view import EditorView
from birkenbihl.gui.views.settings_view import SettingsView
from birkenbihl.gui.views.translation_view import TranslationView
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class MainWindow(QMainWindow):
    """Main application window with view navigation."""

    def __init__(
        self,
        translation_service: TranslationService,
        settings_service: SettingsService,
        parent=None,
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
        self._create_views()

    def _create_views(self) -> None:
        """Create and add all views."""
        self._create_translation_view()
        self._create_editor_view()
        self._create_settings_view()

    def _create_translation_view(self) -> None:
        """Create translation creation view."""
        vm = TranslationCreationViewModel(
            self._translation_service,
            self._settings,
        )
        self._translation_view = TranslationView(vm, self._settings)
        self._stacked_widget.addWidget(self._translation_view)

    def _create_editor_view(self) -> None:
        """Create translation editor view."""
        vm = TranslationEditorViewModel(
            self._translation_service,
            self._settings,
        )
        self._editor_view = EditorView(vm, self._settings)
        self._stacked_widget.addWidget(self._editor_view)

    def _create_settings_view(self) -> None:
        """Create settings view."""
        vm = SettingsViewModel(self._settings_service)
        self._settings_view = SettingsView(vm)
        self._stacked_widget.addWidget(self._settings_view)

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = self.menuBar()
        self._create_file_menu(menubar)
        self._create_view_menu(menubar)
        self._create_help_menu(menubar)

    def _create_file_menu(self, menubar: QMenuBar) -> None:
        """Create File menu."""
        file_menu = menubar.addMenu("&Datei")
        file_menu.addAction("&Neue Übersetzung", self.show_translation_view)
        file_menu.addAction("Übersetzung &bearbeiten", self.show_editor_view)
        file_menu.addSeparator()
        file_menu.addAction("&Beenden", self.close)

    def _create_view_menu(self, menubar: QMenuBar) -> None:
        """Create View menu."""
        view_menu = menubar.addMenu("&Ansicht")
        view_menu.addAction("&Erstellen", self.show_translation_view)
        view_menu.addAction("&Editor", self.show_editor_view)
        view_menu.addAction("&Einstellungen", self.show_settings_view)

    def _create_help_menu(self, menubar: QMenuBar) -> None:
        """Create Help menu."""
        help_menu = menubar.addMenu("&Hilfe")
        help_menu.addAction("Über &Birkenbihl", self._show_about)

    def show_translation_view(self) -> None:
        """Show translation creation view."""
        self._stacked_widget.setCurrentWidget(self._translation_view)

    def show_editor_view(self) -> None:
        """Show translation editor view."""
        self._stacked_widget.setCurrentWidget(self._editor_view)

    def show_settings_view(self) -> None:
        """Show settings view."""
        self._stacked_widget.setCurrentWidget(self._settings_view)

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

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        event.accept()
