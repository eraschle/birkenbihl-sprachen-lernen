"""SettingsView for application settings UI."""

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from birkenbihl.gui.viewmodels.settings_vm import SettingsViewModel
from birkenbihl.models.settings import ProviderConfig


class ProviderDialog(QDialog):
    """Dialog for adding or editing provider configuration."""

    def __init__(self, provider: ProviderConfig | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Provider" if provider is None else "Edit Provider")
        self._provider = provider
        self._init_ui()
        if provider:
            self._populate_fields()

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        self._create_form_fields()
        self._add_fields_to_layout(layout)
        self._add_buttons(layout)

    def _create_form_fields(self) -> None:
        self.name_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.type_combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.type_combo.addItems(["openai", "anthropic", "google-genai", "groq"])
        self.model_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.api_key_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.base_url_edit = QLineEdit()  # type: ignore[reportUninitializedInstanceVariable]
        self.is_default_check = QCheckBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.supports_streaming_check = QCheckBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.supports_streaming_check.setChecked(True)

    def _add_fields_to_layout(self, layout: QFormLayout) -> None:
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Provider Type:", self.type_combo)
        layout.addRow("Model:", self.model_edit)
        layout.addRow("API Key:", self.api_key_edit)
        layout.addRow("Base URL:", self.base_url_edit)
        layout.addRow("Set as Default:", self.is_default_check)
        layout.addRow("Supports Streaming:", self.supports_streaming_check)

    def _add_buttons(self, layout: QFormLayout) -> None:
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate_fields(self) -> None:
        if not self._provider:
            return
        self.name_edit.setText(self._provider.name)
        self.type_combo.setCurrentText(self._provider.provider_type)
        self.model_edit.setText(self._provider.model)
        self.api_key_edit.setText(self._provider.api_key)
        self.base_url_edit.setText(self._provider.base_url or "")
        self.is_default_check.setChecked(self._provider.is_default)
        self.supports_streaming_check.setChecked(self._provider.supports_streaming)

    def get_provider(self) -> ProviderConfig | None:
        if not self._validate_input():
            return None

        return ProviderConfig(
            name=self.name_edit.text().strip(),
            provider_type=self.type_combo.currentText(),
            model=self.model_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            base_url=self.base_url_edit.text().strip() or None,
            is_default=self.is_default_check.isChecked(),
            supports_streaming=self.supports_streaming_check.isChecked(),
        )

    def _validate_input(self) -> bool:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Name is required")
            return False
        if not self.model_edit.text().strip():
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
        self._vm = viewmodel
        self._init_ui()
        self._connect_signals()
        self._vm.load_settings()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self._create_provider_section())
        layout.addWidget(self._create_general_section())
        layout.addWidget(self._create_save_button())

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

        self.language_combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self.language_combo.addItems(["de", "en", "es"])
        self.language_combo.currentTextChanged.connect(self._vm.update_target_language)

        layout.addRow("Target Language:", self.language_combo)
        group.setLayout(layout)
        return group

    def _create_save_button(self) -> QPushButton:
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._vm.save_settings)
        return save_btn

    def _connect_signals(self) -> None:
        self._vm.settings_loaded.connect(self._on_settings_loaded)
        self._vm.settings_saved.connect(self._on_settings_saved)
        self._vm.provider_added.connect(self._on_provider_added)
        self._vm.provider_updated.connect(self._on_provider_updated)
        self._vm.provider_deleted.connect(self._on_provider_deleted)
        self._vm.default_provider_changed.connect(self._refresh_provider_list)
        self._vm.error_occurred.connect(self._on_error)

    def _on_settings_loaded(self) -> None:
        self._refresh_provider_list()
        self.language_combo.setCurrentText(self._vm.target_language)

    def _on_settings_saved(self) -> None:
        QMessageBox.information(self, "Success", "Settings saved successfully")

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
        for provider in self._vm.providers:
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
                self._vm.add_provider(provider)

    def _on_edit_provider(self) -> None:
        index = self._get_selected_index()
        if index is None:
            return

        provider = self._vm.providers[index]
        dialog = ProviderDialog(provider, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_provider()
            if updated:
                self._vm.update_provider(index, updated)

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
            self._vm.delete_provider(index)

    def _on_set_default(self) -> None:
        index = self._get_selected_index()
        if index is not None:
            self._vm.set_default_provider(index)

    def _get_selected_index(self) -> int | None:
        current = self.provider_list.currentRow()
        if current < 0:
            QMessageBox.warning(self, "No Selection", "Please select a provider")
            return None
        return current
