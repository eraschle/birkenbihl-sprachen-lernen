"""Core exceptions for Birkenbihl application.

Exception Hierarchy:
    BirkenbihError (base)
    ├── AudioError (audio generation/playback failures)
    └── ProviderError (external provider failures)
"""


class BirkenbihError(Exception):
    """Base exception for all Birkenbihl application errors."""


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
