"""Settings tab UI for the Birkenbihl application."""

from pathlib import Path

import streamlit as st
from pydantic import BaseModel

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.providers.registry import ProviderRegistry
from birkenbihl.services import language_service as ls
from birkenbihl.services.settings_service import SettingsService


class ProviderConfigModel(BaseModel):
    name: str
    provider_type: str
    model: str
    api_key: str
    is_default: bool = False
    supports_streaming: bool = True


def render_settings_tab() -> None:
    """Render the settings tab with provider management."""
    st.markdown("**Konfigurierte Provider**")

    # Show provider cards only when no form is active
    if not st.session_state.show_add_provider_form and not st.session_state.show_edit_provider_form:
        if not st.session_state.settings.providers:
            st.info("Noch keine Provider konfiguriert.")
        else:
            for i, provider in enumerate(st.session_state.settings.providers):
                render_provider_card(provider, i)

            # Warn if no provider is marked as default
            if not any(p.is_default for p in st.session_state.settings.providers):
                message = "⚠️ Kein Provider als Standard markiert. "
                message += "Der erste Provider in der Liste wird automatisch verwendet. "
                message += "Der Standard-Provider ist beim Übersetzen vorausgewählt."
                st.warning(message)

    st.markdown("")  # Small spacing

    # Show edit form, add form, or add button
    if st.session_state.show_edit_provider_form:
        render_edit_provider_form()
    elif st.session_state.show_add_provider_form:
        render_add_provider_form()
    else:
        if st.button("➕ Neuen Provider hinzufügen", type="primary"):
            st.session_state.show_add_provider_form = True
            st.rerun()

    st.markdown("---")
    st.markdown("**Allgemeine Einstellungen**")

    with st.form("general_settings_form"):
        # Show language names but save ISO codes
        lang_names = [lang.name_de for lang in ls.get_languages()]

        # Find current language index
        current_code = st.session_state.settings.target_language
        try:
            current_lang_name = ls.get_language_by(current_code).name_de
            current_index = lang_names.index(current_lang_name)
        except (KeyError, ValueError):
            current_index = lang_names.index("Deutsch")  # Default to German

        selected_lang_name = st.selectbox(
            "Standard-Zielsprache",
            options=lang_names,
            index=current_index,
        )

        # Convert back to ISO code for saving
        try:
            selected_language = ls.get_language_by(name_or_code=selected_lang_name)
        except KeyError:
            selected_language = ls.get_language_by(name_or_code="de")

        if st.form_submit_button("Speichern", type="primary", use_container_width=True):
            save_general_settings(selected_language)


def render_provider_card(provider: ProviderConfig, index: int) -> None:
    """Render a provider configuration card with actions.

    Args:
        provider: Provider configuration to display
        index: Index of provider in the list
    """
    provider_icon = "⭐ " if provider.is_default else ""
    # Compact: Show provider type and model in title, only default expanded
    with st.expander(
        f"{provider_icon}{provider.name} | {provider.provider_type} | {provider.model}",
        expanded=False,
    ):
        col1, col2 = st.columns([3, 1])

        with col1:
            masked_key = provider.api_key[:8] + "..." + provider.api_key[-4:] if len(provider.api_key) > 12 else "***"
            st.caption(f"API-Schlüssel: `{masked_key}`")
            if provider.is_default:
                st.success("✓ Standard-Provider")

        with col2:
            if not provider.is_default:
                if st.button("Als Standard", key=f"default_{index}", use_container_width=True):
                    set_provider_as_default(index)

            if st.button("Bearbeiten", key=f"edit_{index}", use_container_width=True):
                edit_provider(index)

            if st.button("Löschen", key=f"delete_{index}", type="secondary", use_container_width=True):
                delete_provider(index)


