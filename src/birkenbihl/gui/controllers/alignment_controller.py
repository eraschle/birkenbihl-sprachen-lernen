"""Central controller for word alignment state management."""

from PySide6.QtCore import QObject, Signal


class AlignmentController(QObject):
    """Central state manager for word alignments.

    Responsibilities:
    - Track which target words are assigned to which source words
    - Provide list of available (unassigned) words
    - Notify all UI components when mappings change
    - Prevent duplicate assignments

    The controller maintains the invariant that each target word
    is assigned to at most one source word at any time.
    """

    mappings_changed = Signal()  # Emitted after any add/remove operation

    def __init__(
        self, target_words: list[str], initial_mappings: dict[str, list[str]] | None = None, parent: QObject | None = None
    ):
        """Initialize controller.

        Args:
            target_words: All target words from natural translation (in original order)
            initial_mappings: Initial source → target mappings (optional)
            parent: Parent QObject
        """
        super().__init__(parent)
        self._target_words = target_words  # Original order preserved
        self._source_mappings: dict[str, list[str]] = initial_mappings or {}

    def get_available_words(self, for_source_word: str | None = None) -> list[str]:
        """Get words not yet assigned (except to for_source_word).

        Returns words in original order from natural translation.

        Args:
            for_source_word: If provided, includes words already mapped to this source word

        Returns:
            List of available target words in natural translation order
        """
        # Collect all mapped words except for current source
        mapped = set()
        for source, targets in self._source_mappings.items():
            if source != for_source_word:
                mapped.update(targets)

        # Return words not yet mapped, in original order
        return [w for w in self._target_words if w not in mapped]

    def add_word(self, source_word: str, target_word: str) -> None:
        """Add word to source mapping, notify all listeners.

        Args:
            source_word: Source word
            target_word: Target word to add
        """
        if source_word not in self._source_mappings:
            self._source_mappings[source_word] = []

        # Prevent duplicates
        if target_word not in self._source_mappings[source_word]:
            self._source_mappings[source_word].append(target_word)
            self.mappings_changed.emit()

    def remove_word(self, source_word: str, target_word: str) -> None:
        """Remove word from source mapping, notify all listeners.

        Args:
            source_word: Source word
            target_word: Target word to remove
        """
        if source_word in self._source_mappings:
            try:
                self._source_mappings[source_word].remove(target_word)
                self.mappings_changed.emit()
            except ValueError:
                # Word not in list - silently ignore
                pass

    def has_available_words(self) -> bool:
        """Check if any words remain unassigned globally.

        Returns:
            True if at least one word is not assigned to any source
        """
        return len(self.get_available_words()) > 0

    def get_mappings(self) -> dict[str, list[str]]:
        """Get current mappings for serialization.

        Returns:
            Deep copy of current source → target mappings
        """
        return {k: v.copy() for k, v in self._source_mappings.items()}

    def get_assigned_words(self, source_word: str) -> list[str]:
        """Get words currently assigned to source_word.

        Args:
            source_word: Source word

        Returns:
            List of target words assigned to source (copy)
        """
        return self._source_mappings.get(source_word, []).copy()

    def clear_mappings(self) -> None:
        """Clear all mappings and notify listeners."""
        if self._source_mappings:
            self._source_mappings.clear()
            self.mappings_changed.emit()
