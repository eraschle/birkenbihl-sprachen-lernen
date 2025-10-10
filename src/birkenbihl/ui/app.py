"""Streamlit UI for the Birkenbihl application.

This module provides a web-based graphical interface using Streamlit,
with tabs for translation and settings management.
"""

from pathlib import Path

import streamlit as st

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.providers.registry import ProviderRegistry
from birkenbihl.services.settings_service import SettingsService


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
        st.session_state.settings = SettingsService.get_settings()
    if "translation_result" not in st.session_state:
        st.session_state.translation_result = None
    if "show_add_provider_form" not in st.session_state:
        st.session_state.show_add_provider_form = False


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
    """Translate text using configured provider.

    Args:
        text: Input text to translate
        source_lang_option: Source language selection
        target_lang_option: Target language selection
    """
    current_provider = SettingsService.get_current_provider()

    if not current_provider:
        st.error("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
        return

    lang_map = {
        "Automatisch": "auto",
        "Englisch": "en",
        "Spanisch": "es",
        "Deutsch": "de",
    }

    source_lang = lang_map[source_lang_option]
    target_lang = lang_map[target_lang_option]

    try:
        with st.spinner(f"Übersetze Text mit {current_provider.name}..."):
            translator = PydanticAITranslator(current_provider)

            if source_lang == "auto":
                detected_lang = translator.detect_language(text)
                st.info(f"Erkannte Sprache: {detected_lang.upper()}")
                source_lang = detected_lang

            translation = translator.translate(text, source_lang, target_lang)
            st.session_state.translation_result = translation

        st.success(f"Übersetzung erfolgreich mit {current_provider.name}!")

    except Exception as e:
        st.error(f"Fehler bei der Übersetzung: {str(e)}")
        st.info("Bitte überprüfen Sie:\n- API-Schlüssel ist korrekt\n- Modellname ist gültig\n- Internetverbindung")


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


def get_provider_templates() -> dict[str, dict[str, str]]:
    """Get predefined provider templates for common AI models.

    Uses ProviderRegistry to get recommended models (max 3 per provider).

    Returns:
        Dictionary mapping template names to provider configurations
    """
    templates = {}

    for metadata in ProviderRegistry.get_supported_providers():
        # Only use first 3 models per provider for templates (most recommended)
        recommended_models = metadata.default_models[:3]

        for model in recommended_models:
            template_name = f"{metadata.display_name} - {model}"
            templates[template_name] = {
                "provider_type": metadata.provider_type,
                "model": model,
            }

    return templates


def render_provider_card(provider: ProviderConfig, index: int) -> None:
    """Render a provider configuration card with actions.

    Args:
        provider: Provider configuration to display
        index: Index of provider in the list
    """
    provider_icon = "⭐ " if provider.is_default else ""
    with st.expander(f"{provider_icon}{provider.name} ({provider.provider_type})", expanded=provider.is_default):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**Provider-Typ:** {provider.provider_type}")
            st.markdown(f"**Modell:** {provider.model}")
            masked_key = provider.api_key[:8] + "..." + provider.api_key[-4:] if len(provider.api_key) > 12 else "***"
            st.markdown(f"**API-Schlüssel:** `{masked_key}`")
            if provider.is_default:
                st.success("✓ Standard-Provider")

        with col2:
            if not provider.is_default:
                if st.button("Als Standard", key=f"default_{index}", use_container_width=True):
                    set_provider_as_default(index)

            if st.button("Löschen", key=f"delete_{index}", type="secondary", use_container_width=True):
                delete_provider(index)


def render_add_provider_form() -> None:
    """Render form for adding a new provider configuration."""
    st.subheader("Neuen Provider hinzufügen")

    with st.form("add_provider_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            template = st.selectbox(
                "Vorlage wählen (optional)",
                options=["Benutzerdefiniert"] + list(get_provider_templates().keys()),
                help="Wählen Sie eine Vorlage oder erstellen Sie eine benutzerdefinierte Konfiguration",
            )

        templates = get_provider_templates()
        if template != "Benutzerdefiniert" and template in templates:
            template_config = templates[template]
            default_name = template
            default_type = template_config["provider_type"]
            default_model = template_config["model"]
        else:
            default_name = ""
            default_type = "openai"
            default_model = ""

        with col2:
            provider_name = st.text_input(
                "Name",
                value=default_name,
                placeholder="z.B. Mein GPT-4",
                help="Ein eindeutiger Name für diesen Provider",
            )

        col1, col2 = st.columns(2)

        with col1:
            provider_types = ProviderRegistry.get_provider_types()
            try:
                default_index = provider_types.index(default_type)
            except ValueError:
                default_index = 0

            provider_type = st.selectbox(
                "Provider-Typ",
                options=provider_types,
                index=default_index,
                help="Wählen Sie den Provider-Typ",
            )

        with col2:
            model = st.text_input(
                "Modell",
                value=default_model,
                placeholder="z.B. gpt-4, claude-3-5-sonnet-20241022",
                help="Modell-Identifier",
            )

        api_key = st.text_input(
            "API-Schlüssel",
            type="password",
            placeholder="sk-...",
            help="Ihr API-Schlüssel für diesen Provider",
        )

        is_default = st.checkbox(
            "Als Standard-Provider setzen",
            value=len(st.session_state.settings.providers) == 0,
            help="Dieser Provider wird standardmäßig für Übersetzungen verwendet",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Provider hinzufügen", type="primary", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("Abbrechen", use_container_width=True)

        if submitted:
            if not provider_name or not model or not api_key:
                st.error("Bitte füllen Sie alle erforderlichen Felder aus.")
            else:
                add_provider(provider_name, provider_type, model, api_key, is_default)
                st.session_state.show_add_provider_form = False
                st.rerun()

        if cancelled:
            st.session_state.show_add_provider_form = False
            st.rerun()


def render_settings_tab() -> None:
    """Render the settings tab with provider management."""
    st.header("Einstellungen")

    st.markdown("Verwalten Sie Ihre AI-Provider-Konfigurationen für Übersetzungen.")
    st.divider()

    st.subheader("Konfigurierte Provider")

    if not st.session_state.settings.providers:
        st.info("Noch keine Provider konfiguriert. Fügen Sie einen Provider hinzu, um zu beginnen.")
    else:
        for i, provider in enumerate(st.session_state.settings.providers):
            render_provider_card(provider, i)

    st.divider()

    if st.session_state.show_add_provider_form:
        render_add_provider_form()
    else:
        if st.button("➕ Neuen Provider hinzufügen", type="primary"):
            st.session_state.show_add_provider_form = True
            st.rerun()

    st.divider()
    st.subheader("Allgemeine Einstellungen")

    with st.form("general_settings_form"):
        target_language = st.selectbox(
            "Standard-Zielsprache",
            options=["de", "en", "es"],
            index=["de", "en", "es"].index(st.session_state.settings.target_language),
            help="Wählen Sie die Standard-Zielsprache für Übersetzungen",
        )

        if st.form_submit_button("Speichern", type="primary", use_container_width=True):
            save_general_settings(target_language)


def add_provider(name: str, provider_type: str, model: str, api_key: str, is_default: bool) -> None:
    """Add a new provider configuration.

    Args:
        name: Provider display name
        provider_type: Provider type (openai or anthropic)
        model: Model identifier
        api_key: API key for authentication
        is_default: Whether this should be the default provider
    """
    try:
        new_provider = ProviderConfig(
            name=name,
            provider_type=provider_type,
            model=model,
            api_key=api_key,
            is_default=is_default,
        )

        if is_default:
            for provider in st.session_state.settings.providers:
                provider.is_default = False

        st.session_state.settings.providers.append(new_provider)

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

        st.success(f"Provider '{name}' erfolgreich hinzugefügt!")

    except Exception as e:
        st.error(f"Fehler beim Hinzufügen des Providers: {e}")


def delete_provider(index: int) -> None:
    """Delete a provider configuration by index.

    Args:
        index: Index of provider to delete
    """
    try:
        provider_name = st.session_state.settings.providers[index].name
        st.session_state.settings.providers.pop(index)

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

        st.success(f"Provider '{provider_name}' erfolgreich gelöscht!")
        st.rerun()

    except Exception as e:
        st.error(f"Fehler beim Löschen des Providers: {e}")


def set_provider_as_default(index: int) -> None:
    """Set a provider as the default.

    Args:
        index: Index of provider to set as default
    """
    try:
        for i, provider in enumerate(st.session_state.settings.providers):
            provider.is_default = i == index

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

        st.success("Standard-Provider erfolgreich aktualisiert!")
        st.rerun()

    except Exception as e:
        st.error(f"Fehler beim Setzen des Standard-Providers: {e}")


def save_general_settings(target_lang: str) -> None:
    """Save general settings to YAML file.

    Args:
        target_lang: Default target language
    """
    try:
        st.session_state.settings.target_language = target_lang

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

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
