"""Word alignment editor widgets."""

from birkenbihl.gui.widgets.alignment.draggable_word_tag import DraggableWordTag, TagState, TagType
from birkenbihl.gui.widgets.alignment.drop_zone import AlignmentDropZone
from birkenbihl.gui.widgets.alignment.unassigned_pool import UnassignedWordsPool

__all__ = [
    "DraggableWordTag",
    "TagState",
    "TagType",
    "AlignmentDropZone",
    "UnassignedWordsPool",
]
