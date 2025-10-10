"""Translation tab UI for the Birkenbihl application."""

import asyncio
import html
import logging

import streamlit as st
from pydantic import BaseModel

from birkenbihl.models import languages
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class TranslationModel(BaseModel):
    text: str
    title: str
    source_language: str
    target_language: str


def render_translation_tab() -> None:
    """Render the translation tab with input and results."""
    # Initialize session state for uploaded text content
    if "uploaded_text_content" not in st.session_state:
        st.session_state.uploaded_text_content = ""
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

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

        # File upload
        uploaded_file = st.file_uploader(
            "📁 Datei hochladen",
            type=["txt", "md"],
            help="Laden Sie eine Textdatei (.txt, .md), um ihren Inhalt ins Eingabefeld zu übernehmen",
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

        # Clear button to reset the text area
        if st.session_state.uploaded_text_content:
            if st.button("🗑️ Text löschen", use_container_width=True):
                st.session_state.uploaded_text_content = ""
                st.session_state.last_uploaded_file = None
                logger.info("Text cleared by user")
                st.rerun()

        st.markdown("---")

        # Source language options: "Automatisch" + all languages
        source_lang_options = ["Automatisch"] + languages.get_german_names()
        language_detection = st.selectbox(
            "Quellsprache",
            options=source_lang_options,
            index=0,
            help="Wählen Sie die Ausgangssprache oder 'Automatisch' für auto-detect",
        )

        # Target language options: all languages, default to German
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
        )

        # Provider selection (single dropdown with all configured providers)
        providers = st.session_state.settings.providers
        if providers:
            # Create display names for all providers
            provider_display_names = [f"{p.name}" for p in providers]

            # Get current provider for default selection
            current_provider = SettingsService.get_current_provider()
            default_index = 0
            if current_provider:
                for idx, provider in enumerate(providers):
                    if provider.name == current_provider.name:
                        default_index = idx
                        break

            # Select provider
            sel_provider_display = st.selectbox(
                "Provider",
                options=provider_display_names,
                index=default_index,
                help="Wählen Sie den Provider für die Übersetzung",
            )

            # Get the selected provider
            selected_provider_index = provider_display_names.index(sel_provider_display)
            selected_provider = providers[selected_provider_index]
        else:
            selected_provider = None
            st.warning("⚠️ Kein Provider konfiguriert")

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
            disabled=not streaming_enabled,
            help=streaming_help,
        )

        translate_button = st.button(
            "🔄 Übersetzen",
            type="primary",
            use_container_width=True,
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
            model = TranslationModel(
                text=text_input,
                title=title_input,
                source_language=language_detection,
                target_language=target_lang,
            )
            logger.info(
                "Translation initiated: title='%s', text_length=%d chars, source=%s, target=%s, streaming=%s",
                title_input[:50],
                len(text_input),
                language_detection,
                target_lang,
                use_streaming,
            )
            if use_streaming:
                # Use streaming mode with progress bar
                logger.info("Using streaming mode")
                try:
                    asyncio.run(translate_text_streaming(model, selected_provider))
                except Exception as stream_error:
                    # Fallback to sync mode if streaming fails
                    logger.error("Streaming failed: %s", str(stream_error), exc_info=True)
                    st.warning(f"Streaming fehlgeschlagen: {str(stream_error)}")
                    st.info("Verwende Standardmodus ohne Fortschrittsanzeige...")
                    translate_text(model, selected_provider)
            else:
                # Use traditional sync mode
                logger.info("Using sync mode")
                translate_text(model, selected_provider)

    if st.session_state.translation_result:
        render_translation_results()


def translate_text(model: TranslationModel, provider: ProviderConfig | None) -> None:
    """Translate text using configured provider.

    Args:
        text: Input text to translate
        title: Title for the translation
        source_lang_option: Source language selection
        target_lang_option: Target language selection
        provider: Provider configuration to use for translation
    """
    if not provider:
        logger.warning("Translation attempted with no provider configured")
        st.error("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
        return

    # Convert language display names back to ISO codes
    # Handle "Automatisch" for source language
    if model.source_language == "Automatisch":
        source_lang = "auto"
    else:
        try:
            source_lang = languages.get_language_code_by(model.source_language)
        except KeyError:
            logger.warning("Unknown source language: %s, defaulting to 'en'", model.source_language)
            source_lang = "en"

    # Target language must be a valid language (no "auto")
    try:
        target_lang = languages.get_language_code_by(model.target_language)
    except KeyError:
        logger.warning("Unknown target language: %s, defaulting to 'de'", model.target_language)
        target_lang = "de"

    logger.info("UI: Starting translation - provider=%s, source=%s, target=%s, title='%s'",
                provider.name, source_lang, target_lang, model.title)

    try:
        with st.spinner(f"Übersetze Text mit {provider.name}..."):
            translator = PydanticAITranslator(provider)

            if source_lang == "auto":
                detected_lang = translator.detect_language(model.text)
                st.info(f"Erkannte Sprache: {detected_lang.upper()}")
                source_lang = detected_lang

            translation = translator.translate(model.text, source_lang, target_lang)
            translation.title = model.title
            st.session_state.translation_result = translation

        logger.info("UI: Translation successful - %d sentences", len(translation.sentences))
        st.success(f"Übersetzung erfolgreich mit {provider.name}!")

    except Exception as e:
        logger.error("UI: Translation failed - %s: %s", type(e).__name__, str(e), exc_info=True)
        st.error(f"Fehler bei der Übersetzung: {str(e)}")
        st.info("Bitte überprüfen Sie:\n- API-Schlüssel ist korrekt\n- Modellname ist gültig\n- Internetverbindung")


async def translate_text_streaming(model: TranslationModel, provider: ProviderConfig | None) -> None:
    """Translate text using streaming with progress bar.

    Args:
        text: Input text to translate
        title: Title for the translation
        source_lang_option: Source language selection
        target_lang_option: Target language selection
        provider: Provider configuration to use for translation
    """
    logger.info("Streaming function started")
    if not provider:
        logger.warning("Streaming: No provider configured")
        st.error("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
        return

    # Convert language display names back to ISO codes
    # Handle "Automatisch" for source language
    if model.source_language == "Automatisch":
        source_lang = "auto"
    else:
        try:
            source_lang = languages.get_language_code_by(model.source_language)
        except KeyError:
            logger.warning("Streaming: Unknown source language %s", model.source_language)
            source_lang = "en"

    # Target language must be a valid language (no "auto")
    try:
        target_lang = languages.get_language_code_by(model.target_language)
    except KeyError:
        logger.warning("Streaming: Unknown target language %s", model.target_language)
        target_lang = "de"

    try:
        logger.info("Streaming: Creating translator")
        translator = PydanticAITranslator(provider)

        # Handle language detection if needed
        if source_lang == "auto":
            logger.info("Streaming: Detecting language")
            detected_lang = translator.detect_language(model.text)
            st.info(f"Erkannte Sprache: {detected_lang.upper()}")
            source_lang = detected_lang

        # Create progress bar
        logger.info("Streaming: Creating progress bar")
        progress_bar = st.progress(0.0, text="Starte Übersetzung...")

        # Stream translation with progress updates
        logger.info("Streaming: Starting translation stream")
        translations = translator.translate_stream(model.text, source_lang, target_lang)
        logger.info("Streaming: Entering async loop")
        async for progress, translation in translations:
            if translation:
                logger.debug("Streaming: Progress update %.0f%%", progress * 100)
                # Update progress bar
                progress_bar.progress(progress, text=f"Übersetze: {int(progress * 100)}%")

                # Store partial result (will be overwritten with final result)
                translation.title = model.title
                st.session_state.translation_result = translation

        # Clear progress bar
        logger.info("Streaming: Translation complete, clearing progress bar")
        progress_bar.empty()
        logger.info("Streaming: UI Translation successful - %d sentences", len(translation.sentences) if translation else 0)
        st.success(f"Übersetzung erfolgreich mit {provider.name}!")

    except Exception as e:
        logger.error("Streaming: Translation failed - %s: %s", type(e).__name__, str(e), exc_info=True)
        st.error(f"Fehler bei der Übersetzung: {str(e)}")
        st.info("Bitte überprüfen Sie:\n- API-Schlüssel ist korrekt\n- Modellname ist gültig\n- Internetverbindung")


def _create_translation_message(translation: Translation) -> str:
    message = f"**{translation.title}** | "
    message += f"{translation.source_language.upper()} → {translation.target_language.upper()} | "
    message += f"{len(translation.sentences)} Sätze"
    return message


def render_translation_results() -> None:
    """Render translation results with formatting."""
    translation = st.session_state.translation_result

    st.markdown("---")
    st.markdown(_create_translation_message(translation))

    for i, sentence in enumerate(translation.sentences, 1):
        # Only expand first sentence, collapse others for compact view
        with st.expander(f"Satz {i}: {sentence.source_text[:50]}...", expanded=(i == 1)):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Original:**")
                st.info(sentence.source_text)

            with col2:
                st.markdown("**Natürliche Übersetzung:**")
                st.success(sentence.natural_translation)

            st.markdown("**Wort-für-Wort Dekodierung:**")

            alignment_html = "<div style='font-size: 13px; line-height: 1.8;'>"
            for alignment in sentence.word_alignments:
                source_escaped = html.escape(alignment.source_word)
                target_escaped = html.escape(alignment.target_word)
                alignment_html += (
                    f"<span style='display: inline-block; margin: 2px; padding: 4px 8px; "
                    f"background-color: #f0f2f6; border-radius: 6px; border: 1px solid #ddd;'>"
                    f"<div style='color: #0066cc; font-weight: 600; font-size: 12px;'>{source_escaped}</div>"
                    f"<div style='color: #666; font-size: 10px;'>↓</div>"
                    f"<div style='color: #009900; font-weight: 600; font-size: 12px;'>{target_escaped}</div>"
                    f"</span>"
                )
            alignment_html += "</div>"

            st.markdown(alignment_html, unsafe_allow_html=True)
