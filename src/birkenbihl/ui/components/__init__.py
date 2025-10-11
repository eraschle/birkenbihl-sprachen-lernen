"""Reusable UI components following Clean Code principles.

This package contains modular, testable UI components that implement the UIComponent protocol.
Each component follows the Single Responsibility Principle and has minimal parameters (0-2).
"""

from birkenbihl.ui.components.alignment import AlignmentEditor, AlignmentPreview
from birkenbihl.ui.components.base import UIComponent
from birkenbihl.ui.components.buttons import ActionButtonGroup, BackButton, ButtonConfig, SaveCancelButtons
from birkenbihl.ui.components.provider import ProviderSelector, get_current_provider, get_providers_from_settings

__all__ = [
    "UIComponent",
    "AlignmentPreview",
    "AlignmentEditor",
    "ProviderSelector",
    "get_providers_from_settings",
    "get_current_provider",
    "ActionButtonGroup",
    "ButtonConfig",
    "SaveCancelButtons",
    "BackButton",
]
