"""Streamlit UI for the Birkenbihl application.

This module provides a web-based graphical interface using Streamlit,
with tabs for translation and settings management.
"""

import logging
import sys

import streamlit as st

from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.settings import render_settings_tab
from birkenbihl.ui.translation import render_translation_tab
from birkenbihl.ui.manage_translations import render_manage_translations_tab
from birkenbihl.ui.translation_result import render_translation_result_tab


def configure_logging() -> None:
    """Configure logging for the application.

    Sets up logging to stdout with timestamps and appropriate levels.
    Only runs once per session.
    """
    # Use session state to track if logging is configured (survives reruns)
    if "logging_configured" not in st.session_state:
        st.session_state.logging_configured = False

    # Skip if already configured (Streamlit reruns)
    if st.session_state.logging_configured:
        return

    # Create formatter with timestamps
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Only add handler if none exist
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    # Set specific levels for birkenbihl modules
    birkenbihl_logger = logging.getLogger("birkenbihl")
    birkenbihl_logger.setLevel(logging.INFO)
    birkenbihl_logger.propagate = True

    logging.getLogger("birkenbihl.providers").setLevel(logging.DEBUG)
    logging.getLogger("birkenbihl.ui").setLevel(logging.INFO)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("streamlit").setLevel(logging.WARNING)

    st.session_state.logging_configured = True
    logging.info("Logging configured successfully")


logger = logging.getLogger(__name__)


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
    if "is_new_translation" not in st.session_state:
        st.session_state.is_new_translation = False
    if "detected_language_info" not in st.session_state:
        st.session_state.detected_language_info = None
    if "is_translating" not in st.session_state:
        st.session_state.is_translating = False
    if "translation_pending" not in st.session_state:
        st.session_state.translation_pending = None


def main() -> None:
    """Main entry point for Streamlit app."""
    # Configure logging first (uses session state, so must be after Streamlit init)
    configure_logging()

    configure_page()
    initialize_session_state()

    # Log app start only once (not on every rerun)
    if "app_started_logged" not in st.session_state:
        logger.info("=" * 60)
        logger.info("Birkenbihl App started")
        logger.info("=" * 60)

        # Log current settings
        num_providers = len(st.session_state.settings.providers)
        logger.info("App initialized: %d provider(s) configured", num_providers)
        if num_providers > 0:
            default_provider = st.session_state.settings.get_default_provider()
            if default_provider:
                logger.info("Default provider: %s (%s)", default_provider.name, default_provider.provider_type)

        st.session_state.app_started_logged = True

    # Sidebar navigation (disable during translation)
    is_translating = st.session_state.get("is_translating", False)

    with st.sidebar:
        st.markdown("## Navigation")

        if st.button(
            "📝 Übersetzen",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "Übersetzen" else "secondary",
            disabled=is_translating,
        ):
            st.session_state.current_view = "Übersetzen"
            st.rerun()

        if st.button(
            "📋 Meine Übersetzungen",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "Meine Übersetzungen" else "secondary",
            disabled=is_translating,
        ):
            st.session_state.current_view = "Meine Übersetzungen"
            st.rerun()

        if st.button(
            "⚙️ Einstellungen",
            use_container_width=True,
            type="primary" if st.session_state.current_view == "Einstellungen" else "secondary",
            disabled=is_translating,
        ):
            st.session_state.current_view = "Einstellungen"
            st.rerun()

    # Render current view
    if st.session_state.current_view == "Übersetzen":
        render_translation_tab()
    elif st.session_state.current_view == "Meine Übersetzungen":
        render_manage_translations_tab()
    elif st.session_state.current_view == "Übersetzungsergebnis":
        render_translation_result_tab()
    elif st.session_state.current_view == "Übersetzung bearbeiten":
        render_translation_result_tab()  # Use the same view for editing
    else:
        render_settings_tab()


if __name__ == "__main__":
    main()