def render_add_provider_form() -> None:
    """Render form for adding a new provider configuration."""
    st.markdown("**Neuen Provider hinzufügen**")

    # Step 1: Select provider type
    provider_types_list = ProviderRegistry.get_provider_types()
    provider_metadata_map = {pt: ProviderRegistry.get_provider_metadata(pt) for pt in provider_types_list}

    # Filter out None values (should not happen, but type-safe)
    valid_metadata = {pt: meta for pt, meta in provider_metadata_map.items() if meta is not None}

    if not valid_metadata:
        st.error("Keine Provider verfügbar. Bitte installieren Sie die erforderlichen Pakete.")
        return

    # Create display names for provider types
    provider_type_displays = [f"{valid_metadata[pt].display_name} ({pt})" for pt in valid_metadata.keys()]

    # Step 1 & 2 in columns
    col1, col2 = st.columns(2)
    with col1:
        selected_provider_display = st.selectbox(
            "Provider-Typ",
            options=provider_type_displays,
            help="Wählen Sie den Anbieter",
        )

    # Extract provider_type from display
    selected_provider_type = list(valid_metadata.keys())[provider_type_displays.index(selected_provider_display)]
    provider_metadata = valid_metadata[selected_provider_type]
    available_models = provider_metadata.default_models

    with col2:
        selected_model = st.selectbox(
            "Modell",
            options=available_models,
            help=f"Modelle für {provider_metadata.display_name}",
        )

    # Step 3: Name and API key
    suggested_name = f"{provider_metadata.display_name} - {selected_model}"
    provider_name = st.text_input(
        "Name",
        value=suggested_name,
        placeholder="z.B. Mein GPT-4",
    )

    api_key = st.text_input(
        "API-Schlüssel",
        type="password",
        placeholder="sk-...",
    )

    is_default = st.checkbox(
        "Als Standard setzen",
        value=len(st.session_state.settings.providers) == 0,
    )

    # Streaming support checkbox
    # Create temporary config to check streaming support
    temp_config = ProviderConfig(
        name="temp",
        provider_type=selected_provider_type,
        model=selected_model,
        api_key="temp",
    )
    provider_supports_streaming = ProviderRegistry.supports_streaming(temp_config)

    supports_streaming = st.checkbox(
        "Streaming aktivieren",
        value=provider_supports_streaming,
        disabled=not provider_supports_streaming,
        help="Zeigt Fortschritt während der Übersetzung an (empfohlen für lange Texte)"
        if provider_supports_streaming
        else "Dieser Provider/Modell unterstützt kein Streaming",
    )

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✓ Provider hinzufügen", type="primary", use_container_width=True):
            if not provider_name or not api_key:
                st.error("Bitte füllen Sie alle Felder aus.")
            else:
                model = ProviderConfigModel(
                    provider_type=selected_provider_type,
                    name=provider_name,
                    model=selected_model,
                    api_key=api_key,
                    is_default=is_default,
                    supports_streaming=supports_streaming,
                )
                add_provider(model)
                st.session_state.show_add_provider_form = False
                st.rerun()

    with col2:
        if st.button("✗ Abbrechen", use_container_width=True):
            st.session_state.show_add_provider_form = False
            st.rerun()


def edit_provider(index: int) -> None:
    """Open the edit form for a provider configuration.

    Args:
        index: Index of provider to edit
    """
    st.session_state.show_edit_provider_form = True
    st.session_state.edit_provider_index = index
    st.session_state.show_add_provider_form = False
    st.rerun()


