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


# All supported languages (36 total) - European languages first, then others alphabetically
SUPPORTED_LANGUAGES: dict[str, Language] = {
    # European languages (alphabetically by German name)
    "bg": Language(code="bg", name_de="Bulgarisch", name_en="Bulgarian"),
    "da": Language(code="da", name_de="Dänisch", name_en="Danish"),
    "de": Language(code="de", name_de="Deutsch", name_en="German"),
    "en": Language(code="en", name_de="Englisch", name_en="English"),
    "et": Language(code="et", name_de="Estnisch", name_en="Estonian"),
    "fi": Language(code="fi", name_de="Finnisch", name_en="Finnish"),
    "fr": Language(code="fr", name_de="Französisch", name_en="French"),
    "el": Language(code="el", name_de="Griechisch", name_en="Greek"),
    "it": Language(code="it", name_de="Italienisch", name_en="Italian"),
    "hr": Language(code="hr", name_de="Kroatisch", name_en="Croatian"),
    "lv": Language(code="lv", name_de="Lettisch", name_en="Latvian"),
    "lt": Language(code="lt", name_de="Litauisch", name_en="Lithuanian"),
    "nl": Language(code="nl", name_de="Niederländisch", name_en="Dutch"),
    "no": Language(code="no", name_de="Norwegisch", name_en="Norwegian"),
    "pl": Language(code="pl", name_de="Polnisch", name_en="Polish"),
    "pt": Language(code="pt", name_de="Portugiesisch", name_en="Portuguese"),
    "ro": Language(code="ro", name_de="Rumänisch", name_en="Romanian"),
    "ru": Language(code="ru", name_de="Russisch", name_en="Russian"),
    "sv": Language(code="sv", name_de="Schwedisch", name_en="Swedish"),
    "sk": Language(code="sk", name_de="Slowakisch", name_en="Slovak"),
    "sl": Language(code="sl", name_de="Slowenisch", name_en="Slovenian"),
    "es": Language(code="es", name_de="Spanisch", name_en="Spanish"),
    "cs": Language(code="cs", name_de="Tschechisch", name_en="Czech"),
    "tr": Language(code="tr", name_de="Türkisch", name_en="Turkish"),
    "uk": Language(code="uk", name_de="Ukrainisch", name_en="Ukrainian"),
    "hu": Language(code="hu", name_de="Ungarisch", name_en="Hungarian"),
    # Non-European languages (alphabetically by German name)
    "ar": Language(code="ar", name_de="Arabisch", name_en="Arabic"),
    "zh": Language(code="zh", name_de="Chinesisch", name_en="Chinese"),
    "he": Language(code="he", name_de="Hebräisch", name_en="Hebrew"),
    "hi": Language(code="hi", name_de="Hindi", name_en="Hindi"),
    "id": Language(code="id", name_de="Indonesisch", name_en="Indonesian"),
    "ja": Language(code="ja", name_de="Japanisch", name_en="Japanese"),
    "ko": Language(code="ko", name_de="Koreanisch", name_en="Korean"),
    "fa": Language(code="fa", name_de="Persisch", name_en="Persian"),
    "th": Language(code="th", name_de="Thailändisch", name_en="Thai"),
    "vi": Language(code="vi", name_de="Vietnamesisch", name_en="Vietnamese"),
}


def get_german_name(code: str) -> str:
    """Get the German name for a language code.

    Args:
        code: ISO 639-1 language code

    Returns:
        German name of the language

    Raises:
        KeyError: If the language code is not supported
    """
    return SUPPORTED_LANGUAGES[code].name_de


def get_german_names() -> list[str]:
    """Get the German names of supported languages.

    Returns:
        List of German names
    """
    return [get_german_name(code) for code in SUPPORTED_LANGUAGES]


def get_language_code_by(name: str) -> str:
    """Get the ISO 639-1 language code for a German or English language name.

    Args:
        name: German or English name of the language

    Returns:
        ISO 639-1 language code

    Raises:
        KeyError: If the language name is not found
    """
    for code, language in SUPPORTED_LANGUAGES.items():
        if language.name_de == name or language.name_en == name:
            return code
    raise KeyError(f"Language '{name}' not found")


def get_english_name(code: str) -> str:
    """Get the English name for a language code.

    Args:
        code: ISO 639-1 language code

    Returns:
        English name of the language

    Raises:
        KeyError: If the language code is not supported
    """
    return SUPPORTED_LANGUAGES[code].name_en
