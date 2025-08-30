"""Datenmodelle für die Birkenbihl Learning App."""

from .audio import AudioData, AudioFormat, AudioQuality
from .translation import Language, Translation, TranslationType, TranslationResult

__all__ = [
    "Language",
    "Translation", 
    "TranslationType",
    "TranslationResult",
    "AudioData",
    "AudioFormat",
    "AudioQuality",
]
