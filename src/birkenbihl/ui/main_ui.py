"""Main user interface for the Birkenbihl app."""

from nicegui import ui, app
from typing import Optional

from ..models.translation import Translation
from ..services.translation_service import TranslationService
from ..services.audio_service import AudioService


class BirkenbihUI:
    """Main UI class for the Birkenbihl app."""
    
    def __init__(self, translation_service: TranslationService, audio_service: AudioService) -> None:
        """Initialize the UI.
        
        Args:
            translation_service: Service for translations
            audio_service: Service for audio playback
        """
        self._translation_service = translation_service
        self._audio_service = audio_service
        self._current_translation: Optional[Translation] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        ui.page_title("Birkenbihl Sprachlern-App")
        
        with ui.column().classes('w-full max-w-4xl mx-auto p-4'):
            ui.label("Birkenbihl Sprachlern-App").classes('text-3xl font-bold mb-4')
            
            # Input section
            with ui.card().classes('w-full mb-4'):
                ui.label("Text eingeben").classes('text-xl font-semibold mb-2')
                self._text_input = ui.textarea(
                    placeholder="Geben Sie hier den Text ein, den Sie übersetzen möchten..."
                ).classes('w-full')
                
                with ui.row().classes('mt-2'):
                    ui.button("Übersetzen", on_click=self._translate_text).classes('bg-blue-500')
                    ui.button("Audio abspielen", on_click=self._play_audio).classes('bg-green-500')
            
            # Translation display
            self._translation_card = ui.card().classes('w-full mb-4')
            with self._translation_card:
                ui.label("Übersetzung").classes('text-xl font-semibold mb-2')
                self._translation_content = ui.column()
            
            # Saved translations
            with ui.card().classes('w-full'):
                ui.label("Gespeicherte Übersetzungen").classes('text-xl font-semibold mb-2')
                self._saved_translations = ui.column()
                ui.button("Übersetzungen laden", on_click=self._load_translations).classes('mt-2')
        
        # Load existing translations on startup
        self._load_translations()
    
    def _translate_text(self) -> None:
        """Translate the input text."""
        text = self._text_input.value.strip()
        if not text:
            ui.notify("Bitte geben Sie einen Text ein.", type="warning")
            return
        
        try:
            # Show loading
            ui.notify("Übersetze...", type="info")
            
            # Translate and save
            translation = self._translation_service.translate_and_save(text)
            self._current_translation = translation
            
            # Display translation
            self._display_translation(translation)
            
            # Reload saved translations
            self._load_translations()
            
            ui.notify("Übersetzung erfolgreich!", type="positive")
            
        except Exception as e:
            ui.notify(f"Fehler bei der Übersetzung: {e}", type="negative")
    
    def _display_translation(self, translation: Translation) -> None:
        """Display a translation in the UI.
        
        Args:
            translation: Translation to display
        """
        self._translation_content.clear()
        
        with self._translation_content:
            # Original text
            ui.label(f"Original ({translation.source_lang.upper()}):").classes('font-semibold')
            ui.label(translation.original_text).classes('mb-4 p-2 bg-gray-100 rounded')
            
            # Natural translation
            ui.label("Natürliche Übersetzung:").classes('font-semibold')
            ui.label(translation.natural_translation).classes('mb-4 p-2 bg-blue-50 rounded')
            
            # Word-by-word translation with alignment
            ui.label("Wort-für-Wort Übersetzung:").classes('font-semibold')
            self._display_word_alignment(translation.original_text, translation.word_by_word_translation)
    
    def _display_word_alignment(self, original: str, word_by_word: str) -> None:
        """Display word-by-word alignment.
        
        Args:
            original: Original text
            word_by_word: Word-by-word translation
        """
        original_words = original.split()
        translated_words = word_by_word.split()
        
        with ui.grid(columns=2).classes('gap-2 p-2 bg-yellow-50 rounded'):
            # Headers
            ui.label("Original").classes('font-semibold text-center')
            ui.label("Wort-für-Wort").classes('font-semibold text-center')
            
            # Align words (simple approach)
            max_words = max(len(original_words), len(translated_words))
            
            for i in range(max_words):
                original_word = original_words[i] if i < len(original_words) else ""
                translated_word = translated_words[i] if i < len(translated_words) else ""
                
                ui.label(original_word).classes('text-center p-1 border rounded')
                ui.label(translated_word).classes('text-center p-1 border rounded')
    
    def _play_audio(self) -> None:
        """Play audio for the current translation."""
        if not self._current_translation:
            ui.notify("Keine Übersetzung zum Abspielen verfügbar.", type="warning")
            return
        
        try:
            # Play original text
            self._audio_service.speak(
                self._current_translation.original_text, 
                self._current_translation.source_lang
            )
            ui.notify("Audio wird abgespielt...", type="info")
        except Exception as e:
            ui.notify(f"Fehler beim Abspielen: {e}", type="negative")
    
    def _load_translations(self) -> None:
        """Load and display saved translations."""
        try:
            translations = self._translation_service.get_all_translations()
            
            self._saved_translations.clear()
            
            if not translations:
                with self._saved_translations:
                    ui.label("Keine gespeicherten Übersetzungen gefunden.").classes('text-gray-500')
                return
            
            with self._saved_translations:
                for translation in reversed(translations[-10:]):  # Show last 10
                    with ui.card().classes('w-full mb-2'):
                        with ui.row().classes('w-full items-center'):
                            with ui.column().classes('flex-grow'):
                                ui.label(f"{translation.original_text[:50]}...").classes('font-medium')
                                ui.label(f"{translation.source_lang.upper()} → {translation.target_lang.upper()}").classes('text-sm text-gray-500')
                            
                            ui.button(
                                "Anzeigen", 
                                on_click=lambda t=translation: self._show_saved_translation(t)
                            ).classes('bg-gray-500')
        
        except Exception as e:
            ui.notify(f"Fehler beim Laden der Übersetzungen: {e}", type="negative")
    
    def _show_saved_translation(self, translation: Translation) -> None:
        """Show a saved translation.
        
        Args:
            translation: Translation to show
        """
        self._current_translation = translation
        self._text_input.value = translation.original_text
        self._display_translation(translation)
