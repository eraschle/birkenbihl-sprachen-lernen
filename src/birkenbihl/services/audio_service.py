"""Audio service for text-to-speech."""

import pyttsx3
from typing import Optional


class AudioService:
    """Service for text-to-speech functionality."""
    
    def __init__(self) -> None:
        """Initialize the audio service."""
        self._engine: Optional[pyttsx3.Engine] = None
        self._initialize_engine()
    
    def _initialize_engine(self) -> None:
        """Initialize the TTS engine."""
        try:
            self._engine = pyttsx3.init()
            # Set properties for clearer speech
            if self._engine:
                self._engine.setProperty('rate', 150)  # Slower speech
                self._engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Warning: Could not initialize TTS engine: {e}")
            self._engine = None
    
    def speak(self, text: str, language: str = "en") -> None:
        """Speak the given text.
        
        Args:
            text: Text to speak
            language: Language code for pronunciation
        """
        if not self._engine:
            print(f"TTS not available. Would speak: {text}")
            return
        
        try:
            # Try to set voice based on language
            self._set_voice_for_language(language)
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            print(f"Error speaking text: {e}")
    
    def _set_voice_for_language(self, language: str) -> None:
        """Set appropriate voice for language.
        
        Args:
            language: Language code
        """
        if not self._engine:
            return
        
        voices = self._engine.getProperty('voices')
        if not voices:
            return
        
        # Try to find appropriate voice
        for voice in voices:
            voice_id = voice.id.lower()
            if language == "es" and ("spanish" in voice_id or "es" in voice_id):
                self._engine.setProperty('voice', voice.id)
                return
            elif language == "en" and ("english" in voice_id or "en" in voice_id):
                self._engine.setProperty('voice', voice.id)
                return
            elif language == "de" and ("german" in voice_id or "de" in voice_id):
                self._engine.setProperty('voice', voice.id)
                return
        
        # Fallback to first available voice
        if voices:
            self._engine.setProperty('voice', voices[0].id)
