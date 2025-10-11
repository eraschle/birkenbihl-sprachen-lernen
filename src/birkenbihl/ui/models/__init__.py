"""UI-specific data models and context objects.

This package contains Parameter Objects (contexts) used to reduce
function parameters and improve code clarity.
"""

from birkenbihl.ui.models.context import (
    AlignmentContext,
    ProviderSelectorContext,
    SentenceEditorContext,
)

__all__ = [
    "AlignmentContext",
    "ProviderSelectorContext",
    "SentenceEditorContext",
]
