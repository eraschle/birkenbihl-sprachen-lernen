"""Protocols for the Birkenbihl Learning App."""

from .audio import AudioService
from .translation import TranslationProviderProtocol

__all__ = [
    "AudioService",
    "TranslationProviderProtocol",
]