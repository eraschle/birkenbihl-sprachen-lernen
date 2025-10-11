"""Translation result and editing UI for the Birkenbihl application.

This module provides a unified view for:
1. Reviewing newly created translations (with optional progress bar)
2. Editing existing translations
Both flows share the same editing interface.

Refactored to use Clean Code principles with reusable components.
"""

import asyncio
import logging

import streamlit as st
from pydantic import BaseModel

from birkenbihl.models import languages
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.ui.components import AlignmentEditor, AlignmentPreview, ProviderSelector
from birkenbihl.ui.models.context import AlignmentContext, ProviderSelectorContext
from birkenbihl.ui.services.translation_ui_service import TranslationUIServiceImpl
from birkenbihl.ui.state.cache import SessionCacheManager
from birkenbihl.ui.state.session import SessionStateManager

logger = logging.getLogger(__name__)


class TranslationModel(BaseModel):
    text: str
    title: str
    source_language: str
    target_language: str


def render_translation_result_tab() -> None:
    """Render translation result view with editing capabilities.

    Refactored to use StateManager and TranslationUIService.

    This view is used for both:
    - New translations (after creation, before saving)
    - Editing existing translations
    - Active translation (showing progress)
    """
    state = SessionStateManager()

    # Check if translation is currently running
    if state.is_translating and state.get("translation_pending"):
        _execute_translation()
        return

    # Load translation (new or existing)
    is_new = state.is_new_translation
    translation = _load_translation(state, is_new)

    if not translation:
        return

    # Show detected language info for new translations
    detected_lang_info = state.get("detected_language_info")
    if is_new and detected_lang_info:
        st.info(detected_lang_info)

    # Render header with save/back buttons
    render_header(translation, is_new)

    st.markdown("---")

    # Render sentence editors (use TranslationUIService for consistent service access)
    service = TranslationUIServiceImpl.get_service()

    for i, sentence in enumerate(translation.sentences, 1):
        try:
            render_sentence_editor(translation, sentence, i, service, is_new)
        except Exception as e:
            _handle_sentence_editor_error(i, e)


def _load_translation(state: SessionStateManager, is_new: bool) -> Translation | None:
    """Load translation from session state or storage.

    Args:
        state: Session state manager
        is_new: True if loading new translation

    Returns:
        Translation object or None if not found
    """
    if is_new:
        translation = state.translation_result
        if not translation:
            st.error("Keine Übersetzung gefunden")
        return translation

    translation_id = state.selected_translation_id
    if not translation_id:
        st.error("Keine Übersetzung ausgewählt")
        return None

    try:
        translation = TranslationUIServiceImpl.get_translation(translation_id)
        if not translation:
            st.error(f"Übersetzung {translation_id} nicht gefunden")
        return translation
    except Exception as e:
        st.error(f"Fehler beim Laden der Übersetzung: {e}")
        return None


def _handle_sentence_editor_error(sentence_index: int, error: Exception) -> None:
    """Handle and display sentence editor errors.

    Args:
        sentence_index: 1-based sentence index
        error: Exception that occurred
    """
    st.error(f"⚠️ Satz {sentence_index} kann nicht bearbeitet werden: {str(error)}")

    error_msg = str(error).lower()
    if "default value" in error_msg and "not part of the options" in error_msg:
        st.info(
            "💡 Mögliche Ursache: Einige Wörter aus der Word-by-Word-Zuordnung kommen nicht "
            "in der natürlichen Übersetzung vor. Bitte ändern Sie die natürliche Übersetzung."
        )
    else:
        st.info("💡 Tipp: Versuchen Sie die natürliche Übersetzung für diesen Satz anzupassen.")


