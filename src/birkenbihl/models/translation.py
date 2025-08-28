"""Translation data models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class TranslationResult(BaseModel):
    """Result of a translation operation."""
    
    natural: str
    word_by_word: str


class Translation(SQLModel, table=True):
    """Stored translation entity."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    original_text: str = Field(index=True)
    source_lang: str = Field(max_length=2)
    target_lang: str = Field(max_length=2)
    natural_translation: str
    word_by_word_translation: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        
        from_attributes = True
