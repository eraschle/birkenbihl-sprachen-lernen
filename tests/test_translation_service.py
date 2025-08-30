"""Tests for translation service with focus on Birkenbihl formatting."""

import pytest
from unittest.mock import AsyncMock, Mock
from sqlmodel import Session, create_engine, SQLModel

from birkenbihl.models.translation import Translation, Language
from birkenbihl.protocols.translation import TranslationProvider


class MockTranslationProvider:
    """Mock provider for testing."""
    
    async def translate_natural(self, text: str, source_lang: str, target_lang: str) -> str:
        """Mock natural translation."""
        translations = {
            ("Lo que parecía no importante", "es", "de"): "Das was schien nicht wichtig",
            ("Tenlo por seguro", "es", "de"): "Hab es sicher",
            ("Fueron tantos bellos y malos momentos", "es", "de"): "Waren so viele schöne und schlechte Momente"
        }
        return translations.get((text, source_lang, target_lang), f"[{target_lang}] {text}")
    
    async def translate_word_by_word(self, text: str, source_lang: str, target_lang: str) -> str:
        """Mock word-by-word translation."""
        word_translations = {
            ("Lo que parecía no importante", "es", "de"): "Das was schien nicht wichtig",
            ("Tenlo por seguro", "es", "de"): "Hab-es für sicher",
            ("Fueron tantos bellos y malos momentos", "es", "de"): "Waren so-viele schöne und schlechte momente"
        }
        return word_translations.get((text, source_lang, target_lang), text)


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    
    # Add test languages
    de_lang = Language(code="de", name="Deutsch", created_at="2024-01-01T00:00:00")
    es_lang = Language(code="es", name="Español", created_at="2024-01-01T00:00:00")
    session.add(de_lang)
    session.add(es_lang)
    session.commit()
    
    yield session
    session.close()


@pytest.fixture
def mock_provider():
    """Create mock translation provider."""
    return MockTranslationProvider()


@pytest.fixture
def translation_service(mock_provider, db_session):
    """Create translation service with mocks."""
    # Import here to avoid module loading issues
    from birkenbihl.services.translation_service import TranslationService
    return TranslationService(mock_provider, db_session)


class TestTranslationService:
    """Test translation service functionality."""
    
    @pytest.mark.asyncio
    async def test_natural_translation(self, translation_service):
        """Test natural translation."""
        result = await translation_service.translate_natural(
            "Lo que parecía no importante", "es", "de"
        )
        assert result == "Das was schien nicht wichtig"
    
    @pytest.mark.asyncio
    async def test_word_by_word_translation(self, translation_service):
        """Test word-by-word translation."""
        result = await translation_service.translate_word_by_word(
            "Lo que parecía no importante", "es", "de"
        )
        # Should contain formatted alignment
        assert "Lo" in result
        assert "Das" in result
        assert "\n" in result  # Should have line break for alignment