def render_header(translation: Translation, is_new: bool) -> None:
    """Render translation header with save/back buttons.

    Args:
        translation: Translation being edited
        is_new: True if this is a newly created translation
    """
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        title_prefix = "✨ Neue Übersetzung" if is_new else "✏️ Übersetzung bearbeiten"
        st.markdown(f"### {title_prefix}: {translation.title}")
        message = f"{translation.source_language.upper()} → {translation.target_language.upper()} | "
        message += f"{len(translation.sentences)} Sätze"
        if not is_new:
            message += f" | Zuletzt geändert: {translation.updated_at.strftime('%d.%m.%Y %H:%M')}"
        st.caption(message)

    with col2:
        if is_new:
            # Validate all sentences before enabling save button
            all_valid, error_count = _validate_all_sentences(translation)
            save_disabled = not all_valid

            if st.button("💾 Speichern", type="primary", use_container_width=True, disabled=save_disabled):
                try:
                    storage = JsonStorageProvider()
                    storage.save(translation)
                    st.success("Übersetzung erfolgreich gespeichert!")
                    logger.info("New translation saved: %s", translation.uuid)
                    # Clear the new translation state
                    st.session_state.is_new_translation = False
                    st.session_state.translation_result = None
                    st.session_state.detected_language_info = None
                    # Navigate to "Meine Übersetzungen"
                    st.session_state.current_view = "Meine Übersetzungen"
                    st.rerun()
                except Exception as e:
                    logger.error("Failed to save translation: %s", str(e), exc_info=True)
                    st.error(f"Fehler beim Speichern: {e}")

            # Show warning if save is disabled
            if save_disabled:
                st.warning(f"⚠️ {error_count} Satz{'ä' if error_count > 1 else ''}tze mit Fehlern")
        else:
            # For existing translations, "Save" is implicit (auto-save on each edit)
            st.caption("Änderungen werden automatisch gespeichert")

    with col3:
        back_label = "✗ Abbrechen" if is_new else "← Zurück"
        if st.button(back_label, use_container_width=True):
            if is_new:
                # Discard the new translation
                st.session_state.is_new_translation = False
                st.session_state.translation_result = None
                st.session_state.detected_language_info = None
                st.session_state.current_view = "Übersetzen"
            else:
                # Go back to translation list
                st.session_state.current_view = "Meine Übersetzungen"
                st.session_state.selected_translation_id = None
            st.rerun()


def render_sentence_editor(
    translation: Translation,
    sentence: Sentence,
    index: int,
    service: TranslationService,
    is_new: bool,
) -> None:
    """Render editor for a single sentence with two editing modes.

    Creates an expandable section for each sentence showing:
    - Current source text and natural translation
    - Tab 1: Natural translation editing mode (provider suggestions)
    - Tab 2: Word-by-word alignment editing mode (manual)

    Args:
        translation: Parent translation object
        sentence: Sentence to edit
        index: Sentence number (1-based)
        service: TranslationService for updates
        is_new: True if this is a newly created translation (not yet saved)
    """
    preview_text = sentence.source_text[:60]
    if len(sentence.source_text) > 60:
        preview_text += "..."

    with st.expander(f"Satz {index}: {preview_text}", expanded=(index == 1)):
        st.markdown("**Aktuell:**")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Original: {sentence.source_text}")
        with col2:
            st.success(f"Natürlich: {sentence.natural_translation}")

        # Show word-by-word alignment preview
        st.markdown("**Word-by-Word Dekodierung:**")
        AlignmentPreview(sentence.word_alignments).render()

        # Only show editing tabs if not new (or allow editing for new too)
        tab1, tab2 = st.tabs(["🔄 Natürliche Übersetzung ändern", "🔧 Word-by-Word bearbeiten"])

        with tab1:
            render_natural_edit_mode(translation, sentence, service, is_new)

        with tab2:
            render_alignment_edit_mode(translation, sentence, service, is_new)


def render_natural_edit_mode(
    translation: Translation, sentence: Sentence, service: TranslationService, is_new: bool
) -> None:
    """Render natural translation editing mode with provider suggestions.

    Refactored to use ProviderSelector component and SessionCacheManager.
    Reduced from ~107 lines to ~60 lines.

    Args:
        translation: Parent translation object
        sentence: Sentence to edit
        service: TranslationService for API calls
        is_new: True if this is a newly created translation
    """
    st.markdown("**Provider-Vorschläge generieren:**")

    # Use ProviderSelector component
    selector_context = ProviderSelectorContext(
        providers=st.session_state.settings.providers,
        default_provider=SettingsService.get_current_provider(),
        disabled=False,
        key_suffix=str(sentence.uuid),
    )
    provider_selector = ProviderSelector(selector_context)
    selected_provider = provider_selector.render()

    if not selected_provider:
        return

    if st.button("🔄 Vorschläge generieren", key=f"gen_suggestions_{sentence.uuid}"):
        _generate_suggestions(translation, sentence, selected_provider, service)

    # Use SessionCacheManager instead of direct st.session_state access
    suggestions = SessionCacheManager.get_suggestions(sentence.uuid)
    if suggestions:
        st.markdown("**Vorschläge:**")
        selected_suggestion = st.radio(
            "Wählen Sie eine Übersetzung:", options=suggestions, key=f"radio_suggestions_{sentence.uuid}"
        )

        if selected_suggestion and selected_suggestion != sentence.natural_translation:
            st.markdown("---")
            st.markdown("**Vorschau (Word-by-Word wird neu generiert):**")

            with st.spinner("Generiere neue Word-by-Word Zuordnung..."):
                try:
                    translator = PydanticAITranslator(selected_provider)

                    preview_alignments = translator.regenerate_alignment(
                        sentence.source_text,
                        selected_suggestion,
                        translation.source_language,
                        translation.target_language,
                    )

                    st.info(f"Neue natürliche Übersetzung: {selected_suggestion}")
                    AlignmentPreview(preview_alignments).render()

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Übernehmen", key=f"confirm_natural_{sentence.uuid}", type="primary"):
                            try:
                                if is_new:
                                    # Update in-memory translation (not yet saved)
                                    sentence.natural_translation = selected_suggestion
                                    sentence.word_alignments = preview_alignments
                                    st.success("Übersetzung aktualisiert! (Nicht vergessen zu speichern)")
                                else:
                                    # Update persisted translation
                                    service.update_sentence_natural(
                                        translation.uuid, sentence.uuid, selected_suggestion, selected_provider
                                    )
                                    st.success("Übersetzung erfolgreich aktualisiert!")

                                SessionCacheManager.clear_suggestions(sentence.uuid)
                                st.rerun()
                            except Exception as e:
                                logger.error("Failed to update sentence: %s", str(e), exc_info=True)
                                st.error(f"Fehler beim Speichern: {e}")

                    with col2:
                        if st.button("✗ Abbrechen", key=f"cancel_natural_{sentence.uuid}"):
                            st.rerun()

                except Exception as e:
                    logger.error("Failed to generate alignment preview: %s", str(e), exc_info=True)
                    st.error(f"Fehler bei der Vorschau: {e}")


