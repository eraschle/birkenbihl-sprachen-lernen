"""Main entry point for the Birkenbihl Language Learning App.

This module initializes the SQLite database, starts the NiceGUI app,
and connects all services for the Birkenbihl language learning method.
"""

from pathlib import Path

import nicegui as ni
from nicegui import app, ui
from sqlmodel import Session, SQLModel, create_engine, select

from . import __version__
from .config import load_config
from .models.translation import Language, Translation, TranslationResult, TranslationType
from .providers.pydantic_ai_provider import PydanticAITranslationProvider
# Conditional import due to Python 3.13 audioop compatibility
try:
    from .services.audio_service import EdgeTTSAudioService
    AUDIO_AVAILABLE = True
except ImportError:
    EdgeTTSAudioService = None
    AUDIO_AVAILABLE = False


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, database_url: str = "sqlite:///src/translations.db") -> None:
        """Initialize database service.
        
        Args:
            database_url: SQLite database URL
        """
        # Ensure database directory exists
        db_path = Path(database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(database_url, echo=False)
        self._create_tables()
        self._seed_languages()
    
    def _create_tables(self) -> None:
        """Create database tables."""
        SQLModel.metadata.create_all(self.engine)
    
    def _seed_languages(self) -> None:
        """Seed initial languages if not exist."""
        with Session(self.engine) as session:
            # Check if languages already exist
            existing = session.exec(select(Language)).first()
            if existing:
                return
                
            # Add default languages
            languages = [
                Language(code="de", name="Deutsch", native_name="Deutsch"),
                Language(code="en", name="English", native_name="English"),
                Language(code="es", name="Spanish", native_name="Español"),
            ]
            
            for lang in languages:
                session.add(lang)
            session.commit()
    
    def get_session(self) -> Session:
        """Get database session."""
        return Session(self.engine)
    
    def get_languages(self) -> list[Language]:
        """Get all active languages."""
        with self.get_session() as session:
            return session.exec(select(Language).where(Language.is_active == True)).all()
    
    def save_translation(self, translation: Translation) -> Translation:
        """Save translation to database."""
        with self.get_session() as session:
            session.add(translation)
            session.commit()
            session.refresh(translation)
            return translation
    
    def get_translation_history(self, limit: int = 50) -> list[Translation]:
        """Get translation history ordered by creation date."""
        with self.get_session() as session:
            return session.exec(
                select(Translation)
                .order_by(Translation.created_at.desc())
                .limit(limit)
            ).all()
    
    def search_translations(self, search_text: str, limit: int = 20) -> list[Translation]:
        """Search translations by source or translated text."""
        with self.get_session() as session:
            return session.exec(
                select(Translation)
                .where(
                    (Translation.source_text.contains(search_text)) |
                    (Translation.translated_text.contains(search_text))
                )
                .order_by(Translation.created_at.desc())
                .limit(limit)
            ).all()
    
    def get_translations_by_language_pair(
        self, 
        source_lang_id: int, 
        target_lang_id: int,
        limit: int = 20
    ) -> list[Translation]:
        """Get translations for specific language pair."""
        with self.get_session() as session:
            return session.exec(
                select(Translation)
                .where(
                    (Translation.source_language_id == source_lang_id) &
                    (Translation.target_language_id == target_lang_id)
                )
                .order_by(Translation.created_at.desc())
                .limit(limit)
            ).all()




class BirkenbihApp:
    """Main Birkenbihl Learning App."""
    
    def __init__(self) -> None:
        """Initialize the app with services."""
        self.config = load_config()
        self.db = DatabaseService(self.config.database.database_url)
        
        # Initialize real services only
        model_string = self.config.get_ai_model_string()
        self.translation_provider = PydanticAITranslationProvider(
            model=model_string,
            api_key=self.config.ai_provider.api_key
        )
        
        # Initialize audio service if available
        if AUDIO_AVAILABLE and EdgeTTSAudioService:
            self.audio_service = EdgeTTSAudioService()
        else:
            self.audio_service = None
            
        self.languages = self.db.get_languages()
        
        # UI state
        self.source_text = ""
        self.source_language = None
        self.target_language = None
        self.current_result: TranslationResult | None = None
    
    def create_ui(self) -> None:
        """Create the main user interface."""
        ui.page_title("Birkenbihl Sprachlernapp")
        
        with ui.header().style("background-color: #1976d2"):
            ui.label(f"Birkenbihl Lernmethode v{__version__}").style("font-size: 1.5rem; font-weight: bold")
        
        with ui.column().style("max-width: 1200px; margin: 0 auto; padding: 20px"):
            # Language selection
            with ui.card().style("width: 100%; margin-bottom: 20px"):
                ui.label("Sprachen auswählen").style("font-size: 1.2rem; font-weight: bold")
                
                with ui.row().style("width: 100%; gap: 20px"):
                    with ui.column().style("flex: 1"):
                        ui.label("Ausgangssprache:")
                        self.source_lang_select = ui.select(
                            options={lang.code: f"{lang.name} ({lang.code.upper()})" for lang in self.languages},
                            value="es"
                        ).style("width: 100%")
                    
                    with ui.column().style("flex: 1"):
                        ui.label("Zielsprache:")
                        self.target_lang_select = ui.select(
                            options={lang.code: f"{lang.name} ({lang.code.upper()})" for lang in self.languages},
                            value="de"
                        ).style("width: 100%")
            
            # Text input
            with ui.card().style("width: 100%; margin-bottom: 20px"):
                ui.label("Text eingeben").style("font-size: 1.2rem; font-weight: bold")
                self.text_input = ui.textarea(
                    placeholder="Text hier eingeben zum Übersetzen...",
                    value="Lo que parecía no importante"
                ).style("width: 100%; min-height: 120px")
                
                with ui.row().style("justify-content: space-between; margin-top: 10px"):
                    ui.button("🔄 Übersetzen", on_click=self.translate_text).props("color=primary")
                    ui.button("🔊 Original anhören", on_click=self.play_audio).props("color=secondary")
            
            # Results
            self.results_container = ui.column().style("width: 100%")
            
            # Show initial example
            self._show_example()
    
    def _show_example(self) -> None:
        """Show example translation on startup."""
        example_result = TranslationResult(
            natural_translation="Das was schien nicht wichtig", 
            word_by_word_translation="Das  was  schien   nicht  wichtig",
            formatted_decoding="Lo   que  parecía  no     importante\nDas  was  schien   nicht  wichtig"
        )
        self._display_results(example_result)
    
    async def translate_text(self) -> None:
        """Translate the input text."""
        text = self.text_input.value.strip()
        if not text:
            ui.notify("Bitte Text eingeben!", type="warning")
            return
        
        source_lang = self.source_lang_select.value
        target_lang = self.target_lang_select.value
        
        if source_lang == target_lang:
            ui.notify("Ausgangs- und Zielsprache müssen unterschiedlich sein!", type="warning") 
            return
        
        try:
            # Show loading
            ui.notify("Übersetze...", type="info")
            
            # Translate using real PydanticAI provider
            result = await self.translation_provider.translate_birkenbihl(text, source_lang, target_lang)
            # Convert to display format
            display_result = TranslationResult(
                natural_translation=result.natural_translation,
                word_by_word_translation=result.word_for_word_translation,
                formatted_decoding=result.formatted_translation
            )
            
            self.current_result = display_result
            
            # Save to database
            source_lang_obj = next((l for l in self.languages if l.code == source_lang), None)
            target_lang_obj = next((l for l in self.languages if l.code == target_lang), None)
            
            if source_lang_obj and target_lang_obj:
                # Save natural translation
                natural_translation = Translation(
                    source_text=text,
                    source_language_id=source_lang_obj.id,
                    target_language_id=target_lang_obj.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text=display_result.natural_translation
                )
                self.db.save_translation(natural_translation)
                
                # Save word-for-word translation
                word_translation = Translation(
                    source_text=text,
                    source_language_id=source_lang_obj.id,
                    target_language_id=target_lang_obj.id,
                    translation_type=TranslationType.WORD_FOR_WORD,
                    translated_text=display_result.word_by_word_translation
                )
                self.db.save_translation(word_translation)
            
            # Display results
            self._display_results(display_result)
            ui.notify("Übersetzung erfolgreich!", type="positive")
            
        except Exception as e:
            ui.notify(f"Fehler bei der Übersetzung: {str(e)}", type="negative")
    
    def _format_alignment(self, original: str, word_for_word: str) -> str:
        """Format alignment for display."""
        original_words = original.split()
        word_for_word_words = word_for_word.split()
        
        # Simple alignment
        max_len = max(len(w) for w in original_words + word_for_word_words) if original_words and word_for_word_words else 10
        
        original_line = "  ".join(w.ljust(max_len) for w in original_words)
        translated_line = "  ".join(w.ljust(max_len) for w in word_for_word_words)
        
        return f"{original_line}\n{translated_line}"
    
    def _display_results(self, result: TranslationResult) -> None:
        """Display translation results."""
        self.results_container.clear()
        
        with self.results_container:
            # Natural translation
            with ui.card().style("width: 100%; margin-bottom: 20px"):
                ui.label("Natürliche Übersetzung").style("font-size: 1.1rem; font-weight: bold")
                ui.label(result.natural_translation).style("font-size: 1rem; padding: 10px; background-color: #e3f2fd; border-radius: 5px")
            
            # Word-for-word (Dekodierung)
            with ui.card().style("width: 100%"):
                ui.label("Wort-für-Wort Dekodierung").style("font-size: 1.1rem; font-weight: bold")
                
                # Display formatted decoding with monospace font for alignment
                with ui.element("pre").style(
                    "font-family: 'Courier New', monospace; "
                    "font-size: 1rem; "
                    "padding: 15px; "
                    "background-color: #f5f5f5; "
                    "border-radius: 5px; "
                    "line-height: 2; "
                    "overflow-x: auto"
                ):
                    ui.html(result.formatted_decoding.replace("\n", "<br>"))
    
    async def play_audio(self) -> None:
        """Play audio of the source text."""
        text = self.text_input.value.strip()
        if not text:
            ui.notify("Bitte Text eingeben!", type="warning")
            return
        
        source_lang = self.source_lang_select.value
        
        try:
            ui.notify("Generiere Audio...", type="info")
            
            # Generate and play audio using real EdgeTTS service
            if self.audio_service:
                audio_data = await self.audio_service.generate_speech(text, source_lang)
                self.audio_service.play_audio(audio_data)
            else:
                ui.notify("⚠️ Audio nicht verfügbar (Python 3.13 Kompatibilitätsproblem)", type="warning")
                
            ui.notify("Audio wird abgespielt", type="positive")
            
        except Exception as e:
            ui.notify(f"Fehler beim Vorlesen: {str(e)}", type="negative")


def create_app() -> BirkenbihApp:
    """Create and configure the Birkenbihl app."""
    app = BirkenbihApp()
    app.create_ui()
    return app


def main() -> None:
    """Main entry point for CLI start."""
    print(f"🚀 Starting Birkenbihl Sprachlernapp v{__version__}")
    
    # Create and start the app
    birkenbihl_app = create_app()
    
    # Configure NiceGUI
    ui.run(
        title="Birkenbihl Sprachlernapp",
        native=True,  # Use native window
        port=8080,
        show=True,
        reload=False,
        dark=False
    )


if __name__ == "__main__":
    main()