def render_edit_provider_form() -> None:
    """Render form for editing an existing provider configuration."""
    index = st.session_state.edit_provider_index
    if index is None or index >= len(st.session_state.settings.providers):
        st.error("Ungültiger Provider-Index")
        return

    provider = st.session_state.settings.providers[index]
    st.markdown("**Provider bearbeiten**")

    # Provider type is readonly - show but disable
    provider_metadata = ProviderRegistry.get_provider_metadata(provider.provider_type)
    if provider_metadata is None:
        st.error(f"Provider-Typ '{provider.provider_type}' nicht gefunden")
        return

    # Show provider type as info
    st.info(f"Provider-Typ: {provider_metadata.display_name} ({provider.provider_type})")

    # Model selection
    available_models = provider_metadata.default_models
    try:
        current_model_index = available_models.index(provider.model)
    except ValueError:
        current_model_index = 0

    selected_model = st.selectbox(
        "Modell",
        options=available_models,
        index=current_model_index,
        help=f"Modelle für {provider_metadata.display_name}",
    )

    # Name and API key
    provider_name = st.text_input(
        "Name",
        value=provider.name,
        placeholder="z.B. Mein GPT-4",
    )

    api_key = st.text_input(
        "API-Schlüssel",
        value=provider.api_key,
        type="password",
        placeholder="sk-...",
    )

    is_default = st.checkbox(
        "Als Standard setzen",
        value=provider.is_default,
    )

    # Streaming support checkbox
    temp_config = ProviderConfig(
        name="temp",
        provider_type=provider.provider_type,
        model=selected_model,
        api_key="temp",
    )
    provider_supports_streaming = ProviderRegistry.supports_streaming(temp_config)

    supports_streaming = st.checkbox(
        "Streaming aktivieren",
        value=provider.supports_streaming if provider_supports_streaming else False,
        disabled=not provider_supports_streaming,
        help="Zeigt Fortschritt während der Übersetzung an (empfohlen für lange Texte)"
        if provider_supports_streaming
        else "Dieser Provider/Modell unterstützt kein Streaming",
    )

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            if not provider_name or not api_key:
                st.error("Bitte füllen Sie alle Felder aus.")
            else:
                model = ProviderConfigModel(
                    provider_type=provider.provider_type,
                    name=provider_name,
                    model=selected_model,
                    api_key=api_key,
                    is_default=is_default,
                    supports_streaming=supports_streaming,
                )
                update_provider(index, model)
                st.session_state.show_edit_provider_form = False
                st.session_state.edit_provider_index = None
                st.rerun()

    with col2:
        if st.button("✗ Abbrechen", use_container_width=True):
            st.session_state.show_edit_provider_form = False
            st.session_state.edit_provider_index = None
            st.rerun()


def add_provider(model: ProviderConfigModel) -> None:
    """Add a new provider configuration.

    Args:
        name: Provider display name
        provider_type: Provider type (openai or anthropic)
        model: Model identifier
        api_key: API key for authentication
        is_default: Whether this should be the default provider
        supports_streaming: Whether streaming is enabled for this provider
    """
    try:
        new_provider = ProviderConfig(**model.model_dump())

        if model.is_default:
            for provider in st.session_state.settings.providers:
                provider.is_default = False

        st.session_state.settings.providers.append(new_provider)

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

        st.success(f"Provider '{model.name}' erfolgreich hinzugefügt!")

    except Exception as e:
        st.error(f"Fehler beim Hinzufügen des Providers: {e}")


def update_provider(index: int, model: ProviderConfigModel) -> None:
    """Update an existing provider configuration.

    Args:
        index: Index of provider to update
        model: Updated provider configuration
    """
    try:
        updated_provider = ProviderConfig(**model.model_dump())

        if model.is_default:
            for i, provider in enumerate(st.session_state.settings.providers):
                if i != index:
                    provider.is_default = False

        st.session_state.settings.providers[index] = updated_provider

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

        st.success(f"Provider '{model.name}' erfolgreich aktualisiert!")

    except Exception as e:
        st.error(f"Fehler beim Aktualisieren des Providers: {e}")


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


def save_general_settings(target_lang: Language) -> None:
    """Save general settings to YAML file.

    Args:
        target_lang: Default target language
    """
    try:
        st.session_state.settings.target_language = target_lang.code

        settings_file = Path.cwd() / "settings.yaml"
        SettingsService.save_settings(st.session_state.settings, settings_file)

        st.success("Einstellungen erfolgreich gespeichert!")

    except Exception as e:
        st.error(f"Fehler beim Speichern der Einstellungen: {e}")
