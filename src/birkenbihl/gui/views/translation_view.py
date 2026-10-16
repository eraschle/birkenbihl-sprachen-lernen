"""Main translation view with three modes: VIEW, CREATE, EDIT."""

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.models.app_state import AppMode, AppState
from birkenbihl.gui.views.create_mode_panel import CreateModePanel
from birkenbihl.gui.views.edit_mode_panel import EditModePanel
from birkenbihl.gui.views.view_mode_panel import ViewModePanel
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService


class TranslationView(QWidget):
    """Main view managing VIEW/CREATE/EDIT modes.

    Shows header with translation selector + mode buttons,
    and content area that switches between mode-specific panels.
    """

    def __init__(
        self,
        translation_service: TranslationService,
        settings_service: SettingsService,
        app_state: AppState,
        parent: QWidget | None = None,
    ):
        """Initialize translation view.

        Args:
            translation_service: Service for translation operations
            settings_service: Service for settings and provider access
            app_state: Global application state
            parent: Parent widget
        """
        super().__init__(parent)
        self._service = translation_service
        self._settings_service = settings_service
        self._state = app_state
        self._init_ui()
        self._connect_signals()
        self._load_translations()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.addLayout(self._create_header())
        layout.addWidget(self._create_content_area())

    def _create_header(self) -> QHBoxLayout:
        """Create header with translation selector and mode buttons."""
        header = QHBoxLayout()

        label = QLabel("Bestehende Übersetzungen")
        header.addWidget(label)

        self._translation_combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self._translation_combo.setMinimumWidth(300)
        self._translation_combo.currentIndexChanged.connect(self._on_translation_selected)
        header.addWidget(self._translation_combo, stretch=1)

        self._edit_button = QPushButton("Edit")  # type: ignore[reportUninitializedInstanceVariable]
        self._edit_button.setToolTip("Übersetzung bearbeiten")
        self._edit_button.clicked.connect(self._on_edit_clicked)
        header.addWidget(self._edit_button)

        self._new_button = QPushButton("New")  # type: ignore[reportUninitializedInstanceVariable]
        self._new_button.setToolTip("Neue Übersetzung erstellen")
        self._new_button.clicked.connect(self._on_new_clicked)
        header.addWidget(self._new_button)

        return header

    def _create_content_area(self) -> QStackedWidget:
        """Create stacked widget for mode-specific content."""
        self._content_stack = QStackedWidget()  # type: ignore[reportUninitializedInstanceVariable]

        self._view_panel = ViewModePanel(self._state, parent=self)  # type: ignore[reportUninitializedInstanceVariable]
        self._create_panel = CreateModePanel(  # type: ignore[reportUninitializedInstanceVariable]
            self._service,
            self._settings_service,
            self._state,
            parent=self,
        )
        self._edit_panel = EditModePanel(  # type: ignore[reportUninitializedInstanceVariable]
            self._service,
            self._settings_service,
            self._state,
            parent=self,
        )

        self._content_stack.addWidget(self._view_panel)
        self._content_stack.addWidget(self._create_panel)
        self._content_stack.addWidget(self._edit_panel)

        return self._content_stack

    def _connect_signals(self) -> None:
        """Connect signals to state changes."""
        self._state.mode_changed.connect(self._on_mode_changed)
        self._state.translation_selected.connect(self._update_button_states)

    def _load_translations(self) -> None:
        """Load all translations into combobox."""
        translations = self._service.list_all_translations()
        self._translation_combo.clear()

        for translation in translations:
            self._translation_combo.addItem(translation.title, userData=translation)

        if translations:
            self._state.select_translation(translations[0])

    def _on_translation_selected(self, index: int) -> None:
        """Handle translation selection from combobox."""
        if index >= 0:
            translation = self._translation_combo.itemData(index)
            self._state.select_translation(translation)
            if self._state.mode != AppMode.CREATE:
                self._state.set_mode(AppMode.VIEW)

    def _on_edit_clicked(self) -> None:
        """Handle Edit/Save button click."""
        if self._state.mode == AppMode.EDIT:
            # Save button in EDIT mode - delegate to edit panel
            self._edit_panel.save_changes()
        else:
            # Edit button in VIEW mode - switch to EDIT
            self._state.set_mode(AppMode.EDIT)

    def _on_new_clicked(self) -> None:
        """Handle New/Cancel button click."""
        if self._state.mode == AppMode.EDIT:
            # Cancel button in EDIT mode - restore original state and return to VIEW
            self._edit_panel.cancel_changes()
            self._state.set_mode(AppMode.VIEW)
        else:
            # New button - create new translation
            self._state.select_translation(None)
            self._state.set_mode(AppMode.CREATE)

    def _on_mode_changed(self, mode: AppMode) -> None:
        """Handle mode change - switch content panel."""
        mode_to_index = {
            AppMode.VIEW: 0,
            AppMode.CREATE: 1,
            AppMode.EDIT: 2,
        }
        self._content_stack.setCurrentIndex(mode_to_index[mode])
        self._update_button_states()

    def _update_button_states(self) -> None:
        """Update button enabled states based on current mode and selection."""
        mode = self._state.mode
        has_selection = self._state.selected_translation is not None

        # Combobox enabled only in VIEW mode
        self._translation_combo.setEnabled(mode == AppMode.VIEW)

        # Edit button: "Edit" in VIEW, "Save" in EDIT
        if mode == AppMode.EDIT:
            self._edit_button.setText("Save")
            self._edit_button.setToolTip("Änderungen speichern")
            self._edit_button.setEnabled(True)
        else:
            self._edit_button.setText("Edit")
            self._edit_button.setToolTip("Übersetzung bearbeiten")
            self._edit_button.setEnabled(mode == AppMode.VIEW and has_selection)

        # New button: "New" in VIEW/CREATE, "Cancel" in EDIT
        if mode == AppMode.EDIT:
            self._new_button.setText("Cancel")
            self._new_button.setToolTip("Bearbeitung abbrechen")
        else:
            self._new_button.setText("New")
            self._new_button.setToolTip("Neue Übersetzung erstellen")
