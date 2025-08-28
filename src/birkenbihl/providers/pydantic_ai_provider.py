"""Pydantic AI translation provider implementation."""

import os
from typing import Any

from langdetect import detect
from pydantic import BaseModel
from pydantic_ai import Agent

from ..models.translation import TranslationResult
from ..protocols.translation import TranslationProvider


class BirkenbihTranslation(BaseModel):
    """Structured output for Birkenbihl translations."""
    
    natural: str
    word_by_word: str


class PydanticAITranslationProvider:
    """Translation provider using Pydantic AI."""
    
    def __init__(self, model: str = "openai:gpt-4", api_key: str | None = None) -> None:
        """Initialize the provider.
        
        Args:
            model: Model to use (e.g., "openai:gpt-4", "anthropic:claude-3-sonnet")
            api_key: API key for the model provider
        """
        self._model = model
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        self._agent = Agent(
            self._model,
            system_prompt=self._get_system_prompt(),
        )
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        """Translate text using Birkenbihl method."""
        try:
            import asyncio
            import threading
            
            prompt = f"""
            Übersetze den folgenden {self._get_language_name(source_lang)} Text ins {self._get_language_name(target_lang)} 
            nach der Vera F. Birkenbihl Methode:

            Text: "{text}"

            Erstelle zwei Übersetzungen:
            1. Eine natürliche, fließende Übersetzung
            2. Eine Wort-für-Wort Übersetzung (jedes Wort einzeln übersetzt)

            Beispiel für Wort-für-Wort: "Yo te extrañaré" → "Ich dich vermissen-werde"
            
            Antworte nur mit den beiden Übersetzungen, getrennt durch "|||":
            [Natürliche Übersetzung]|||[Wort-für-Wort Übersetzung]
            """
            
            # Run in a separate thread to avoid event loop conflicts
            def run_translation():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(self._agent.run(prompt))
                    finally:
                        loop.close()
                except Exception as e:
                    print(f"Thread error: {e}")
                    return None
            
            # Run in thread
            result = None
            thread = threading.Thread(target=lambda: setattr(threading.current_thread(), 'result', run_translation()))
            thread.start()
            thread.join()
            result = getattr(thread, 'result', None)
            
            if result is None:
                raise Exception("Translation failed - no result from AI")
            
            # Debug: Print the raw response
            print(f"DEBUG: Raw AI response: {result}")
            print(f"DEBUG: Response type: {type(result)}")
            print(f"DEBUG: Available attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
            
            # Parse the response - use the correct attribute
            if hasattr(result, 'message'):
                response_text = str(result.message)
            elif hasattr(result, 'content'):
                response_text = str(result.content)
            elif hasattr(result, 'text'):
                response_text = str(result.text)
            else:
                response_text = str(result)
            
            print(f"DEBUG: Response text: '{response_text}'")
            
            if "|||" in response_text:
                parts = response_text.split("|||")
                natural = parts[0].strip()
                word_by_word = parts[1].strip() if len(parts) > 1 else parts[0].strip()
            else:
                # Fallback: try to split by common patterns
                lines = response_text.strip().split('\n')
                if len(lines) >= 2:
                    natural = lines[0].strip()
                    word_by_word = lines[1].strip()
                else:
                    # Last fallback: use same text for both
                    natural = response_text.strip()
                    word_by_word = f"Wort-für-Wort: {response_text.strip()}"
            
            print(f"DEBUG: Natural: '{natural}'")
            print(f"DEBUG: Word-by-word: '{word_by_word}'")
            
            return TranslationResult(
                natural=natural,
                word_by_word=word_by_word
            )
            
        except Exception as e:
            print(f"ERROR in translate: {e}")
            # Return error message as translation
            return TranslationResult(
                natural=f"Fehler bei der Übersetzung: {str(e)}",
                word_by_word=f"Fehler: {str(e)}"
            )
    
    def detect_language(self, text: str) -> str:
        """Detect language of given text."""
        try:
            detected = detect(text)
            # Map common language codes
            lang_map = {
                "en": "en",
                "es": "es", 
                "de": "de",
                "ca": "es",  # Catalan -> Spanish
            }
            return lang_map.get(detected, "en")  # Default to English
        except Exception:
            return "en"  # Default fallback
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent."""
        return """
        Du bist ein Experte für die Vera F. Birkenbihl Sprachlernmethode. 
        
        Die Birkenbihl-Methode verwendet zwei Arten von Übersetzungen:
        1. Natürliche Übersetzung: Fließend und idiomatisch korrekt
        2. Wort-für-Wort Übersetzung: Jedes Wort einzeln übersetzt, um die Sprachstruktur zu verstehen
        
        Erstelle immer beide Übersetzungstypen. Die Wort-für-Wort Übersetzung soll helfen, 
        die Denkweise der Originalsprache zu verstehen.
        """
    
    def _get_language_name(self, lang_code: str) -> str:
        """Get language name from code."""
        names = {
            "en": "Englische",
            "es": "Spanische", 
            "de": "Deutsche"
        }
        return names.get(lang_code, "Unbekannte")
