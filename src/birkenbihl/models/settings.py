"""Application settings domain model."""

from typing import Literal

from pydantic import BaseModel, Field

WordAlignerType = Literal["llm", "jev"]


class ProviderConfig(BaseModel):
    """Configuration for a single AI provider.

    Represents a complete provider configuration including credentials,
    model selection, and default status.
    """

    name: str
    provider_type: str
    model: str
    api_key: str
    api_url: str | None = None
    is_default: bool = False


class AudioSettings(BaseModel):
    """Text-to-speech preferences for the listening phase.

    Piper runs locally and is used whenever it has a voice for the language, unless ElevenLabs is preferred.
    ElevenLabs needs an API key and covers languages Piper lacks.
    """

    provider: Literal["piper", "elevenlabs"] = "piper"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""  # empty: the provider's default voice
    # 1.0 = normal; slower helps beginners. 0.7 is ElevenLabs' minimum and where Piper still sounds natural.
    speech_speed: float = Field(default=1.0, ge=0.7, le=1.0)


class Settings(BaseModel):
    """Application configuration and preferences.

    Domain model for application settings including provider configurations
    and target language preference. Defaults are provided for all fields.
    """

    providers: list[ProviderConfig] = []
    target_language: str = "de"
    audio: AudioSettings = AudioSettings()
    # Word-by-word step: "llm" uses the translating provider, "jev" uses Jev (TypeSafe)
    word_aligner: WordAlignerType = "llm"
    jev_api_key: str | None = None  # None: pydantic-ai reads TYPESAFE_API_KEY from the environment

    def get_default_provider(self) -> ProviderConfig | None:
        """Get the default provider configuration.

        Returns the first provider marked as default, or the first provider
        if none are marked as default, or None if no providers exist.

        Returns:
            Default provider config or None
        """
        if not self.providers:
            return None

        for provider in self.providers:
            if provider.is_default:
                return provider

        return self.providers[0]
