"""Presenter layer for formatting domain models for display.

Follows Presentation Model pattern (Martin Fowler).
Separates domain logic from presentation logic.
"""

from birkenbihl.presenters.display_models import (
    AlignmentDisplayModel,
    SentenceDisplayModel,
    TranslationDisplayModel,
)
from birkenbihl.presenters.translation_presenter import TranslationPresenter

__all__ = [
    "TranslationPresenter",
    "TranslationDisplayModel",
    "SentenceDisplayModel",
    "AlignmentDisplayModel",
]
