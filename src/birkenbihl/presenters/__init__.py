"""Presenter layer for view-agnostic data preparation.

Presenters convert domain models to presentation models with:
- Computed fields (formatted dates, display indices)
- View-ready structure (eliminates logic duplication)
- Immutable presentation data
"""

from birkenbihl.presenters.models import SentencePresentation, TranslationPresentation
from birkenbihl.presenters.translation_presenter import TranslationPresenter

__all__ = [
    "SentencePresentation",
    "TranslationPresentation",
    "TranslationPresenter",
]
