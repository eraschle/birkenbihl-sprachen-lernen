"""Alignment components for word-by-word translation editing.

This module provides components for displaying and editing word alignments
according to the Birkenbihl method.
"""

import html
import logging
import re

import streamlit as st

from birkenbihl.models.translation import WordAlignment
from birkenbihl.models.validation import validate_alignment_complete, validate_source_words_mapped
from birkenbihl.ui.models.context import AlignmentContext

logger = logging.getLogger(__name__)


class AlignmentPreview:
    """Renders word alignments preview.

    This component displays word alignments in a visual format with source words
    above target words, connected by arrows.

    Replaces duplicated code from:
    - translation_result.py:323-346
    - edit_translation.py:208-231
    """

    def __init__(self, alignments: list[WordAlignment]) -> None:
        """Initialize alignment preview.

        Args:
            alignments: List of WordAlignment objects to display
        """
        self.alignments = alignments

    def render(self) -> None:
        """Render the alignment preview to Streamlit."""
        alignment_html = self._build_alignment_html()
        st.markdown(alignment_html, unsafe_allow_html=True)

    def _build_alignment_html(self) -> str:
        """Build HTML for alignment visualization.

        Returns:
            HTML string with styled alignment boxes
        """
        html_parts = ["<div style='font-size: 13px; line-height: 1.8;'>"]

        for alignment in self.alignments:
            source_escaped = html.escape(alignment.source_word)
            target_escaped = html.escape(alignment.target_word)

            message = "<span style='display: inline-block; margin: 2px; padding: 4px 8px; "
            message += "background-color: #f0f2f6; border-radius: 6px; border: 1px solid #ddd;'>"
            message += f"<div style='color: #0066cc; font-weight: 600; font-size: 12px;'>{source_escaped}</div>"
            message += "<div style='color: #666; font-size: 10px;'>↓</div>"
            message += f"<div style='color: #009900; font-weight: 600; font-size: 12px;'>{target_escaped}</div>"
            message += "</span>"
            html_parts.append(message)

        html_parts.append("</div>")
        return "".join(html_parts)


