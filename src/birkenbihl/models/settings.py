"""Application settings domain model."""

from pydantic import BaseModel


class ProviderConfig(BaseModel):
    """Configuration for a single AI provider.

    Represents a complete provider configuration including credentials,
    model selection, and default status.
    """

    name: str
    provider_type: str
    model: str
    api_key: str
    is_default: bool = False
    supports_streaming: bool = True


class Settings(BaseModel):
    """Application configuration and preferences.

    Domain model for application settings including provider configurations
    and target language preference. Defaults are provided for all fields.
    """

    providers: list[ProviderConfig] = []
    target_language: str = "de"

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
