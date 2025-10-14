"""SettingsView for application settings UI."""

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.styles import theme
from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.gui.widgets.language_combo import LanguageCombo
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.registry import ProviderRegistry
from birkenbihl.services import language_service as ls


class ProviderDialog(QDialog):
    """Dialog for adding or editing provider configuration."""

    def __init__(self, provider_config: ProviderConfig | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Provider" if provider_config is None else "Edit Provider")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.resize(500, 300)
        self.setSizeGripEnabled(True)
        self.setModal(False)
        self._provider_config = provider_config
        self._init_ui()
        if provider_config:
            self._populate_fields()
        else:
            self._update_auto_name()

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        self._create_form_fields()
        self._add_fields_to_layout(layout)
        self._add_spacer(layout)
        self._add_buttons(layout)
        self._connect_signals()
        self._update_base_url_visibility()

    def _create_form_fields(self) -> None:
        self.name_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.type_combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.type_combo.setStyleSheet(theme.get_default_combobox_style())
        self._populate_provider_types()
        self.model_combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.model_combo.setStyleSheet(theme.get_default_combobox_style())
        self.model_combo.setEditable(True)
        self.api_key_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.base_url_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.base_url_label = QLabel("Base URL:")  # type: ignore[reportUninitializedInstanceVariable]
        self.is_default_check = QCheckBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.supports_streaming_check = QCheckBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.supports_streaming_check.setChecked(True)

    def _populate_provider_types(self) -> None:
        """Populate provider type combo with available providers from registry."""
        for provider in ProviderRegistry.get_supported_providers():
            self.type_combo.addItem(provider.display_name, userData=provider.provider_type)

    def _add_fields_to_layout(self, layout: QFormLayout) -> None:
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Provider Type:", self.type_combo)
        layout.addRow("Model:", self.model_combo)
        layout.addRow("API Key:", self.api_key_edit)
        self.base_url_row_index = layout.rowCount()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addRow(self.base_url_label, self.base_url_edit)
        layout.addRow("Set as Default:", self.is_default_check)
        layout.addRow("Supports Streaming:", self.supports_streaming_check)
        self._form_layout = layout  # type: ignore[reportUninitializedInstanceVariable]

    def _add_spacer(self, layout: QFormLayout) -> None:
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

    def _connect_signals(self) -> None:
        self.type_combo.currentIndexChanged.connect(self._on_provider_type_changed)
        self.model_combo.currentTextChanged.connect(self._on_provider_or_model_changed)

    def _add_buttons(self, layout: QFormLayout) -> None:
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate_fields(self) -> None:
        if not self._provider_config:
            return
        self.name_edit.setText(self._provider_config.name)
        self._set_provider_type_by_code(self._provider_config.provider_type)
        self._populate_models_for_provider(self._provider_config.provider_type)
        self.model_combo.setCurrentText(self._provider_config.model)
        self.api_key_edit.setText(self._provider_config.api_key)
        self.base_url_edit.setText(self._provider_config.api_url)
        self.is_default_check.setChecked(self._provider_config.is_default)
        self.supports_streaming_check.setChecked(self._provider_config.supports_streaming)
        self._update_base_url_visibility()

    def _set_provider_type_by_code(self, provider_type: str) -> None:
        """Set provider type combo by provider_type code."""
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == provider_type:
                self.type_combo.setCurrentIndex(i)
                return

    def _populate_models_for_provider(self, provider_type: str) -> None:
        """Populate model combo with models for the selected provider type."""
        provider_metadata = ProviderRegistry.get_provider_metadata(provider_type)
        if not provider_metadata:
            return
        self.model_combo.clear()
        for model_name in provider_metadata.default_models:
            self.model_combo.addItem(model_name)

    def _on_provider_type_changed(self) -> None:
        """Handle provider type selection change."""
        provider_type = self.type_combo.currentData()
        if provider_type:
            self._populate_models_for_provider(provider_type)
        self._on_provider_or_model_changed()

    def _on_provider_or_model_changed(self) -> None:
        self._update_auto_name()
        self._update_base_url_visibility()

    def _update_auto_name(self) -> None:
        self.name_edit.setText(self._generate_auto_name())

    def _generate_auto_name(self) -> str:
        display_name = self.type_combo.currentText()
        model_name = self.model_combo.currentText().strip()
        if model_name:
            return f"{display_name} - {model_name}"
        return display_name

    def _update_base_url_visibility(self) -> None:
        provider_type = self.type_combo.currentData()
        provider_meta = ProviderRegistry.get_provider_metadata(provider_type)
        if not provider_meta:
            return

        label_item = self._form_layout.itemAt(self.base_url_row_index, QFormLayout.ItemRole.LabelRole)
        field_item = self._form_layout.itemAt(self.base_url_row_index, QFormLayout.ItemRole.FieldRole)
        if label_widget := label_item.widget():
            label_widget.setVisible(provider_meta.requires_api_url)
        if combobox_widget := field_item.widget():
            combobox_widget.setVisible(provider_meta.requires_api_url)

    def get_provider(self) -> ProviderConfig | None:
        if not self._validate_input():
            return None

        return ProviderConfig(
            name=self.name_edit.text().strip(),
            provider_type=self.type_combo.currentData(),
            model=self.model_combo.currentText().strip(),
            api_key=self.api_key_edit.text().strip(),
            api_url=self.base_url_edit.text().strip(),
            is_default=self.is_default_check.isChecked(),
            supports_streaming=self.supports_streaming_check.isChecked(),
        )

    def _validate_input(self) -> bool:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return False
        if not self.model_combo.currentText().strip():
            QMessageBox.warning(self, "Validation Error", "Model is required")
            return False
        if not self.api_key_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "API Key is required")
            return False
        return True


