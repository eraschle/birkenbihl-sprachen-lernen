"""Application settings with .env file integration."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Supports loading API keys and configuration from .env file.
    Defaults are provided for all fields to allow graceful startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    default_model: str = Field(default="openai:gpt-4", validation_alias="BIRKENBIHL_DEFAULT_MODEL")
    target_language: str = Field(default="de", validation_alias="BIRKENBIHL_TARGET_LANGUAGE")

    @classmethod
    def load_from_env(cls, env_file: str | Path = ".env") -> "Settings":
        """Load settings from specified .env file.

        Args:
            env_file: Path to .env file (defaults to .env in current directory)

        Returns:
            Settings instance with values from .env or defaults
        """
        from dotenv import dotenv_values

        env_path = Path(env_file)
        if not env_path.exists():
            return cls()

        env_vars = dotenv_values(env_path)
        filtered_vars = {k: v for k, v in env_vars.items() if v is not None}
        return cls(**filtered_vars)

    def save_to_env(self, env_file: str | Path = ".env") -> None:
        """Save current settings to .env file.

        Args:
            env_file: Path to .env file (defaults to .env in current directory)
        """
        env_path = Path(env_file)
        env_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        if self.openai_api_key:
            lines.append(f"OPENAI_API_KEY={self.openai_api_key}")
        if self.anthropic_api_key:
            lines.append(f"ANTHROPIC_API_KEY={self.anthropic_api_key}")
        lines.append(f"BIRKENBIHL_DEFAULT_MODEL={self.default_model}")
        lines.append(f"BIRKENBIHL_TARGET_LANGUAGE={self.target_language}")

        env_path.write_text("\n".join(lines) + "\n")
