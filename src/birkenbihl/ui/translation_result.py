"""Translation result and editing UI for the Birkenbihl application.

This module provides a unified view for:
1. Reviewing newly created translations (with optional progress bar)
2. Editing existing translations
Both flows share the same editing interface.
"""

import asyncio
import html
import logging
import re

import streamlit as st
from pydantic import BaseModel

from birkenbihl.models import languages
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.models.validation import validate_alignment_complete, validate_source_words_mapped
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider

logger = logging.getLogger(__name__)


class TranslationModel(BaseModel):
    text: str
    title: str
    source_language: str
    target_language: str


def render_translation_result_tab() -> None:
    """Render translation result view with editing capabilities.

    This view is used for both:
    - New translations (after creation, before saving)
    - Editing existing translations
    - Active translation (showing progress)

    The difference is indicated by session state flags:
    - is_translating: True if translation is currently running
    - is_new_translation: True if this is a newly created translation
    - selected_translation_id: Set if editing an existing translation
    """
    # Check if translation is currently running
    is_translating = st.session_state.get("is_translating", False)

    # If translating, execute the translation first
    if is_translating and st.session_state.get("translation_pending"):
        _execute_translation()
        return  # Return early as _execute_translation will rerun

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
    storage = JsonStorageProvider()
    service = TranslationService(translator=None, storage=storage)

    for i, sentence in enumerate(translation.sentences, 1):
        try:
            render_sentence_editor(translation, sentence, i, service, is_new)
        except Exception as e:
            # Show error for this specific sentence but continue with others
            st.error(f"⚠️ Satz {i} kann nicht bearbeitet werden: {str(e)}")
            if "default value" in str(e).lower() and "not part of the options" in str(e).lower():
                st.info("💡 Mögliche Ursache: Einige Wörter aus der Word-by-Word-Zuordnung kommen nicht in der natürlichen Übersetzung vor. Bitte ändern Sie die natürliche Übersetzung.")
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

    # Extract target words from natural translation
    target_words = re.findall(r"\b\w+\b", sentence.natural_translation)

    # Also include all words from existing alignments to ensure defaults are in options
    existing_target_words = set()
    for alignment in sentence.word_alignments:
        # Split by hyphen and filter out empty/whitespace strings
        words = [w.strip() for w in alignment.target_word.split("-")]
        words = [w for w in words if w]  # Remove empty strings and whitespace
        existing_target_words.update(words)

    # Combine both sets (maintain order, no duplicates)
    target_words_set = set(target_words)
    for word in existing_target_words:
        if word not in target_words_set:
            target_words.append(word)
            target_words_set.add(word)

    source_words = [a.source_word for a in sentence.word_alignments]

    editor_key = f"alignment_editor_{sentence.uuid}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = {
            f"{idx}_{sw}": _extract_target_words_for_position(idx, sentence.word_alignments)
            for idx, sw in enumerate(source_words)
        }

    st.info(f"Natürliche Übersetzung: {sentence.natural_translation}")
    st.caption("Ordnen Sie jedem Wort der Originalsprache ein oder mehrere Wörter der Zielsprache zu.")

    st.markdown("**Zuordnung:**")

    # Track invalid defaults for warning
    invalid_defaults = []

    for idx, source_word in enumerate(source_words):
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"**{source_word}**")

        with col2:
            # Use index to make key unique even if source_word appears multiple times
            source_key = f"{idx}_{source_word}"

            # Get default values and filter out any that aren't in options
            raw_defaults = st.session_state[editor_key].get(source_key, [])
            valid_defaults = [d for d in raw_defaults if d in target_words]

            # Track invalid defaults for warning
            invalid = [d for d in raw_defaults if d not in target_words]
            if invalid:
                invalid_defaults.extend([(source_word, invalid)])

            selected_targets = st.multiselect(
                "Zielwörter",
                options=target_words,
                default=valid_defaults,
                key=f"multiselect_{sentence.uuid}_{source_key}",
                label_visibility="collapsed",
            )
            st.session_state[editor_key][source_key] = selected_targets

    # Show warning if there were invalid defaults
    if invalid_defaults:
        warning_msg = "⚠️ Einige Wörter konnten nicht zugeordnet werden:\n"
        for src, invalids in invalid_defaults:
            invalid_str = ", ".join([f"'{w}'" if w.strip() else "'[Leerzeichen]'" for w in invalids])
            warning_msg += f"\n- '{src}' → {invalid_str}"
        warning_msg += "\n\n💡 Tipp: Ändern Sie die natürliche Übersetzung, um eine bessere Word-by-Word-Zuordnung zu ermöglichen."
        st.warning(warning_msg)

    new_alignments = []
    for position, source_word in enumerate(source_words):
        source_key = f"{position}_{source_word}"
        target_list = st.session_state[editor_key][source_key]
        if target_list:
            target_word = "-".join(target_list)
            new_alignments.append(WordAlignment(source_word=source_word, target_word=target_word, position=position))

    st.markdown("---")

    # Validate source words are mapped
    source_valid, source_error = validate_source_words_mapped(new_alignments)
    # Validate natural translation completeness
    natural_valid, natural_error = validate_alignment_complete(sentence.natural_translation, new_alignments)

    is_valid = source_valid and natural_valid

    if is_valid:
        st.success("✓ Zuordnung ist vollständig und gültig")
    else:
        if not source_valid:
            st.error(f"✗ {source_error}")
            st.info("💡 Tipp: Ändern Sie die natürliche Übersetzung, sodass jedes Quellwort ein Zielwort hat. Beispiel: 'unwichtig' → 'nicht wichtig'")
        if not natural_valid:
            st.error(f"✗ {natural_error}")

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

    source_lang = "auto" if model.source_language == "Automatisch" else languages.get_language_code_by(model.source_language)
    target_lang = languages.get_language_code_by(model.target_language)

    logger.info("UI: Starting translation - provider=%s, source=%s, target=%s, title='%s'",
                provider.name, source_lang, target_lang, model.title)

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

    source_lang = "auto" if model.source_language == "Automatisch" else languages.get_language_code_by(model.source_language)
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
        logger.info("Streaming: UI Translation successful - %d sentences", len(final_translation.sentences) if final_translation else 0)

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


def _extract_target_words_for_position(position: int, alignments: list[WordAlignment]) -> list[str]:
    """Extract target words for a given position from alignments.

    Handles hyphenated combinations by splitting them into individual words.
    For example, "werde-vermissen" returns ["werde", "vermissen"].

    Args:
        position: Position index of the word to find
        alignments: List of current alignments

    Returns:
        List of target words (split by hyphen if combined)
    """
    for alignment in alignments:
        if alignment.position == position:
            return alignment.target_word.split("-")
    return []
