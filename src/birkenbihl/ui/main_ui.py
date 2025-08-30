"""NiceGUI main interface for Birkenbihl learning app."""

import asyncio
from pathlib import Path

from nicegui import ui, app
from sqlmodel import Session

from birkenbihl.services.translation_service import TranslationService
from birkenbihl.services.audio_service import AudioService


class BirkenbihIUI:
    """Main UI for Birkenbihl language learning."""
    
    def __init__(self, translation_service: TranslationService, audio_service: AudioService):
        self.translation_service = translation_service
        self.audio_service = audio_service
        self.current_translation = None
    
    def create_ui(self):
        """Create the main user interface."""
        ui.page_title("Birkenbihl Sprachlern-App")
        
        with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
            ui.label("Birkenbihl Sprachlern-App").classes("text-3xl font-bold mb-6")
            
            # Input section
            with ui.card().classes("w-full p-4 mb-4"):
                ui.label("Text eingeben:").classes("text-lg font-medium mb-2")
                self.text_input = ui.textarea(
                    placeholder="Geben Sie hier den Text ein, den Sie übersetzen möchten..."
                ).classes("w-full").props("rows=3")
                
                with ui.row().classes("mt-4"):
                    self.source_lang = ui.select(
                        options={"es": "Español", "en": "English", "de": "Deutsch"},
                        value="es"
                    ).classes("w-32")
                    ui.label("→").classes("text-xl mx-2")
                    self.target_lang = ui.select(
                        options={"de": "Deutsch", "es": "Español", "en": "English"},
                        value="de"
                    ).classes("w-32")
                    
                    ui.button("Übersetzen", on_click=self.translate_text).classes("bg-blue-500 text-white px-6 py-2 ml-4")
            
            # Results section
            with ui.row().classes("w-full gap-4"):
                # Natural translation
                with ui.card().classes("flex-1 p-4"):
                    ui.label("Natürliche Übersetzung").classes("text-lg font-medium mb-3")
                    self.natural_result = ui.textarea(
                        placeholder="Die natürliche Übersetzung erscheint hier..."
                    ).classes("w-full").props("rows=5 readonly")
                
                # Word-by-word translation
                with ui.card().classes("flex-1 p-4"):
                    ui.label("Wort-für-Wort Dekodierung").classes("text-lg font-medium mb-3")
                    self.word_by_word_result = ui.html().classes("w-full font-mono text-sm")
            
            # Audio controls
            with ui.card().classes("w-full p-4 mt-4"):
                with ui.row().classes("items-center gap-4"):
                    self.play_button = ui.button(
                        "Audio abspielen", 
                        on_click=self.play_audio,
                        icon="play_arrow"
                    ).classes("bg-green-500 text-white").props("disable")
                    
                    self.save_button = ui.button(
                        "Übersetzung speichern",
                        on_click=self.save_translation,
                        icon="save"
                    ).classes("bg-purple-500 text-white").props("disable")
    
    async def translate_text(self):
        """Handle translation request."""
        text = self.text_input.value.strip()
        if not text:
            ui.notify("Bitte geben Sie einen Text ein.", type="warning")
            return
        
        source = self.source_lang.value
        target = self.target_lang.value
        
        if source == target:
            ui.notify("Quell- und Zielsprache müssen unterschiedlich sein.", type="warning")
            return
        
        # Show loading
        ui.notify("Übersetze...", type="info")
        
        try:
            # Get translations
            natural = await self.translation_service.translate_natural(text, source, target)
            word_by_word = await self.translation_service.translate_word_by_word(text, source, target)
            
            # Update UI
            self.natural_result.value = natural
            self._display_word_by_word(word_by_word)
            
            # Store current translation
            self.current_translation = {
                "text": text,
                "source": source,
                "target": target,
                "natural": natural,
                "word_by_word": word_by_word
            }
            
            # Enable buttons
            self.play_button.props(remove="disable")
            self.save_button.props(remove="disable")
            
            ui.notify("Übersetzung erfolgreich!", type="positive")
            
        except Exception as e:
            ui.notify(f"Fehler bei der Übersetzung: {str(e)}", type="negative")
    
    def _display_word_by_word(self, formatted_text: str):
        """Display word-by-word translation with proper formatting."""
        lines = formatted_text.split('\n')
        if len(lines) >= 2:
            html_content = f"""
            <div class="birkenbihl-translation">
                <div class="original-line" style="margin-bottom: 8px; font-family: monospace; white-space: pre;">{lines[0]}</div>
                <div class="translation-line" style="font-family: monospace; white-space: pre; color: #666;">{lines[1]}</div>
            </div>
            """
            self.word_by_word_result.content = html_content
        else:
            self.word_by_word_result.content = f"<pre>{formatted_text}</pre>"
    
    async def play_audio(self):
        """Play audio for the original text."""
        if not self.current_translation:
            return
        
        try:
            ui.notify("Generiere Audio...", type="info")
            audio_file = await self.audio_service.text_to_speech(
                self.current_translation["text"],
                self.current_translation["source"]
            )
            
            # Play audio in browser
            ui.audio(src=str(audio_file)).classes("hidden").props("autoplay")
            ui.notify("Audio wird abgespielt", type="positive")
            
        except Exception as e:
            ui.notify(f"Audio-Fehler: {str(e)}", type="negative")
    
    async def save_translation(self):
        """Save the current translation to database."""
        if not self.current_translation:
            return
        
        try:
            await self.translation_service.save_translation(
                self.current_translation["text"],
                self.current_translation["source"],
                self.current_translation["target"],
                self.current_translation["natural"],
                self.current_translation["word_by_word"]
            )
            ui.notify("Übersetzung gespeichert!", type="positive")
            
        except Exception as e:
            ui.notify(f"Speicher-Fehler: {str(e)}", type="negative")


async def create_app(translation_service: TranslationService, audio_service: AudioService):
    """Create and return the NiceGUI app."""
    birkenbihl_ui = BirkenbihIUI(translation_service, audio_service)
    birkenbihl_ui.create_ui()
    return birkenbihl_ui