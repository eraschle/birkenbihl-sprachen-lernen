"""Main window for Birkenbihl GUI application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from birkenbihl.gui.models.editor_viewmodel import TranslationEditorViewModel
from birkenbihl.gui.models.translation_viewmodel import TranslationCreationViewModel
from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.gui.views.editor_view import EditorView
from birkenbihl.gui.views.settings_view import SettingsView
from birkenbihl.gui.views.translation_view import TranslationView
from birkenbihl.models.translation import Translation
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
        self._settings = settings_service.get_settings()
        self._init_ui()
        self._create_menu_bar()
        self._apply_geometry()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        self.setWindowTitle("Birkenbihl Sprachtrainer")
        self._stacked_widget = QStackedWidget()  # type: ignore[reportUninitializedInstanceVariable]
        self.setCentralWidget(self._stacked_widget)
        self._previous_view_index = -1  # type: ignore[reportUninitializedInstanceVariable]
        self._settings_view_index = -1  # type: ignore[reportUninitializedInstanceVariable]
        self._create_views()
        self._stacked_widget.currentChanged.connect(self._on_view_changed)

    def _create_views(self) -> None:
        """Create and add all views."""
        self._create_translation_view()
        self._create_editor_view()
        self._create_settings_view()

    def _create_translation_view(self) -> None:
        """Create translation creation view."""
        view_model = TranslationCreationViewModel(self._translation_service, parent=self)
        self._translation_view = TranslationView(  # type: ignore[reportUninitializedInstanceVariable]
            view_model, self._settings, self._settings_service, parent=self
        )
        self._translation_view.translation_created.connect(self._on_translation_created)
        self._stacked_widget.addWidget(self._translation_view)

    def _create_editor_view(self) -> None:
        """Create translation editor view."""
        view_model = TranslationEditorViewModel(self._translation_service, parent=self)
        self._editor_view = EditorView(  # type: ignore[reportUninitializedInstanceVariable]
            viewmodel=view_model, settings=self._settings, settings_service=self._settings_service, parent=self
        )
        self._stacked_widget.addWidget(self._editor_view)

    def _create_settings_view(self) -> None:
        """Create settings view."""
        self._settings_viewmodel = SettingsViewModel(  # type: ignore[reportUninitializedInstanceVariable]
            self._settings_service, parent=self
        )
        self._settings_view = SettingsView(  # type: ignore[reportUninitializedInstanceVariable]
            self._settings_viewmodel, parent=self
        )
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

    def _on_translation_created(self, translation: Translation) -> None:
        """Handle translation creation completion.

        Navigate to editor view and load the newly created translation.

        Args:
            translation: Newly created translation (unsaved)
        """
        self._editor_view.set_translation(translation)
        self.show_editor_view()

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

    def closeEvent(self, event) -> None:  # type: ignore
        """Handle window close event - save settings if currently in settings view."""
        if self._stacked_widget.currentIndex() == self._settings_view_index:
            self._settings_viewmodel.save_settings()
        event.accept()
