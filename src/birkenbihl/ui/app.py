"""Streamlit UI for the Birkenbihl application.

This module provides a web-based graphical interface using Streamlit,
with tabs for translation and settings management.
"""

import streamlit as st

from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.settings import render_settings_tab
from birkenbihl.ui.translation import render_translation_tab
from birkenbihl.ui.manage_translations import render_manage_translations_tab
from birkenbihl.ui.edit_translation import render_edit_translation_tab


def configure_page() -> None:
    """Configure Streamlit page settings and styling."""
    st.set_page_config(
        page_title="Birkenbihl Sprachlernmethode",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Reduce top padding/margin
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 3rem;
            padding-bottom: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
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
    if "show_edit_provider_form" not in st.session_state:
        st.session_state.show_edit_provider_form = False
    if "edit_provider_index" not in st.session_state:
        st.session_state.edit_provider_index = None
    if "current_view" not in st.session_state:
        st.session_state.current_view = "Übersetzen"
    if "selected_translation_id" not in st.session_state:
        st.session_state.selected_translation_id = None
    if "selected_sentence_uuid" not in st.session_state:
        st.session_state.selected_sentence_uuid = None
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = None
    if "suggestions_cache" not in st.session_state:
        st.session_state.suggestions_cache = {}


def main() -> None:
    """Main entry point for Streamlit app."""
    configure_page()
    initialize_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")

        if st.button(
            "📝 Übersetzen",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "Übersetzen" else "secondary",
        ):
            st.session_state.current_view = "Übersetzen"
            st.rerun()

        if st.button(
            "📋 Meine Übersetzungen",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "Meine Übersetzungen" else "secondary",
        ):
            st.session_state.current_view = "Meine Übersetzungen"
            st.rerun()

        if st.button(
            "⚙️ Einstellungen",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "Einstellungen" else "secondary",
        ):
            st.session_state.current_view = "Einstellungen"
            st.rerun()

    # Render current view
    if st.session_state.current_view == "Übersetzen":
        render_translation_tab()
    elif st.session_state.current_view == "Meine Übersetzungen":
        render_manage_translations_tab()
    elif st.session_state.current_view == "Übersetzung bearbeiten":
        render_edit_translation_tab()
    else:
        render_settings_tab()


if __name__ == "__main__":
    main()
