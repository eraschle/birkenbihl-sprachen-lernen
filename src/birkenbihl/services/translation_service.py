"""Translation service implementation."""

from typing import Optional

from sqlmodel import Session, create_engine, select

from ..models.translation import Translation, TranslationResult
from ..protocols.translation import TranslationProvider


class TranslationService:
    """Service for handling translations and storage."""
    
    def __init__(self, provider: TranslationProvider, db_url: str = "sqlite:///translations.db") -> None:
        """Initialize the service.
        
        Args:
            provider: Translation provider to use
            db_url: Database URL for SQLite
        """
        self._provider = provider
        self._engine = create_engine(db_url)
        
        # Create tables
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(self._engine)
    
    def translate_and_save(self, text: str, target_lang: str = "de") -> Translation:
        """Translate text and save to database.
        
        Args:
            text: Text to translate
            target_lang: Target language (default: German)
            
        Returns:
            Saved translation entity
        """
        # Detect source language
        source_lang = self._provider.detect_language(text)
        
        # Check if translation already exists
        with Session(self._engine) as session:
            existing = session.exec(
                select(Translation).where(
                    Translation.original_text == text,
                    Translation.source_lang == source_lang,
                    Translation.target_lang == target_lang
                )
            ).first()
            
            if existing:
                return existing
        
        # Translate
        result = self._provider.translate(text, source_lang, target_lang)
        
        # Save to database
        translation = Translation(
            original_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            natural_translation=result.natural,
            word_by_word_translation=result.word_by_word
        )
        
        with Session(self._engine) as session:
            session.add(translation)
            session.commit()
            session.refresh(translation)
        
        return translation
    
    def get_translation(self, translation_id: int) -> Optional[Translation]:
        """Get translation by ID.
        
        Args:
            translation_id: ID of the translation
            
        Returns:
            Translation entity or None
        """
        with Session(self._engine) as session:
            return session.get(Translation, translation_id)
    
    def get_all_translations(self) -> list[Translation]:
        """Get all translations from database.
        
        Returns:
            List of all translations
        """
        with Session(self._engine) as session:
            return list(session.exec(select(Translation)).all())
    
    def search_translations(self, query: str) -> list[Translation]:
        """Search translations by original text.
        
        Args:
            query: Search query
            
        Returns:
            List of matching translations
        """
        with Session(self._engine) as session:
            return list(session.exec(
                select(Translation).where(
                    Translation.original_text.contains(query)
                )
            ).all())
