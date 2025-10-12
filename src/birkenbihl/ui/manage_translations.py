"""Translation management UI for listing, viewing, and deleting translations."""

from uuid import UUID

import streamlit as st

from birkenbihl.models.translation import Translation
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.ui.services.translation_ui_service import TranslationUIServiceImpl
from birkenbihl.ui.state.session import SessionStateManager


def render_manage_translations_tab() -> None:
    """Main function for translation management tab.

    Displays all translations with options to view, edit, or delete them.
    """
    st.subheader("Übersetzungen verwalten")

    try:
        service = TranslationUIServiceImpl.get_service()
        translations = service.list_all_translations()

        if not translations:
            st.info("Keine Übersetzungen vorhanden. Erstellen Sie zuerst eine Übersetzung im 'Übersetzen' Tab.")
            return

        st.write(f"**{len(translations)} Übersetzung(en) gefunden:**")

        for translation in translations:
            render_translation_card(translation, service)

    except Exception as e:
        st.error(f"Fehler beim Laden der Übersetzungen: {e}")


def render_translation_card(translation: Translation, service: TranslationService) -> None:
    """Render a single translation card with expand/collapse functionality.

    Args:
        translation: The translation to display
        service: Translation service for delete operations
    """
    source_lang = translation.source_language.code.upper()
    target_lang = translation.target_language.code.upper()

    message = f"**{translation.title or 'Ohne Titel'}** | "
    message += f"{source_lang} → {target_lang} | "
    message += f"{len(translation.sentences)} Satz/Sätze"
    with st.expander(message):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**Erstellt:** {translation.created_str()}")
            if translation.updated_at and translation.updated_at != translation.created_at:
                st.write(f"**Aktualisiert:** {translation.updated_str()}")

        with col2:
            if st.button("✏️ Bearbeiten", key=f"edit_{translation.uuid}", use_container_width=True):
                open_translation_editor(translation.uuid)

            if st.button("🗑️ Löschen", key=f"delete_{translation.uuid}", use_container_width=True, type="secondary"):
                delete_translation_with_confirmation(translation, service)


def delete_translation_with_confirmation(translation: Translation, service: TranslationService) -> None:
    """Handle translation deletion with confirmation dialog.

    Args:
        translation: The translation to delete
        service: Translation service for delete operations
    """
    confirmation_key = f"confirm_delete_{translation.uuid}"

    if confirmation_key not in st.session_state:
        st.session_state[confirmation_key] = False

    if not st.session_state[confirmation_key]:
        st.session_state[confirmation_key] = True
        st.rerun()
    else:
        message = f"Möchten Sie die Übersetzung **'{translation.title or 'Ohne Titel'}'** wirklich löschen? "
        message += "Diese Aktion kann nicht rückgängig gemacht werden."
        st.warning(message)

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "✓ Ja, löschen",
                key=f"confirm_yes_{translation.uuid}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    service.delete_translation(translation.uuid)
                    st.success(f"Übersetzung '{translation.title or 'Ohne Titel'}' erfolgreich gelöscht.")
                    if confirmation_key in st.session_state:
                        del st.session_state[confirmation_key]
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Löschen der Übersetzung: {e}")

        with col2:
            if st.button("✗ Abbrechen", key=f"confirm_no_{translation.uuid}", use_container_width=True):
                if confirmation_key in st.session_state:
                    del st.session_state[confirmation_key]
                st.rerun()


def open_translation_editor(translation_id: UUID) -> None:
    """Open the translation editor for the specified translation.

    Args:
        translation_id: UUID of the translation to edit
    """
    state = SessionStateManager()
    state.selected_translation_id = translation_id
    state.current_view = "Übersetzung bearbeiten"
    st.rerun()
