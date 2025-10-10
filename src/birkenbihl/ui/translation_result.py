"""Translation result and editing UI for the Birkenbihl application.

This module provides a unified view for:
1. Reviewing newly created translations (with optional progress bar)
2. Editing existing translations
Both flows share the same editing interface.
"""

import html
import logging
import re

import streamlit as st

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider

logger = logging.getLogger(__name__)


def render_translation_result_tab() -> None:
    """Render translation result view with editing capabilities.

    This view is used for both:
    - New translations (after creation, before saving)
    - Editing existing translations

    The difference is indicated by session state flags:
    - is_new_translation: True if this is a newly created translation
    - selected_translation_id: Set if editing an existing translation
    """
    # Determine if this is a new translation or editing existing
    is_new = st.session_state.get("is_new_translation", False)
    translation_id = st.session_state.get("selected_translation_id")

    if is_new:
        translation = st.session_state.get("translation_result")
        if not translation:
            st.error("Keine Übersetzung gefunden")
            return
    elif translation_id:
        try:
            storage = JsonStorageProvider()
            service = TranslationService(translator=None, storage=storage)
            translation = service.get_translation(translation_id)
            if not translation:
                st.error(f"Übersetzung {translation_id} nicht gefunden")
                return
        except Exception as e:
            st.error(f"Fehler beim Laden der Übersetzung: {e}")
            return
    else:
        st.error("Keine Übersetzung ausgewählt")
        return

    # Show detected language info for new translations
    detected_lang_info = st.session_state.get("detected_language_info")
    if is_new and detected_lang_info:
        st.info(detected_lang_info)

    # Render header with save/back buttons
    render_header(translation, is_new)

    st.markdown("---")

    # Render sentence editors
    try:
        storage = JsonStorageProvider()
        service = TranslationService(translator=None, storage=storage)

        for i, sentence in enumerate(translation.sentences, 1):
            render_sentence_editor(translation, sentence, i, service, is_new)
    except Exception as e:
        st.error(f"Fehler beim Rendern der Sätze: {e}")


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
            if st.button("💾 Speichern", type="primary", use_container_width=True):
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
    translation: Translation, sentence: Sentence, index: int, service: TranslationService, is_new: bool
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
        render_alignment_preview(sentence.word_alignments)

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

    Workflow:
    1. Select provider
    2. Generate suggestions via get_sentence_suggestions()
    3. User selects one suggestion
    4. Preview: Show new alignment via regenerate_alignment()
    5. Confirm or cancel

    Args:
        translation: Parent translation object
        sentence: Sentence to edit
        service: TranslationService for API calls
        is_new: True if this is a newly created translation
    """
    st.markdown("**Provider-Vorschläge generieren:**")

    providers = st.session_state.settings.providers
    if not providers:
        st.warning("Kein Provider konfiguriert. Bitte fügen Sie einen Provider in den Einstellungen hinzu.")
        return

    provider_names = [p.name for p in providers]
    current_provider = SettingsService.get_current_provider()
    default_index = 0
    if current_provider:
        default_index = next((i for i, p in enumerate(providers) if p.name == current_provider.name), 0)

    selected_provider_name = st.selectbox(
        "Provider wählen", options=provider_names, index=default_index, key=f"provider_select_{sentence.uuid}"
    )
    selected_provider = next(p for p in providers if p.name == selected_provider_name)

    suggestions_key = f"suggestions_{sentence.uuid}"

    if st.button("🔄 Vorschläge generieren", key=f"gen_suggestions_{sentence.uuid}"):
        with st.spinner("Generiere Vorschläge..."):
            try:
                suggestions = service.get_sentence_suggestions(
                    translation.uuid, sentence.uuid, selected_provider, count=3
                )
                st.session_state.suggestions_cache[suggestions_key] = suggestions
                st.success(f"{len(suggestions)} Vorschläge generiert!")
                st.rerun()
            except Exception as e:
                logger.error("Failed to generate suggestions: %s", str(e), exc_info=True)
                st.error(f"Fehler beim Generieren der Vorschläge: {e}")

    if suggestions_key in st.session_state.suggestions_cache:
        suggestions = st.session_state.suggestions_cache[suggestions_key]

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
                    render_alignment_preview(preview_alignments)

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

                                if suggestions_key in st.session_state.suggestions_cache:
                                    del st.session_state.suggestions_cache[suggestions_key]
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


def render_alignment_preview(alignments: list[WordAlignment]) -> None:
    """Render word alignments as preview.

    Displays word alignments in a visual format matching the main translation view,
    with source words above target words connected by arrows.

    Args:
        alignments: List of WordAlignment objects to display
    """
    alignment_html = "<div style='font-size: 13px; line-height: 1.8;'>"
    for alignment in alignments:
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


def render_alignment_edit_mode(
    translation: Translation, sentence: Sentence, service: TranslationService, is_new: bool
) -> None:
    """Render manual word-by-word alignment editor.

    Workflow:
    1. Show source words (read-only)
    2. For each source word: Multiselect target words
    3. Real-time validation via validate_alignment_complete()
    4. Save button (enabled only if valid)

    Args:
        translation: Parent translation object
        sentence: Sentence to edit
        service: TranslationService for updates
        is_new: True if this is a newly created translation
    """
    st.markdown("**Manuelle Word-by-Word Zuordnung:**")

    target_words = re.findall(r"\b\w+\b", sentence.natural_translation)
    source_words = [a.source_word for a in sentence.word_alignments]

    editor_key = f"alignment_editor_{sentence.uuid}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = {
            sw: _extract_target_words_for_source(sw, sentence.word_alignments) for sw in source_words
        }

    st.info(f"Natürliche Übersetzung: {sentence.natural_translation}")
    st.caption("Ordnen Sie jedem Wort der Originalsprache ein oder mehrere Wörter der Zielsprache zu.")

    st.markdown("**Zuordnung:**")

    for source_word in source_words:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"**{source_word}**")

        with col2:
            selected_targets = st.multiselect(
                "Zielwörter",
                options=target_words,
                default=st.session_state[editor_key].get(source_word, []),
                key=f"multiselect_{sentence.uuid}_{source_word}",
                label_visibility="collapsed",
            )
            st.session_state[editor_key][source_word] = selected_targets

    new_alignments = []
    for position, source_word in enumerate(source_words):
        target_list = st.session_state[editor_key][source_word]
        if target_list:
            target_word = "-".join(target_list)
            new_alignments.append(WordAlignment(source_word=source_word, target_word=target_word, position=position))

    st.markdown("---")
    is_valid, error_message = validate_alignment_complete(sentence.natural_translation, new_alignments)

    if is_valid:
        st.success("✓ Zuordnung ist vollständig und gültig")
    else:
        st.error(f"✗ Ungültige Zuordnung: {error_message}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "💾 Speichern",
            key=f"save_alignment_{sentence.uuid}",
            type="primary",
            disabled=not is_valid,
            use_container_width=True,
        ):
            try:
                if is_new:
                    # Update in-memory translation (not yet saved)
                    sentence.word_alignments = new_alignments
                    st.success("Zuordnung aktualisiert! (Nicht vergessen zu speichern)")
                else:
                    # Update persisted translation
                    service.update_sentence_alignment(translation.uuid, sentence.uuid, new_alignments)
                    st.success("Word-by-Word Zuordnung erfolgreich gespeichert!")

                del st.session_state[editor_key]
                st.rerun()
            except Exception as e:
                logger.error("Failed to save alignment: %s", str(e), exc_info=True)
                st.error(f"Fehler beim Speichern: {e}")

    with col2:
        if st.button("🔄 Zurücksetzen", key=f"reset_alignment_{sentence.uuid}", use_container_width=True):
            del st.session_state[editor_key]
            st.rerun()


def _extract_target_words_for_source(source_word: str, alignments: list[WordAlignment]) -> list[str]:
    """Extract target words for a given source word from alignments.

    Handles hyphenated combinations by splitting them into individual words.
    For example, "werde-vermissen" returns ["werde", "vermissen"].

    Args:
        source_word: Source word to find
        alignments: List of current alignments

    Returns:
        List of target words (split by hyphen if combined)
    """
    for alignment in alignments:
        if alignment.source_word == source_word:
            return alignment.target_word.split("-")
    return []
