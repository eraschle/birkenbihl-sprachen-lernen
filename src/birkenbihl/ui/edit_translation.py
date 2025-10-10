"""Translation editing UI for the Birkenbihl application."""

import html
import re

import streamlit as st

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


def render_edit_translation_tab() -> None:
    """Render translation editing view with sentence-by-sentence editing.

    Loads the selected translation from session state and displays an editor
    interface with two editing modes for each sentence:
    - Mode A: Natural translation editing with provider suggestions
    - Mode B: Manual word-by-word alignment editing
    """
    translation_id = st.session_state.selected_translation_id
    if not translation_id:
        st.error("Keine Übersetzung ausgewählt")
        return

    try:
        storage = JsonStorageProvider()
        service = TranslationService(translator=None, storage=storage)
        translation = service.get_translation(translation_id)

        if not translation:
            st.error(f"Übersetzung {translation_id} nicht gefunden")
            return

        render_header(translation)

        st.markdown("---")
        st.markdown("**Sätze bearbeiten**")

        for i, sentence in enumerate(translation.sentences, 1):
            render_sentence_editor(translation, sentence, i, service)

    except Exception as e:
        st.error(f"Fehler beim Laden der Übersetzung: {e}")
        return


def render_header(translation: Translation) -> None:
    """Render translation editor header with back button.

    Displays translation title, metadata (language pair, sentence count, last modified),
    and a back button to return to the translation list.

    Args:
        translation: Translation being edited
    """
    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"### ✏️ {translation.title}")
        message = f"{translation.source_language.upper()} → {translation.target_language.upper()} | "
        message += f"{len(translation.sentences)} Sätze | "
        message += f"Zuletzt geändert: {translation.updated_at.strftime('%d.%m.%Y %H:%M')}"
        st.caption(message)

    with col2:
        if st.button("← Zurück", use_container_width=True):
            st.session_state.current_view = "Meine Übersetzungen"
            st.session_state.selected_translation_id = None
            st.rerun()


def render_sentence_editor(
    translation: Translation, sentence: Sentence, index: int, service: TranslationService
) -> None:
    """Render editor for a single sentence with two editing modes.

    Creates an expandable section for each sentence showing:
    - Current source text and natural translation
    - Tab 1: Natural translation editing mode
    - Tab 2: Word-by-word alignment editing mode

    Args:
        translation: Parent translation object
        sentence: Sentence to edit
        index: Sentence number (1-based)
        service: TranslationService for updates
    """
    preview_text = sentence.source_text[:60]
    if len(sentence.source_text) > 60:
        preview_text += "..."

    with st.expander(f"Satz {index}: {preview_text}", expanded=False):
        st.markdown("**Aktuell:**")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Original: {sentence.source_text}")
        with col2:
            st.success(f"Natürlich: {sentence.natural_translation}")

        tab1, tab2 = st.tabs(["🔄 Natürliche Übersetzung ändern", "🔧 Word-by-Word bearbeiten"])

        with tab1:
            render_natural_edit_mode(translation, sentence, service)

        with tab2:
            render_alignment_edit_mode(translation, sentence, service)


def render_natural_edit_mode(translation: Translation, sentence: Sentence, service: TranslationService) -> None:
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
                                service.update_sentence_natural(
                                    translation.uuid, sentence.uuid, selected_suggestion, selected_provider
                                )
                                st.success("Übersetzung erfolgreich aktualisiert!")
                                if suggestions_key in st.session_state.suggestions_cache:
                                    del st.session_state.suggestions_cache[suggestions_key]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Speichern: {e}")

                    with col2:
                        if st.button("✗ Abbrechen", key=f"cancel_natural_{sentence.uuid}"):
                            st.rerun()

                except Exception as e:
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


def render_alignment_edit_mode(translation: Translation, sentence: Sentence, service: TranslationService) -> None:
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
    """
    st.markdown("**Manuelle Word-by-Word Zuordnung:**")

    target_words = [w for w in re.findall(r"\b\w+\b", sentence.natural_translation)]
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
                service.update_sentence_alignment(translation.uuid, sentence.uuid, new_alignments)
                st.success("Word-by-Word Zuordnung erfolgreich gespeichert!")
                del st.session_state[editor_key]
                st.rerun()
            except Exception as e:
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
