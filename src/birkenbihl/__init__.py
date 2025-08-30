"""Birkenbihl Language Learning App.

A Python application for digitalizing the Vera F. Birkenbihl language learning method.
"""

__version__ = "0.1.0"

from .models import Language, Translation, TranslationType, AudioData, AudioFormat, AudioQuality
from .protocols import TranslationProviderProtocol, AudioService

__all__ = [
    # Version
    "__version__",
    # Models
    "Language",
    "Translation", 
    "TranslationType",
    "AudioData",
    "AudioFormat", 
    "AudioQuality",
    # Protocols
    "TranslationProviderProtocol",
    "AudioService",
]