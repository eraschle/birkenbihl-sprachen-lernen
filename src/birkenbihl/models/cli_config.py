"""Configuration models for CLI commands."""

from dataclasses import dataclass
from pathlib import Path

from birkenbihl.models.languages import Language


@dataclass
class TranslationConfig:
    """Configuration for translation command.

    Reduces parameter count from 6 to 1 (Single Responsibility Principle).
    """

    text: str
    source: Language | None
    target: Language
    title: str | None
    provider_name: str | None
    storage_path: Path | None
