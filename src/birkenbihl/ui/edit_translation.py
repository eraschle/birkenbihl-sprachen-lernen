"""Translation editing UI for the Birkenbihl application.

Refactored to use Clean Code components and state management.
"""

import streamlit as st

from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.ui.components import AlignmentPreview, BackButton, ProviderSelector
from birkenbihl.ui.models.context import ProviderSelectorContext
from birkenbihl.ui.services.translation_ui_service import TranslationUIServiceImpl
from birkenbihl.ui.state.cache import SessionCacheManager
from birkenbihl.ui.state.session import SessionStateManager


def render_edit_translation_tab() -> None:
    """Render translation editing view with sentence-by-sentence editing.

    Refactored to use StateManager and TranslationUIService.
    """
    state = SessionStateManager()
    translation_id = state.selected_translation_id

    if not translation_id:
        st.error("Keine Übersetzung ausgewählt")
        return

    try:
        translation = TranslationUIServiceImpl.get_translation(translation_id)

        if not translation:
            st.error(f"Übersetzung {translation_id} nicht gefunden")
            return

        render_header(translation)

        st.markdown("---")
        st.markdown("**Sätze bearbeiten**")

        service = TranslationUIServiceImpl.get_service()
        for i, sentence in enumerate(translation.sentences, 1):
            render_sentence_editor(translation, sentence, i, service)

    except Exception as e:
        st.error(f"Fehler beim Laden der Übersetzung: {e}")
        return


def render_header(translation: Translation) -> None:
    """Render translation editor header with back button.

    Refactored to use BackButton component and StateManager.

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
        back_button = BackButton(key="edit_translation_back")
        if back_button.render():
            _navigate_back()


def _navigate_back() -> None:
    """Navigate back to translations list."""
    state = SessionStateManager()
    state.current_view = "Meine Übersetzungen"
    state.selected_translation_id = None
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
                                service.update_sentence_natural(
                                    translation.uuid, sentence.uuid, selected_suggestion, selected_provider
                                )
                                st.success("Übersetzung erfolgreich aktualisiert!")
                                SessionCacheManager.clear_suggestions(sentence.uuid)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Speichern: {e}")

                    with col2:
                        if st.button("✗ Abbrechen", key=f"cancel_natural_{sentence.uuid}"):
                            st.rerun()

                except Exception as e:
                    st.error(f"Fehler bei der Vorschau: {e}")


# render_alignment_preview removed - now using AlignmentPreview component


def _generate_suggestions(translation: Translation, sentence: Sentence, provider: ProviderConfig, service) -> None:
    """Generate translation suggestions and cache them.

    Helper function to keep render_natural_edit_mode() clean.

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
            st.error(f"Fehler beim Generieren der Vorschläge: {e}")


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


# _extract_target_words_for_source removed - now in ui/components/alignment.py
