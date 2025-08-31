"""Configuration management for Birkenbihl Language Learning App."""

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AIProviderConfig(BaseModel):
    """Configuration for AI translation provider."""
    
    provider: str = Field(default="openai", description="AI provider name")
    model: str = Field(default="gpt-4o", description="Model to use")
    api_key: str | None = Field(default=None, description="API key")
    base_url: str | None = Field(default=None, description="Custom API base URL")


class AudioConfig(BaseModel):
    """Configuration for audio/TTS settings."""
    
    default_voice_de: str = Field(default="de-DE-KatjaNeural", description="Default German voice")
    default_voice_es: str = Field(default="es-ES-ElviraNeural", description="Default Spanish voice") 
    default_voice_en: str = Field(default="en-US-AriaNeural", description="Default English voice")
    speech_rate: float = Field(default=1.0, ge=0.1, le=3.0, description="Speech rate")
    audio_quality: str = Field(default="medium", description="Audio quality")


class DatabaseConfig(BaseModel):
    """Configuration for database settings."""
    
    database_url: str = Field(default="sqlite:///src/translations.db", description="Database URL")
    echo_sql: bool = Field(default=False, description="Echo SQL queries")


class UIConfig(BaseModel):
    """Configuration for UI settings."""
    
    theme: str = Field(default="light", description="UI theme")
    default_source_lang: str = Field(default="es", description="Default source language")
    default_target_lang: str = Field(default="de", description="Default target language")
    auto_play_audio: bool = Field(default=False, description="Auto-play audio after translation")


class BirkenbihIConfig(BaseModel):
    """Main configuration for Birkenbihl app."""
    
    ai_provider: AIProviderConfig = Field(default_factory=AIProviderConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    @classmethod
    def load_from_env(cls) -> "BirkenbihIConfig":
        """Load configuration from environment variables."""
        config = cls()
        
        # AI Provider settings
        if api_key := os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
            config.ai_provider.api_key = api_key
        
        if provider := os.getenv("AI_PROVIDER"):
            config.ai_provider.provider = provider
        
        if model := os.getenv("AI_MODEL"):
            config.ai_provider.model = model
        
        # Database settings
        if db_url := os.getenv("DATABASE_URL"):
            config.database.database_url = db_url
        
        return config
    
    def get_ai_model_string(self) -> str:
        """Get full model string for pydantic-ai."""
        if self.ai_provider.provider.lower() == "anthropic":
            return f"anthropic:{self.ai_provider.model}"
        elif self.ai_provider.provider.lower() == "openai":
            return f"openai:{self.ai_provider.model}"
        else:
            return self.ai_provider.model


def load_config() -> BirkenbihIConfig:
    """Load application configuration."""
    return BirkenbihIConfig.load_from_env()