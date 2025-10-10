"""Translation tab UI for the Birkenbihl application."""

import html

import streamlit as st

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.constants import LANGUAGES


def render_translation_tab() -> None:
    """Render the translation tab with input and results."""
    col1, col2 = st.columns([3, 1])

    with col1:
        text_input = st.text_area(
            "Text eingeben",
            height=600,
            placeholder="Geben Sie hier den zu übersetzenden Text ein...",
            help="Geben Sie einen Text in einer beliebigen Sprache ein",
        )

    with col2:
        st.markdown("**Einstellungen**")

        # Source language options: "Automatisch" + all languages
        source_lang_options = ["Automatisch"] + list(LANGUAGES.values())
        language_detection = st.selectbox(
            "Quellsprache",
            options=source_lang_options,
            index=0,
            help="Wählen Sie die Ausgangssprache oder 'Automatisch' für auto-detect",
        )

        # Target language options: all languages, default to German
        target_lang_options = list(LANGUAGES.values())
        default_target_lang = LANGUAGES.get(
            st.session_state.settings.target_language, "Deutsch"
        )
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
                for i, p in enumerate(providers):
                    if p.name == current_provider.name:
                        default_index = i
                        break

            # Select provider
            selected_provider_display = st.selectbox(
                "Provider",
                options=provider_display_names,
                index=default_index,
                help="Wählen Sie den Provider für die Übersetzung",
            )

            # Get the selected provider
            selected_provider_index = provider_display_names.index(selected_provider_display)
            selected_provider = providers[selected_provider_index]
        else:
            selected_provider = None
            st.warning("⚠️ Kein Provider konfiguriert")

        st.markdown("")  # Small spacing
        translate_button = st.button(
            "🔄 Übersetzen",
            type="primary",
            use_container_width=True,
        )

    if translate_button:
        if not text_input.strip():
            st.error("Bitte geben Sie einen Text ein.")
        else:
            translate_text(text_input, language_detection, target_lang, selected_provider)

    if st.session_state.translation_result:
        render_translation_results()


def translate_text(
    text: str, source_lang_option: str, target_lang_option: str, provider: ProviderConfig | None
) -> None:
    """Translate text using configured provider.

    Args:
        text: Input text to translate
        source_lang_option: Source language selection
        target_lang_option: Target language selection
        provider: Provider configuration to use for translation
    """
    if not provider:
        st.error(
            "Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu."
        )
        return

    # Convert language display names back to ISO codes
    # Create reverse mapping: "Deutsch" -> "de"
    lang_name_to_code = {name: code for code, name in LANGUAGES.items()}

    # Handle "Automatisch" for source language
    if source_lang_option == "Automatisch":
        source_lang = "auto"
    else:
        source_lang = lang_name_to_code.get(source_lang_option, "en")

    # Target language must be a valid language (no "auto")
    target_lang = lang_name_to_code.get(target_lang_option, "de")

    try:
        with st.spinner(f"Übersetze Text mit {provider.name}..."):
            translator = PydanticAITranslator(provider)

            if source_lang == "auto":
                detected_lang = translator.detect_language(text)
                st.info(f"Erkannte Sprache: {detected_lang.upper()}")
                source_lang = detected_lang

            translation = translator.translate(text, source_lang, target_lang)
            st.session_state.translation_result = translation

        st.success(f"Übersetzung erfolgreich mit {provider.name}!")

    except Exception as e:
        st.error(f"Fehler bei der Übersetzung: {str(e)}")
        st.info(
            "Bitte überprüfen Sie:\n- API-Schlüssel ist korrekt\n- Modellname ist gültig\n- Internetverbindung"
        )


def render_translation_results() -> None:
    """Render translation results with formatting."""
    translation = st.session_state.translation_result

    st.markdown("---")
    st.markdown(
        (
            f"**{translation.title}** | "
            f"{translation.source_language.upper()} → {translation.target_language.upper()} | "
            f"{len(translation.sentences)} Sätze"
        )
    )

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
