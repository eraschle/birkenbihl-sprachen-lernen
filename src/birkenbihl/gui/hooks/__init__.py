"""Hook system for post-processing alignments."""

from birkenbihl.gui.hooks.alignment_hooks import (
    AlignmentHook,
    AlignmentHookManager,
    HyphenateMultiWordsHook,
)

__all__ = [
    "AlignmentHook",
    "AlignmentHookManager",
    "HyphenateMultiWordsHook",
]