class TestBirkenbihIFormatting:
    """Test Birkenbihl-specific formatting rules."""
    
    def test_format_birkenbihl_style_basic(self, translation_service):
        """Test basic Birkenbihl formatting."""
        original = "Lo que parecía no importante"
        translation = "Das was schien nicht wichtig"
        
        result = translation_service._format_birkenbihl_style(original, translation)
        lines = result.split('\n')
        
        assert len(lines) == 2
        # Check that words are properly aligned
        assert "Lo" in lines[0]
        assert "Das" in lines[1]
    
    def test_format_birkenbihl_style_spacing(self, translation_service):
        """Test proper spacing in Birkenbihl format."""
        original = "Tenlo por seguro"
        translation = "Hab-es für sicher"
        
        result = translation_service._format_birkenbihl_style(original, translation)
        lines = result.split('\n')
        
        # Should have 2 spaces between words as per spec
        assert "  " in lines[0]  # 2 spaces between words
        assert "  " in lines[1]  # 2 spaces between words
    
    def test_format_birkenbihl_style_alignment(self, translation_service):
        """Test vertical alignment in Birkenbihl format."""
        original = "Fueron tantos bellos"
        translation = "Waren so-viele schöne"
        
        result = translation_service._format_birkenbihl_style(original, translation)
        lines = result.split('\n')
        
        # Words should be left-justified to max width
        orig_words = lines[0].split('  ')
        trans_words = lines[1].split('  ')
        
        # Each position should have same width
        for orig, trans in zip(orig_words, trans_words):
            assert len(orig) == len(trans)
    
    def test_format_birkenbihl_style_complex_example(self, translation_service):
        """Test complex example from spec."""
        original = "Lo que parecía no importante"
        translation = "Das was schien nicht wichtig"
        
        result = translation_service._format_birkenbihl_style(original, translation)
        
        # Should match the pattern from specs:
        # Lo   que  parecía  no     importante
        # Das  was  schien   nicht  wichtig
        lines = result.split('\n')
        assert len(lines) == 2
        
        # Check that longer words get more space
        assert "parecía" in lines[0]  # Longest word
        assert "schien" in lines[1]   # Corresponding translation
    
    def test_format_birkenbihl_unequal_word_count(self, translation_service):
        """Test formatting when word counts differ."""
        original = "Hola amigo"
        translation = "Hallo mein lieber Freund"
        
        result = translation_service._format_birkenbihl_style(original, translation)
        lines = result.split('\n')
        
        # Should handle different word counts gracefully
        assert len(lines) == 2
        orig_words = [w for w in lines[0].split('  ') if w.strip()]
        trans_words = [w for w in lines[1].split('  ') if w.strip()]
        
        # Should pad to same length
        assert len(orig_words) == len(trans_words)


class TestRealWorldExamples:
    """Test with real examples from requirements."""
    
    @pytest.mark.asyncio
    async def test_spec_example_1(self, translation_service):
        """Test: Lo que parecía no importante."""
        text = "Lo que parecía no importante"
        result = await translation_service.translate_word_by_word(text, "es", "de")
        
        # Should produce proper Birkenbihl format
        lines = result.split('\n')
        assert len(lines) == 2
        
        # Check alignment - "parecía" is longest word
        assert "parecía" in lines[0]
        
    @pytest.mark.asyncio
    async def test_spec_example_2(self, translation_service):
        """Test: Tenlo por seguro.""" 
        text = "Tenlo por seguro"
        result = await translation_service.translate_word_by_word(text, "es", "de")
        
        # Should match spec format:
        # Tenlo   por  seguro
        # Hab-es  für  sicher
        lines = result.split('\n')
        assert "Tenlo" in lines[0]
        assert "Hab-es" in lines[1]
    
    @pytest.mark.asyncio
    async def test_spec_example_3(self, translation_service):
        """Test: Fueron tantos bellos y malos momentos."""
        text = "Fueron tantos bellos y malos momentos"
        result = await translation_service.translate_word_by_word(text, "es", "de")
        
        # Should handle longer sentences properly
        lines = result.split('\n')
        assert len(lines) == 2
        assert "Fueron" in lines[0]
        assert "momentos" in lines[0]
    
    @pytest.mark.asyncio
    async def test_save_translation(self, translation_service, db_session):
        """Test saving translation to database."""
        translation = await translation_service.save_translation(
            text="Hola mundo",
            source_lang="es", 
            target_lang="de",
            natural="Hallo Welt",
            word_by_word="Hallo  Welt\nHallo  Welt"
        )
        
        assert translation.id is not None
        assert translation.original_text == "Hola mundo"
        assert translation.natural_translation == "Hallo Welt"
        assert translation.word_by_word_translation == "Hallo  Welt\nHallo  Welt"
        
        # Check it's in database
        saved = db_session.get(Translation, translation.id)
        assert saved is not None
        assert saved.original_text == "Hola mundo"