class AlignmentEditor:
    """Manual word-by-word alignment editor.

    Provides interface for manually mapping source words to target words.
    Includes real-time validation and state management.

    Refactors translation_result.py:349-473 (124 lines → ~60 lines)
    """

    def __init__(self, context: AlignmentContext) -> None:
        """Initialize alignment editor.

        Args:
            context: AlignmentContext with sentence, translation, service, and is_new flag
        """
        self.context = context
        self.sentence = context.sentence
        self.editor_key = f"alignment_editor_{self.sentence.uuid}"

    def render(self) -> None:
        """Render the alignment editor interface."""
        st.markdown("**Manuelle Word-by-Word Zuordnung:**")

        target_words = self._extract_target_words()
        source_words = [a.source_word for a in self.sentence.word_alignments]

        self._initialize_editor_state(source_words)

        st.info(f"Natürliche Übersetzung: {self.sentence.natural_translation}")
        st.caption("Ordnen Sie jedem Wort der Originalsprache ein oder mehrere Wörter der Zielsprache zu.")

        invalid_defaults = self._render_word_mapping(source_words, target_words)
        new_alignments = self._build_alignments(source_words)

        self._show_validation_warnings(invalid_defaults)
        self._validate_and_render_actions(new_alignments)

    def _extract_target_words(self) -> list[str]:
        """Extract target words from natural translation and existing alignments.

        Returns:
            List of unique target words maintaining order
        """
        # Extract words from natural translation
        target_words = re.findall(r"\b\w+\b", self.sentence.natural_translation)

        # Include words from existing alignments
        existing_words = set()
        for alignment in self.sentence.word_alignments:
            words = [w.strip() for w in alignment.target_word.split("-")]
            words = [w for w in words if w]
            existing_words.update(words)

        # Combine maintaining order
        target_words_set = set(target_words)
        for word in existing_words:
            if word not in target_words_set:
                target_words.append(word)
                target_words_set.add(word)

        return target_words

    def _initialize_editor_state(self, source_words: list[str]) -> None:
        """Initialize session state for editor.

        Args:
            source_words: List of source words to initialize
        """
        if self.editor_key not in st.session_state:
            st.session_state[self.editor_key] = {
                f"{idx}_{sw}": _extract_target_words_for_position(idx, self.sentence.word_alignments)
                for idx, sw in enumerate(source_words)
            }

    def _render_word_mapping(self, source_words: list[str], target_words: list[str]) -> list[tuple[str, list[str]]]:
        """Render word mapping interface.

        Args:
            source_words: List of source words
            target_words: List of available target words

        Returns:
            List of (source_word, invalid_defaults) tuples for warnings
        """
        st.markdown("**Zuordnung:**")
        invalid_defaults = []

        for idx, source_word in enumerate(source_words):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown(f"**{source_word}**")

            with col2:
                source_key = f"{idx}_{source_word}"
                raw_defaults = st.session_state[self.editor_key].get(source_key, [])
                valid_defaults = [d for d in raw_defaults if d in target_words]

                invalid = [d for d in raw_defaults if d not in target_words]
                if invalid:
                    invalid_defaults.append((source_word, invalid))

                selected_targets = st.multiselect(
                    "Zielwörter",
                    options=target_words,
                    default=valid_defaults,
                    key=f"multiselect_{self.sentence.uuid}_{source_key}",
                    label_visibility="collapsed",
                )
                st.session_state[self.editor_key][source_key] = selected_targets

        return invalid_defaults

    def _build_alignments(self, source_words: list[str]) -> list[WordAlignment]:
        """Build new alignments from current state.

        Args:
            source_words: List of source words

        Returns:
            List of WordAlignment objects
        """
        new_alignments = []
        for position, source_word in enumerate(source_words):
            source_key = f"{position}_{source_word}"
            target_list = st.session_state[self.editor_key][source_key]
            if target_list:
                target_word = "-".join(target_list)
                new_alignments.append(
                    WordAlignment(source_word=source_word, target_word=target_word, position=position)
                )
        return new_alignments

    def _show_validation_warnings(self, invalid_defaults: list[tuple[str, list[str]]]) -> None:
        """Show warnings for invalid word mappings.

        Args:
            invalid_defaults: List of (source_word, invalid_words) tuples
        """
        if invalid_defaults:
            warning_msg = "⚠️ Einige Wörter konnten nicht zugeordnet werden:\n"
            for src, invalids in invalid_defaults:
                invalid_str = ", ".join([f"'{w}'" if w.strip() else "'[Leerzeichen]'" for w in invalids])
                warning_msg += f"\n- '{src}' → {invalid_str}"
            warning_msg += (
                "\n\n💡 Tipp: Ändern Sie die natürliche Übersetzung, "
                "um eine bessere Word-by-Word-Zuordnung zu ermöglichen."
            )
            st.warning(warning_msg)

    def _validate_and_render_actions(self, new_alignments: list[WordAlignment]) -> None:
        """Validate alignments and render action buttons.

        Args:
            new_alignments: New alignment configuration to validate
        """
        st.markdown("---")

        # Validate alignments
        source_valid, source_error = validate_source_words_mapped(new_alignments)
        natural_valid, natural_error = validate_alignment_complete(self.sentence.natural_translation, new_alignments)
        is_valid = source_valid and natural_valid

        # Show validation status
        if is_valid:
            st.success("✓ Zuordnung ist vollständig und gültig")
        else:
            if not source_valid:
                st.error(f"✗ {source_error}")
                message = "💡 Tipp: Ändern Sie die natürliche Übersetzung, sodass jedes Quellwort ein Zielwort hat. "
                message += "Beispiel: 'unwichtig' → 'nicht wichtig'"
                st.info(message)
            if not natural_valid:
                st.error(f"✗ {natural_error}")

        # Render action buttons
        self._render_action_buttons(is_valid, new_alignments)

    def _render_action_buttons(self, is_valid: bool, new_alignments: list[WordAlignment]) -> None:
        """Render save and reset buttons.

        Args:
            is_valid: Whether current alignment is valid
            new_alignments: New alignments to save
        """
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "💾 Speichern",
                key=f"save_alignment_{self.sentence.uuid}",
                type="primary",
                disabled=not is_valid,
                use_container_width=True,
            ):
                self._save_alignment(new_alignments)

        with col2:
            if st.button("🔄 Zurücksetzen", key=f"reset_alignment_{self.sentence.uuid}", use_container_width=True):
                self._reset_editor()

    def _save_alignment(self, new_alignments: list[WordAlignment]) -> None:
        """Save the new alignment configuration.

        Args:
            new_alignments: Alignments to save
        """
        try:
            if self.context.is_new_translation:
                # Update in-memory translation (not yet saved)
                self.sentence.word_alignments = new_alignments
                st.success("Zuordnung aktualisiert! (Nicht vergessen zu speichern)")
            else:
                # Update persisted translation
                self.context.service.update_sentence_alignment(
                    self.context.translation.uuid, self.sentence.uuid, new_alignments
                )
                st.success("Word-by-Word Zuordnung erfolgreich gespeichert!")

            # Clean up editor state
            if self.editor_key in st.session_state:
                del st.session_state[self.editor_key]
            st.rerun()
        except Exception as e:
            logger.error("Failed to save alignment: %s", str(e), exc_info=True)
            st.error(f"Fehler beim Speichern: {e}")

    def _reset_editor(self) -> None:
        """Reset editor to initial state."""
        if self.editor_key in st.session_state:
            del st.session_state[self.editor_key]
        st.rerun()


def _extract_target_words_for_position(position: int, alignments: list[WordAlignment]) -> list[str]:
    """Extract target words for a given position from alignments.

    Helper function used by AlignmentEditor to initialize default values.

    Args:
        position: Position index of the word to find
        alignments: List of current alignments

    Returns:
        List of target words (split by hyphen if combined)
    """
    for alignment in alignments:
        if alignment.position == position:
            words = alignment.target_word.split("-")
            return [w.strip() for w in words if w.strip()]
    return []
