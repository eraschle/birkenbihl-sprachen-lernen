"""Tests for language detection (langdetect, no AI call)."""

import pytest
from langdetect import LangDetectException

from birkenbihl.services.language_service import detect_language


class TestDetectLanguage:
    @pytest.mark.parametrize(
        ("text", "code"),
        [
            ("Yesterday I met some new people at the market.", "en"),
            ("Mas comprendo que llegó tu tiempo, que Dios te ha llamado.", "es"),
            ("Ich werde dich sehr vermissen, mein Freund.", "de"),
        ],
    )
    def test_detects_supported_languages(self, text: str, code: str) -> None:
        assert detect_language(text).code == code

    def test_same_text_gives_same_answer(self) -> None:
        text = "Hola"

        assert len({detect_language(text).code for _ in range(5)}) == 1

    def test_empty_text_raises(self) -> None:
        with pytest.raises(LangDetectException):
            detect_language("")
