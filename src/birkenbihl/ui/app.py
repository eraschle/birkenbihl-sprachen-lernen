"""Streamlit UI for the Birkenbihl application.

This module provides a web-based graphical interface using Streamlit,
with tabs for translation and settings management.
"""

import streamlit as st

from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.settings import render_settings_tab
from birkenbihl.ui.translation import render_translation_tab


def configure_page() -> None:
    """Configure Streamlit page settings and styling."""
    st.set_page_config(
        page_title="Birkenbihl Sprachlernmethode",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown("### 📚 Birkenbihl Sprachlernmethode")
    st.caption("Dekodieren Sie Texte nach der Vera F. Birkenbihl Methode")


def initialize_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    if "settings" not in st.session_state:
        st.session_state.settings = SettingsService.get_settings()
    if "translation_result" not in st.session_state:
        st.session_state.translation_result = None
    if "show_add_provider_form" not in st.session_state:
        st.session_state.show_add_provider_form = False


def main() -> None:
    """Main entry point for Streamlit app."""
    configure_page()
    initialize_session_state()

    tab1, tab2 = st.tabs(["Übersetzen", "Einstellungen"])

    with tab1:
        render_translation_tab()

    with tab2:
        render_settings_tab()


if __name__ == "__main__":
    main()
