"""Alignment post-processing hooks for transforming source mappings to WordAlignments.

This module provides a hook system for processing word alignment mappings from the UI
into final WordAlignment objects. The primary hook hyphenates multiple target words
assigned to a single source word.
"""

from typing import Protocol

from birkenbihl.models.translation import WordAlignment


class AlignmentHook(Protocol):
    """Protocol for alignment post-processing hooks.

    Hooks process source word mappings and convert them to final WordAlignments.
    This allows extensible post-processing of alignments before they are saved.
    """

    def process(
        self,
        source_mappings: dict[str, list[str]],
        target_words: list[str],
    ) -> list[WordAlignment]:
        """Process source mappings and return final WordAlignments.

        Args:
            source_mappings: Dict mapping source words to list of target words
                Example: {"Yo": ["Ich"], "extrañaré": ["werde", "vermissen"]}
            target_words: Complete list of target words from natural translation (for ordering)

        Returns:
            List of WordAlignment objects with position numbers
        """
        ...


class HyphenateMultiWordsHook:
    """Verbindet mehrere Zielwörter mit Bindestrich.

    Dieser Hook verarbeitet die UI-Zuordnungen und erstellt finale WordAlignment-Objekte.
    Wenn einem Quellwort mehrere Zielwörter zugeordnet sind, werden diese mit Bindestrich verbunden.

    Beispiel:
        Input:  {"extrañaré": ["werde", "vermissen"]}
        Output: WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=0)
    """

    def process(
        self,
        source_mappings: dict[str, list[str]],
        target_words: list[str],
    ) -> list[WordAlignment]:
        """Process mappings by hyphenating multiple target words.

        Rules:
        1. If source word has 0 target words → skip (not mapped)
        2. If source word has 1 target word → use as-is
        3. If source word has 2+ target words → join with hyphen: "werde-vermissen"
        4. Position is sequential (0, 1, 2, ...)
        5. Order follows source_mappings dict iteration order

        Args:
            source_mappings: Dict of source → list of target words
            target_words: Complete list (for reference, not currently used)

        Returns:
            List of WordAlignment objects
        """
        alignments: list[WordAlignment] = []
        position = 0

        for source_word, target_word_list in source_mappings.items():
            # Skip unmapped source words
            if len(target_word_list) == 0:
                continue

            # Single target word: use as-is
            if len(target_word_list) == 1:
                target_word = target_word_list[0]
            else:
                # Multiple target words: join with hyphen
                target_word = "-".join(target_word_list)

            alignments.append(
                WordAlignment(
                    source_word=source_word,
                    target_word=target_word,
                    position=position,
                )
            )
            position += 1

        return alignments


class AlignmentHookManager:
    """Manager for alignment post-processing hooks.

    Allows registration of multiple hooks and applies them in sequence.
    Default: Registers HyphenateMultiWordsHook.
    """

    def __init__(self) -> None:
        """Initialize with default hooks."""
        self._hooks: list[AlignmentHook] = []
        self._register_default_hooks()

    def _register_default_hooks(self) -> None:
        """Register default hooks."""
        self.register(HyphenateMultiWordsHook())

    def register(self, hook: AlignmentHook) -> None:
        """Register a new hook.

        Args:
            hook: Hook to register
        """
        self._hooks.append(hook)

    def process(
        self,
        source_mappings: dict[str, list[str]],
        target_words: list[str],
    ) -> list[WordAlignment]:
        """Process source mappings through all registered hooks.

        Currently applies only the last hook (as we only have one).
        Future: Could chain hooks if needed.

        Args:
            source_mappings: Dict of source → list of target words
            target_words: Complete list of target words

        Returns:
            Final list of WordAlignment objects
        """
        # For now, apply the last hook (we only have one)
        # Future: Could implement hook chaining if needed
        if not self._hooks:
            return []

        result = self._hooks[-1].process(source_mappings, target_words)
        return result
