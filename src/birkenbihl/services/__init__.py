"""Services for the Birkenbihl Learning App."""

# Conditional import for audio service due to Python 3.13 compatibility
try:
    from .audio_service import EdgeTTSAudioService
    __all__ = ["EdgeTTSAudioService"]
except ImportError:
    EdgeTTSAudioService = None
    __all__ = []