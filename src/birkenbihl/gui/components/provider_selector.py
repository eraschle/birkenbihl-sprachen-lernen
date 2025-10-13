"""Provider selector component for choosing AI providers."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox

from birkenbihl.gui.models.context import ProviderSelectorContext
from birkenbihl.gui.styles import theme
from birkenbihl.models.settings import ProviderConfig


class ProviderSelector(QComboBox):
    """Dropdown for selecting AI translation provider.

    Emits provider_changed signal when user selects a different provider.
    Displays provider name and model in format: "Provider Name (model-name)".
    """

    provider_changed = Signal(ProviderConfig)

    def __init__(self, context: ProviderSelectorContext):
        super().__init__()
        self._providers = context.providers
        self.setStyleSheet(theme.get_default_combobox_style())
        self._populate_providers()
        self._set_default_provider(context.default_provider)
        self.setEnabled(not context.disabled)
        self.currentIndexChanged.connect(self._on_selection_changed)

    def _populate_providers(self) -> None:
        """Add all providers to dropdown with name and model."""
        for provider in self._providers:
            display_text = self._format_provider_display(provider)
            self.addItem(display_text, userData=provider)

    def _format_provider_display(self, provider: ProviderConfig) -> str:
        """Format provider display text."""
        return f"{provider.name} ({provider.model})"

    def _set_default_provider(self, default: ProviderConfig | None) -> None:
        """Select the default provider if provided."""
        if default is None:
            return

        for index in range(self.count()):
            if self.itemData(index) == default:
                self.setCurrentIndex(index)
                break

    def _on_selection_changed(self, index: int) -> None:
        """Emit signal when provider selection changes."""
        if index >= 0:
            provider = self.itemData(index)
            self.provider_changed.emit(provider)

    def get_selected_provider(self) -> ProviderConfig | None:
        """Get currently selected provider."""
        index = self.currentIndex()
        return self.itemData(index) if index >= 0 else None