def _generate_suggestions(
    translation: Translation, sentence: Sentence, provider: ProviderConfig, service: TranslationService
) -> None:
    """Generate translation suggestions and cache them.

    Helper function extracted from render_natural_edit_mode().

    Args:
        translation: Parent translation
        sentence: Sentence to generate suggestions for
        provider: Provider to use
        service: Translation service
    """
    with st.spinner("Generiere Vorschläge..."):
        try:
            suggestions = service.get_sentence_suggestions(translation.uuid, sentence.uuid, provider, count=3)
            SessionCacheManager.set_suggestions(sentence.uuid, suggestions)
            st.success(f"{len(suggestions)} Vorschläge generiert!")
            st.rerun()
        except Exception as e:
            logger.error("Failed to generate suggestions: %s", str(e), exc_info=True)
            st.error(f"Fehler beim Generieren der Vorschläge: {e}")


# render_alignment_preview removed - now using AlignmentPreview component


def render_alignment_edit_mode(
    translation: Translation, sentence: Sentence, service: TranslationService, is_new: bool
) -> None:
    """Render manual word-by-word alignment editor using AlignmentEditor component.

    Refactored to use AlignmentEditor component (reduced from 146 lines to ~10 lines).

    Args:
        translation: Parent translation object
        sentence: Sentence to edit
        service: TranslationService for updates
        is_new: True if this is a newly created translation
    """
    context = AlignmentContext(sentence=sentence, translation=translation, service=service, is_new_translation=is_new)
    editor = AlignmentEditor(context)
    editor.render()


def _execute_translation() -> None:
    """Execute pending translation with progress display on result page."""
    pending = st.session_state.translation_pending
    st.session_state.translation_pending = None

    try:
        model = TranslationModel(
            text=pending["text"],
            title=pending["title"],
            source_language=pending["source_language"],
            target_language=pending["target_language"],
        )

        # Show progress header at the top
        st.markdown(f"### ✨ Neue Übersetzung: {model.title}")
        st.caption("Übersetzung wird erstellt...")

        # Progress container at the top
        progress_container = st.container()

        logger.info(
            "Translation initiated: title='%s', text_length=%d chars, source=%s, target=%s, streaming=%s",
            pending["title"][:50],
            len(pending["text"]),
            pending["source_language"],
            pending["target_language"],
            pending["use_streaming"],
        )

        if pending["use_streaming"]:
            logger.info("Using streaming mode")
            try:
                with progress_container:
                    asyncio.run(_translate_text_streaming(model, pending["provider"]))
            except Exception as stream_error:
                logger.error("Streaming failed: %s", str(stream_error), exc_info=True)
                with progress_container:
                    st.error(f"❌ Streaming fehlgeschlagen: {str(stream_error)}")
                    st.info("Versuche Standardmodus ohne Fortschrittsanzeige...")
                _translate_text(model, pending["provider"], progress_container)
        else:
            logger.info("Using sync mode")
            _translate_text(model, pending["provider"], progress_container)
    finally:
        st.session_state.is_translating = False
        st.rerun()


