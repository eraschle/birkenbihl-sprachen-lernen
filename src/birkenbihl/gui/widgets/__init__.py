"""Reusable UI widgets/components."""

from birkenbihl.gui.widgets import (
    alignment_editor,
    alignment_preview,
    base,
    language_combo,
    language_selector,
    progress_widget,
    provider_selector,
    sentence_card,
    tag_container,
    tag_widget,
)
from birkenbihl.gui.widgets.tag_container import TagContainer
from birkenbihl.gui.widgets.tag_widget import TagWidget

__all__ = [
    "base",
    "provider_selector",
    "language_selector",
    "language_combo",
    "progress_widget",
    "alignment_preview",
    "alignment_editor",
    "sentence_card",
    "tag_container",
    "tag_widget",
    "TagContainer",
    "TagWidget",
]