class SettingsView(QWidget):
    """View for application settings management."""

    def __init__(self, viewmodel: SettingsViewModel, parent: QWidget | None = None):
        super().__init__(parent)
        self._view_model = viewmodel
        self._init_ui()
        self._connect_signals()
        self._view_model.load_settings()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self._create_provider_section())
        layout.addWidget(self._create_general_section())

    def _create_provider_section(self) -> QGroupBox:
        group = QGroupBox("Provider Management")
        layout = QVBoxLayout()

        self.provider_list = QListWidget()  # type: ignore[reportUninitializedInstanceVariable]
        layout.addWidget(self.provider_list)

        button_layout = self._create_provider_buttons()
        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def _create_provider_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        self.add_btn = QPushButton("Add")  # type: ignore[reportUninitializedInstanceVariable]
        self.edit_btn = QPushButton("Edit")  # type: ignore[reportUninitializedInstanceVariable]
        self.delete_btn = QPushButton("Delete")  # type: ignore[reportUninitializedInstanceVariable]
        self.set_default_btn = QPushButton("Set as Default")  # type: ignore[reportUninitializedInstanceVariable]

        self.add_btn.clicked.connect(self._on_add_provider)
        self.edit_btn.clicked.connect(self._on_edit_provider)
        self.delete_btn.clicked.connect(self._on_delete_provider)
        self.set_default_btn.clicked.connect(self._on_set_default)

        layout.addWidget(self.add_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.set_default_btn)

        return layout

    def _create_general_section(self) -> QGroupBox:
        group = QGroupBox("General Settings")
        layout = QFormLayout()

        self._language_combo = LanguageCombo(self)  # type: ignore[reportUninitializedInstanceVariable]
        self._language_combo.add_languages(ls.get_languages(with_auto_detect=False))
        self._language_combo.currentIndexChanged.connect(self._on_target_language_changed)

        layout.addRow("Target Language:", self._language_combo)
        group.setLayout(layout)
        return group

    def _on_target_language_changed(self) -> None:
        """Handle target language selection change."""
        language = self._language_combo.current_language()
        if language:
            self._view_model.update_target_language(language.code)

    def _connect_signals(self) -> None:
        self._view_model.settings_loaded.connect(self._on_settings_loaded)
        self._view_model.settings_saved.connect(self._on_settings_saved)
        self._view_model.provider_added.connect(self._on_provider_added)
        self._view_model.provider_updated.connect(self._on_provider_updated)
        self._view_model.provider_deleted.connect(self._on_provider_deleted)
        self._view_model.default_provider_changed.connect(self._refresh_provider_list)
        self._view_model.error_occurred.connect(self._on_error)

    def _on_settings_loaded(self) -> None:
        self._refresh_provider_list()
        self._language_combo.set_language(self._view_model.target_language)

    def _on_settings_saved(self) -> None:
        """Settings saved - auto-save, no user notification needed."""
        pass

    def _on_provider_added(self, _: ProviderConfig) -> None:
        self._refresh_provider_list()

    def _on_provider_updated(self, _: int) -> None:
        self._refresh_provider_list()

    def _on_provider_deleted(self, _: int) -> None:
        self._refresh_provider_list()

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def _refresh_provider_list(self) -> None:
        self.provider_list.clear()
        for provider in self._view_model.providers:
            self._add_provider_item(provider)

    def _add_provider_item(self, provider: ProviderConfig) -> None:
        default_marker = " [DEFAULT]" if provider.is_default else ""
        text = f"{provider.name} ({provider.provider_type}/{provider.model}){default_marker}"
        item = QListWidgetItem(text)
        self.provider_list.addItem(item)

    def _on_add_provider(self) -> None:
        dialog = ProviderDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            provider = dialog.get_provider()
            if provider:
                self._view_model.add_provider(provider)

    def _on_edit_provider(self) -> None:
        index = self._get_selected_index()
        if index is None:
            return

        provider = self._view_model.providers[index]
        dialog = ProviderDialog(provider, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_metadata = dialog.get_provider()
        if not updated_metadata:
            return
        self._view_model.update_provider(index, updated_metadata)

    def _on_delete_provider(self) -> None:
        index = self._get_selected_index()
        if index is None:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this provider?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.delete_provider(index)

    def _on_set_default(self) -> None:
        index = self._get_selected_index()
        if index is not None:
            self._view_model.set_default_provider(index)

    def _get_selected_index(self) -> int | None:
        current = self.provider_list.currentRow()
        if current < 0:
            QMessageBox.warning(self, "No Selection", "Please select a provider")
            return None
        return current
