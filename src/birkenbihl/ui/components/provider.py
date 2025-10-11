"""Provider selection component.

Eliminates duplicated provider selection code across multiple UI modules.
"""

import streamlit as st

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.models.context import ProviderSelectorContext


class ProviderSelector:
    """Provider selection dropdown component.

    Replaces duplicated provider selection code from:
    - translation.py:103-131
    - translation_result.py:234-248
    - edit_translation.py:130-144

    Single Responsibility: Only provider selection, no business logic.
    """

    def __init__(self, context: ProviderSelectorContext) -> None:
        """Initialize provider selector.

        Args:
            context: ProviderSelectorContext with providers and configuration
        """
        self.context = context

    def render(self) -> ProviderConfig | None:
        """Render provider selection dropdown.

        Returns:
            Selected ProviderConfig or None if no providers available
        """
        if not self.context.providers:
            st.warning("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
            return None

        return self._render_provider_dropdown()

    def _render_provider_dropdown(self) -> ProviderConfig:
        """Render the provider dropdown and return selected provider.

        Returns:
            Selected ProviderConfig
        """
        provider_names = self._get_provider_names()
        default_index = self._get_default_index()

        selected_provider_name = st.selectbox(
            "Provider wählen",
            options=provider_names,
            index=default_index,
            key=self._generate_key(),
            disabled=self.context.disabled,
        )

        return self._find_provider_by_name(selected_provider_name)

    def _get_provider_names(self) -> list[str]:
        """Get list of provider names.

        Returns:
            List of provider name strings
        """
        return [p.name for p in self.context.providers]

    def _get_default_index(self) -> int:
        """Get default selection index based on current provider.

        Returns:
            Index of default provider or 0
        """
        if not self.context.default_provider:
            return 0

        for idx, provider in enumerate(self.context.providers):
            if provider.name == self.context.default_provider.name:
                return idx

        return 0

    def _generate_key(self) -> str:
        """Generate unique key for selectbox.

        Returns:
            Unique key string
        """
        if self.context.key_suffix:
            return f"provider_select_{self.context.key_suffix}"
        return "provider_select"

    def _find_provider_by_name(self, name: str) -> ProviderConfig:
        """Find provider by name.

        Args:
            name: Provider name to find

        Returns:
            ProviderConfig matching the name
        """
        return next(p for p in self.context.providers if p.name == name)


def get_providers_from_settings() -> list[ProviderConfig]:
    """Get providers from session state settings.

    Helper function to retrieve providers for ProviderSelectorContext.

    Returns:
        List of configured providers
    """
    return st.session_state.settings.providers


def get_current_provider() -> ProviderConfig | None:
    """Get current default provider.

    Helper function to retrieve default provider for ProviderSelectorContext.

    Returns:
        Current default provider or None
    """
    return SettingsService.get_current_provider()
