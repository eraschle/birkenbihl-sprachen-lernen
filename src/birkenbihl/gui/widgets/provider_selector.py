"""Provider selection widget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from birkenbihl.gui.styles import theme
from birkenbihl.models.settings import ProviderConfig


class ProviderSelector(QWidget):
    """Provider selection dropdown widget.

    Displays available providers with name and model.
    Emits signal when provider is selected.
    Highlights default provider.
    """

    provider_selected = Signal(object)  # ProviderConfig

    def __init__(self, providers: list[ProviderConfig], parent: QWidget | None = None):
        """Initialize widget.

        Args:
            providers: List of available providers
            parent: Parent widget
        """
        super().__init__(parent)
        self._providers = providers
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Provider:")
        self._combo = QComboBox()  # type: ignore[reportUninitializedInstanceVariable]
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        self._combo.setStyleSheet(theme.get_default_combobox_style())

        layout.addWidget(label)
        layout.addWidget(self._combo)

        self._populate_combo()

    def _populate_combo(self) -> None:
        """Populate combo box with providers."""
        self._combo.clear()

        for provider in self._providers:
            display_text = self._format_provider_text(provider)
            self._combo.addItem(display_text)

    def _format_provider_text(self, provider: ProviderConfig) -> str:
        """Format provider display text.

        Args:
            provider: Provider config

        Returns:
            Formatted text (e.g., "OpenAI - gpt-4 [default]")
        """
        text = provider.name
        if provider.is_default:
            text += " [default]"
        return text

    def _on_selection_changed(self, index: int) -> None:
        """Handle selection change.

        Args:
            index: Selected index
        """
        if 0 <= index < len(self._providers):
            self.provider_selected.emit(self._providers[index])

    def update_data(self, providers: list[ProviderConfig]) -> None:
        """Update providers list.

        Args:
            providers: New providers list
        """
        self._providers = providers
        self._populate_combo()

    def get_selected_provider(self) -> ProviderConfig | None:
        """Get currently selected provider.

        Returns:
            Selected provider or None
        """
        index = self._combo.currentIndex()
        if 0 <= index < len(self._providers):
            return self._providers[index]
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable widget.

        Args:
            enabled: Enable state
        """
        self._combo.setEnabled(enabled)