def _translate_text(model: TranslationModel, provider: ProviderConfig | None, progress_container) -> None:
    """Translate text using configured provider."""
    if not provider:
        logger.warning("Translation attempted with no provider configured")
        with progress_container:
            st.error("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
        return

    source_lang = (
        "auto" if model.source_language == "Automatisch" else languages.get_language_code_by(model.source_language)
    )
    target_lang = languages.get_language_code_by(model.target_language)

    logger.info(
        "UI: Starting translation - provider=%s, source=%s, target=%s, title='%s'",
        provider.name,
        source_lang,
        target_lang,
        model.title,
    )

    try:
        with progress_container:
            with st.spinner(f"Übersetze Text mit {provider.name}..."):
                translator = PydanticAITranslator(provider)

                detected_language_info = None
                if source_lang == "auto":
                    detected_lang = translator.detect_language(model.text)
                    detected_language_info = f"✓ Erkannte Sprache: {detected_lang.upper()}"
                    source_lang = detected_lang

                translation = translator.translate(model.text, source_lang, target_lang)
                translation.title = model.title

                st.session_state.translation_result = translation
                st.session_state.is_new_translation = True
                st.session_state.detected_language_info = detected_language_info

        logger.info("UI: Translation successful - %d sentences", len(translation.sentences))
        with progress_container:
            st.success(f"✓ Übersetzung erfolgreich mit {provider.name}!")

    except Exception as e:
        logger.error("UI: Translation failed - %s: %s", type(e).__name__, str(e), exc_info=True)
        with progress_container:
            st.error(f"❌ Fehler bei der Übersetzung: {str(e)}")
            _show_error_details(e)


async def _translate_text_streaming(model: TranslationModel, provider: ProviderConfig | None) -> None:
    """Translate text using streaming with progress bar."""
    logger.info("Streaming function started")
    if not provider:
        logger.warning("Streaming: No provider configured")
        st.error("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
        return

    source_lang = (
        "auto" if model.source_language == "Automatisch" else languages.get_language_code_by(model.source_language)
    )
    target_lang = languages.get_language_code_by(model.target_language)

    try:
        logger.info("Streaming: Creating translator")
        translator = PydanticAITranslator(provider)

        detected_language_info = None
        if source_lang == "auto":
            logger.info("Streaming: Detecting language")
            detected_lang = translator.detect_language(model.text)
            detected_language_info = f"✓ Erkannte Sprache: {detected_lang.upper()}"
            source_lang = detected_lang

        logger.info("Streaming: Creating progress bar")
        progress_bar = st.progress(0.0, text="Starte Übersetzung...")

        logger.info("Streaming: Starting translation stream")
        translations = translator.translate_stream(model.text, source_lang, target_lang)
        logger.info("Streaming: Entering async loop")

        final_translation = None
        async for progress, translation in translations:
            if translation:
                logger.debug("Streaming: Progress update %.0f%%", progress * 100)
                progress_bar.progress(progress, text=f"Übersetze: {int(progress * 100)}%")

                translation.title = model.title
                st.session_state.translation_result = translation
                final_translation = translation

        progress_bar.empty()
        logger.info(
            "Streaming: UI Translation successful - %d sentences",
            len(final_translation.sentences) if final_translation else 0,
        )

        st.session_state.is_new_translation = True
        st.session_state.detected_language_info = detected_language_info

        st.success(f"✓ Übersetzung erfolgreich mit {provider.name}!")

    except Exception as e:
        logger.error("Streaming: Translation failed - %s: %s", type(e).__name__, str(e), exc_info=True)
        st.error(f"❌ Fehler bei der Übersetzung: {str(e)}")
        _show_error_details(e)


def _show_error_details(e: Exception) -> None:
    """Show detailed error information to the user."""
    error_details = []
    error_str = str(e).lower()

    if "api" in error_str or "key" in error_str:
        error_details.append("- Überprüfen Sie, ob der API-Schlüssel korrekt ist")
    if "model" in error_str:
        error_details.append("- Überprüfen Sie, ob der Modellname gültig ist")
    if "rate" in error_str or "quota" in error_str:
        error_details.append("- API-Limit erreicht oder Kontingent aufgebraucht")
    if "stream" in error_str:
        error_details.append("- Streaming nicht verfügbar für Ihr Konto")

    if error_details:
        st.info("Mögliche Ursachen:\n" + "\n".join(error_details))
    else:
        st.info("Bitte überprüfen Sie:\n- API-Schlüssel ist korrekt\n- Modellname ist gültig\n- Internetverbindung")


def _validate_all_sentences(translation: Translation) -> tuple[bool, int]:
    """Validate all sentences in a translation.

    Args:
        translation: Translation to validate

    Returns:
        Tuple of (all_valid, error_count)
        - all_valid: True if all sentences are valid
        - error_count: Number of sentences with errors
    """
    error_count = 0

    for sentence in translation.sentences:
        # Validate source words are mapped
        source_valid, _ = validate_source_words_mapped(sentence.word_alignments)
        # Validate natural translation completeness
        natural_valid, _ = validate_alignment_complete(sentence.natural_translation, sentence.word_alignments)

        if not source_valid or not natural_valid:
            error_count += 1

    return (error_count == 0, error_count)


# _extract_target_words_for_position removed - now in ui/components/alignment.py
