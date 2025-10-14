"""Translation tab UI for the Birkenbihl application."""

import logging

import streamlit as st

from birkenbihl.models import languages
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.components import ProviderSelector
from birkenbihl.ui.models.context import ProviderSelectorContext

logger = logging.getLogger(__name__)


def render_translation_tab() -> None:
    """Render the translation tab with input and results."""
    # Initialize session state for uploaded text content
    if "uploaded_text_content" not in st.session_state:
        st.session_state.uploaded_text_content = ""
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None
    if "is_translating" not in st.session_state:
        st.session_state.is_translating = False

    # Check if translation is in progress
    is_translating = st.session_state.is_translating

    col1, col2 = st.columns([3, 1])

    with col1:
        title_input = st.text_input(
            "Titel *",
            placeholder="Geben Sie einen Titel für die Übersetzung ein",
            help="Ein beschreibender Titel für diese Übersetzung",
        )

        text_input = st.text_area(
            "Text eingeben",
            value=st.session_state.uploaded_text_content,
            height=600,
            placeholder="Geben Sie hier den zu übersetzenden Text ein...",
            help="Geben Sie einen Text in einer beliebigen Sprache ein",
        )

    with col2:
        st.markdown("**Einstellungen**")

        # File upload (disabled during translation)
        uploaded_file = st.file_uploader(
            "📁 Datei hochladen",
            type=["txt", "md"],
            help="Laden Sie eine Textdatei (.txt, .md), um ihren Inhalt ins Eingabefeld zu übernehmen",
            disabled=is_translating,
        )

        if uploaded_file is not None:
            # Only process if it's a new file (avoid re-logging on rerun)
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.last_uploaded_file != file_id:
                # Read file content
                content = uploaded_file.read().decode("utf-8")
                st.session_state.uploaded_text_content = content
                st.session_state.last_uploaded_file = file_id
                logger.info("File uploaded: %s (%d characters)", uploaded_file.name, len(content))
                st.success(f"✓ Datei '{uploaded_file.name}' geladen ({len(content)} Zeichen)")
                st.rerun()

        # Clear button to reset the text area (disabled during translation)
        if st.session_state.uploaded_text_content:
            if st.button("🗑️ Text löschen", use_container_width=True, disabled=is_translating):
                st.session_state.uploaded_text_content = ""
                st.session_state.last_uploaded_file = None
                logger.info("Text cleared by user")
                st.rerun()

        st.markdown("---")

        # Source language options: "Automatisch" + all languages (disabled during translation)
        source_lang_options = ["Automatisch"] + languages.get_german_names()
        language_detection = st.selectbox(
            "Quellsprache",
            options=source_lang_options,
            index=0,
            help="Wählen Sie die Ausgangssprache oder 'Automatisch' für auto-detect",
            disabled=is_translating,
        )

        # Target language options: all languages, default to German (disabled during translation)
        target_lang_options = languages.get_german_names()
        try:
            default_target_lang = languages.get_german_name(st.session_state.settings.target_language)
        except KeyError:
            default_target_lang = "Deutsch"
        default_target_index = target_lang_options.index(default_target_lang)

        target_lang = st.selectbox(
            "Zielsprache",
            options=target_lang_options,
            index=default_target_index,
            help="Wählen Sie die Zielsprache",
            disabled=is_translating,
        )

        # Provider selection using ProviderSelector component
        selector_context = ProviderSelectorContext(
            providers=st.session_state.settings.providers,
            default_provider=SettingsService.get_current_provider(),
            disabled=is_translating,
            key_suffix="translation",
        )
        provider_selector = ProviderSelector(selector_context)
        selected_provider = provider_selector.render()

        st.markdown("")  # Small spacing

        # Streaming option based on provider settings
        if selected_provider:
            streaming_enabled = selected_provider.supports_streaming
            streaming_help = (
                "Zeigt Fortschritt während der Übersetzung an (empfohlen für lange Texte)"
                if streaming_enabled
                else "Dieser Provider unterstützt kein Streaming"
            )
        else:
            streaming_enabled = False
            streaming_help = "Kein Provider ausgewählt"

        use_streaming = st.checkbox(
            "Streaming aktivieren",
            value=streaming_enabled,
            disabled=not streaming_enabled or is_translating,
            help=streaming_help,
        )

        # Show translation status
        if is_translating:
            st.info("⏳ Übersetzung läuft...")

        translate_button = st.button(
            "🔄 Übersetzen",
            type="primary",
            use_container_width=True,
            disabled=is_translating,
        )

    if translate_button:
        logger.info("Translation button clicked")
        if not title_input.strip():
            logger.warning("Translation aborted: No title provided")
            st.error("Bitte geben Sie einen Titel ein.")
        elif not text_input.strip():
            logger.warning("Translation aborted: No text provided")
            st.error("Bitte geben Sie einen Text ein.")
        else:
            # Store translation parameters and trigger translation on next rerun
            st.session_state.translation_pending = {
                "text": text_input,
                "title": title_input,
                "source_language": language_detection,
                "target_language": target_lang,
                "use_streaming": use_streaming,
                "provider": selected_provider,
            }
            st.session_state.is_translating = True
            # Navigate to result view immediately to show progress
            st.session_state.current_view = "Übersetzungsergebnis"
            st.rerun()
