"""Tests for LanguageCombo widget."""

import pytest
from pytestqt.qtbot import QtBot

from birkenbihl.gui.widgets.language_combo import LanguageCombo
from birkenbihl.models.languages import Language


@pytest.fixture
def language_combo(qtbot: QtBot) -> LanguageCombo:
    """Create LanguageCombo widget."""
    combo = LanguageCombo(None)
    qtbot.addWidget(combo)
    return combo


@pytest.fixture
def sample_languages() -> list[Language]:
    """Sample languages for testing."""
    return [
        Language(code="de", name_de="Deutsch", name_en="German"),
        Language(code="en", name_de="Englisch", name_en="English"),
        Language(code="es", name_de="Spanisch", name_en="Spanish"),
    ]


@pytest.mark.ui
def test_init(language_combo: LanguageCombo) -> None:
    """Test widget initialization."""
    assert language_combo is not None
    assert language_combo.count() == 0


@pytest.mark.ui
def test_add_language(language_combo: LanguageCombo, sample_languages: list[Language]) -> None:
    """Test adding a single language."""
    lang = sample_languages[0]
    language_combo.add_language(lang)

    assert language_combo.count() == 1
    assert language_combo.itemText(0) == "Deutsch"
    assert language_combo.itemData(0).code == "de"


@pytest.mark.ui
def test_add_languages(language_combo: LanguageCombo, sample_languages: list[Language]) -> None:
    """Test adding multiple languages."""
    language_combo.add_languages(sample_languages)

    assert language_combo.count() == 3
    assert language_combo.itemText(0) == "Deutsch"
    assert language_combo.itemText(1) == "Englisch"
    assert language_combo.itemText(2) == "Spanisch"


@pytest.mark.ui
def test_current_language(language_combo: LanguageCombo, sample_languages: list[Language]) -> None:
    """Test getting current language."""
    language_combo.add_languages(sample_languages)

    current = language_combo.current_language()
    assert current is not None
    assert current.code == "de"

    language_combo.setCurrentIndex(1)
    current = language_combo.current_language()
    assert current is not None
    assert current.code == "en"
    assert current.name_de == "Englisch"


@pytest.mark.ui
def test_set_language(language_combo: LanguageCombo, sample_languages: list[Language]) -> None:
    """Test setting language by code."""
    language_combo.add_languages(sample_languages)

    result = language_combo.set_language("es")
    assert result is True
    assert language_combo.currentIndex() == 2

    current = language_combo.current_language()
    assert current is not None
    assert current.code == "es"


@pytest.mark.ui
def test_set_language_not_found(language_combo: LanguageCombo, sample_languages: list[Language]) -> None:
    """Test setting non-existent language."""
    language_combo.add_languages(sample_languages)

    result = language_combo.set_language("fr")
    assert result is False
    assert language_combo.currentIndex() == 0


@pytest.mark.ui
def test_current_language_empty(language_combo: LanguageCombo) -> None:
    """Test current_language returns None when empty."""
    assert language_combo.current_language() is None
