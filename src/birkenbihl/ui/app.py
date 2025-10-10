"""Streamlit UI for the Birkenbihl application.

This module provides a web-based graphical interface using Streamlit,
with tabs for translation and settings management.
"""

import os
from pathlib import Path
from uuid import uuid4

import streamlit as st

from birkenbihl.models.settings import Settings
from birkenbihl.models.translation import Sentence, Translation, WordAlignment


def configure_page() -> None:
    """Configure Streamlit page settings and styling."""
    st.set_page_config(
        page_title="Birkenbihl Sprachlernmethode",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("📚 Birkenbihl Sprachlernmethode")
    st.markdown("*Dekodieren Sie Texte nach der Vera F. Birkenbihl Methode*")
    st.divider()


def initialize_session_state() -> None:
    """Initialize Streamlit session state with default values."""
    if "settings" not in st.session_state:
        st.session_state.settings = Settings.load_from_env()
    if "translation_result" not in st.session_state:
        st.session_state.translation_result = None


def render_translation_tab() -> None:
    """Render the translation tab with input and results."""
    st.header("Übersetzung")

    col1, col2 = st.columns([3, 1])

    with col1:
        text_input = st.text_area(
            "Text eingeben",
            height=200,
            placeholder="Geben Sie hier den zu übersetzenden Text ein...",
            help="Geben Sie einen Text in Englisch oder Spanisch ein",
        )

    with col2:
        st.markdown("### Einstellungen")

        language_detection = st.selectbox(
            "Spracherkennung",
            options=["Automatisch", "Englisch", "Spanisch"],
            index=0,
            help="Wählen Sie die Ausgangssprache",
        )

        target_lang = st.selectbox(
            "Zielsprache",
            options=["Deutsch", "Englisch", "Spanisch"],
            index=0,
            help="Wählen Sie die Zielsprache für die Übersetzung",
        )

        st.divider()

        translate_button = st.button(
            "🔄 Übersetzen",
            type="primary",
            use_container_width=True,
        )

    if translate_button:
        if not text_input.strip():
            st.error("Bitte geben Sie einen Text ein.")
        else:
            translate_text(text_input, language_detection, target_lang)

    if st.session_state.translation_result:
        render_translation_results()


def translate_text(text: str, source_lang_option: str, target_lang_option: str) -> None:
    """Translate text using mock data (stub implementation).

    Args:
        text: Input text to translate
        source_lang_option: Source language selection
        target_lang_option: Target language selection
    """
    lang_map = {
        "Automatisch": "auto",
        "Englisch": "en",
        "Spanisch": "es",
        "Deutsch": "de",
    }

    source_lang = lang_map[source_lang_option]
    target_lang = lang_map[target_lang_option]

    with st.spinner("Übersetze Text..."):
        translation = create_mock_translation(text, source_lang, target_lang)
        st.session_state.translation_result = translation

    st.success("Übersetzung erfolgreich!")


def create_mock_translation(text: str, source_lang: str, target_lang: str) -> Translation:
    """Create mock translation for demonstration (stub implementation).

    Args:
        text: Source text
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Mock Translation object
    """
    sentences = []
    for sentence_text in text.split("."):
        if sentence_text.strip():
            word_alignments = []
            words = sentence_text.strip().split()
            for pos, word in enumerate(words):
                word_alignments.append(
                    WordAlignment(
                        source_word=word,
                        target_word=f"[{word}]",
                        position=pos,
                    )
                )

            sentences.append(
                Sentence(
                    source_text=sentence_text.strip(),
                    natural_translation=f"[Natürliche Übersetzung: {sentence_text.strip()}]",
                    word_alignments=word_alignments,
                )
            )

    detected_source = source_lang if source_lang != "auto" else "en"

    return Translation(
        id=uuid4(),
        title=f"Übersetzung {text[:30]}...",
        source_language=detected_source,
        target_language=target_lang,
        sentences=sentences,
    )


def render_translation_results() -> None:
    """Render translation results with formatting."""
    translation = st.session_state.translation_result

    st.divider()
    st.subheader("Ergebnisse")

    st.markdown(f"**Titel:** {translation.title}")
    st.markdown(f"**Von:** {translation.source_language.upper()} → **Nach:** {translation.target_language.upper()}")
    st.markdown(f"**Anzahl Sätze:** {len(translation.sentences)}")

    st.divider()

    for i, sentence in enumerate(translation.sentences, 1):
        with st.expander(f"Satz {i}: {sentence.source_text[:50]}...", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Original:**")
                st.info(sentence.source_text)

            with col2:
                st.markdown("**Natürliche Übersetzung:**")
                st.success(sentence.natural_translation)

            st.markdown("**Wort-für-Wort Dekodierung:**")

            alignment_html = "<div style='font-size: 14px; line-height: 2.5;'>"
            for alignment in sentence.word_alignments:
                alignment_html += f"""
                <span style='display: inline-block; margin: 4px; padding: 8px 12px;
                             background-color: #f0f2f6; border-radius: 8px;
                             border: 1px solid #ddd;'>
                    <div style='color: #0066cc; font-weight: 600;'>{alignment.source_word}</div>
                    <div style='color: #666; font-size: 12px;'>↓</div>
                    <div style='color: #009900; font-weight: 600;'>{alignment.target_word}</div>
                </span>
                """
            alignment_html += "</div>"

            st.markdown(alignment_html, unsafe_allow_html=True)


def render_settings_tab() -> None:
    """Render the settings tab with configuration options."""
    st.header("Einstellungen")

    st.markdown("Konfigurieren Sie die API-Schlüssel und Standardeinstellungen für die Übersetzung.")

    with st.form("settings_form"):
        st.subheader("API-Schlüssel")

        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.settings.openai_api_key or "",
            help="Ihr OpenAI API-Schlüssel für GPT-Modelle",
        )

        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.session_state.settings.anthropic_api_key or "",
            help="Ihr Anthropic API-Schlüssel für Claude-Modelle",
        )

        st.divider()
        st.subheader("Standardeinstellungen")

        default_model = st.selectbox(
            "Standard-Modell",
            options=[
                "openai:gpt-4",
                "openai:gpt-4o",
                "anthropic:claude-3-5-sonnet-20241022",
                "anthropic:claude-3-opus-20240229",
            ],
            index=0 if st.session_state.settings.default_model.startswith("openai") else 2,
            help="Wählen Sie das Standard-KI-Modell für Übersetzungen",
        )

        target_language = st.selectbox(
            "Standard-Zielsprache",
            options=["de", "en", "es"],
            index=["de", "en", "es"].index(st.session_state.settings.target_language),
            help="Wählen Sie die Standard-Zielsprache",
        )

        submitted = st.form_submit_button("💾 Speichern", type="primary", use_container_width=True)

        if submitted:
            save_settings(openai_key, anthropic_key, default_model, target_language)


def save_settings(openai_key: str, anthropic_key: str, model: str, target_lang: str) -> None:
    """Save settings to environment file.

    Args:
        openai_key: OpenAI API key
        anthropic_key: Anthropic API key
        model: Default model selection
        target_lang: Default target language
    """
    try:
        settings = Settings(
            openai_api_key=openai_key if openai_key else None,
            anthropic_api_key=anthropic_key if anthropic_key else None,
            default_model=model,
            target_language=target_lang,
        )

        env_path = Path.cwd() / ".env"
        settings.save_to_env(env_path)

        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key

        st.session_state.settings = settings
        st.success("Einstellungen erfolgreich gespeichert!")

    except Exception as e:
        st.error(f"Fehler beim Speichern der Einstellungen: {e}")


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
