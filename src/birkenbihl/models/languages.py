"""Central language definitions for the Birkenbihl application.

This module provides language codes (ISO 639-1) and their display names in German and English.
Supported languages include European languages (prioritized) and other common languages.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    """Language definition with ISO code and localized names."""

    code: str  # ISO 639-1 code
    name_de: str  # German name
    name_en: str  # English name
