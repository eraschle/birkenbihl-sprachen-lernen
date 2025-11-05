"""Core exceptions for Birkenbihl application.

Exception Hierarchy:
    BirkenbihError (base)
    ├── TranslationError (translation-related failures)
    ├── AudioError (audio generation/playback failures)
    └── ProviderError (external provider failures)
"""


class BirkenbihError(Exception):
    """Base exception for all Birkenbihl application errors."""


class TranslationError(BirkenbihError):
    """Raised when translation operations fail.

    Examples:
        - AI model returns invalid response
        - Language detection fails
        - Alignment generation fails
        - API call to translation provider fails
    """


class AudioError(BirkenbihError):
    """Raised when audio operations fail.

    Examples:
        - Text-to-speech generation fails
        - Audio file save fails
        - Unsupported language for TTS
        - Audio playback fails
    """


class ProviderError(BirkenbihError):
    """Raised when external provider operations fail.

    Examples:
        - Unsupported provider type
        - Provider configuration invalid
        - API authentication fails
        - Provider rate limit exceeded
    """
