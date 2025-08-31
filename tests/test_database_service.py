"""Comprehensive tests for DatabaseService."""

from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
import pytest
import tempfile
import sys
from unittest.mock import Mock, patch

from sqlmodel import Session, SQLModel, create_engine, select

from birkenbihl.models.translation import Language, Translation, TranslationType

# Mock all potentially missing dependencies and submodules before importing
mock_module = Mock()
mock_module.Agent = Mock()
mock_module.AudioSegment = Mock()
mock_module.play = Mock()
mock_module.ModelRequest = Mock()
mock_module.UserPrompt = Mock()

missing_modules = [
    'pydantic_ai', 
    'pydantic_ai.messages',
    'pydub', 
    'pydub.playback',
    'edge_tts',
    'nicegui',
    'pywebview'
]

for module_name in missing_modules:
    if module_name not in sys.modules:
        sys.modules[module_name] = mock_module

# Now we should be able to import DatabaseService
from birkenbihl.main import DatabaseService


class TestDatabaseService:
    """Test database service functionality."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            yield f"sqlite:///{db_path}"

    @pytest.fixture
    def db_service(self, temp_db_path):
        """Create database service with temporary database."""
        service = DatabaseService(temp_db_path)
        yield service

    @pytest.fixture
    def populated_db_service(self, db_service):
        """Database service with test translations."""
        with db_service.get_session() as session:
            # Get languages
            languages = session.exec(select(Language)).all()
            de_lang = next((l for l in languages if l.code == "de"), None)
            es_lang = next((l for l in languages if l.code == "es"), None)
            en_lang = next((l for l in languages if l.code == "en"), None)
            
            if not de_lang or not es_lang or not en_lang:
                pytest.fail("Required languages not found in test database")
            
            # Create test translations with various timestamps
            base_time = datetime.utcnow()
            test_translations = [
                Translation(
                    source_text="Hola mundo",
                    source_language_id=es_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text="Hallo Welt",
                    created_at=base_time - timedelta(hours=5)
                ),
                Translation(
                    source_text="Hola mundo",
                    source_language_id=es_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.WORD_FOR_WORD,
                    translated_text="Hallo Welt",
                    created_at=base_time - timedelta(hours=4)
                ),
                Translation(
                    source_text="Buenos días",
                    source_language_id=es_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text="Guten Tag",
                    created_at=base_time - timedelta(hours=3)
                ),
                Translation(
                    source_text="Hello world",
                    source_language_id=en_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text="Hallo Welt",
                    created_at=base_time - timedelta(hours=2)
                ),
                Translation(
                    source_text="Good morning everyone",
                    source_language_id=en_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text="Guten Morgen alle zusammen",
                    created_at=base_time - timedelta(hours=1)
                ),
                Translation(
                    source_text="How are you doing today",
                    source_language_id=en_lang.id,
                    target_language_id=es_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text="Cómo estás hoy",
                    created_at=base_time
                ),
            ]
            
            for translation in test_translations:
                session.add(translation)
            
            session.commit()
        
        yield db_service

    def test_database_initialization_creates_tables(self, temp_db_path):
        """Test that database initialization creates all required tables."""
        service = DatabaseService(temp_db_path)
        
        with service.get_session() as session:
            # Check that tables exist by querying them
            languages = session.exec(select(Language)).all()
            translations = session.exec(select(Translation)).all()
            
            # Should not raise exceptions
            assert isinstance(languages, list)
            assert isinstance(translations, list)

    def test_database_initialization_creates_directory(self):
        """Test that database initialization creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "directory" / "test.db"
            db_url = f"sqlite:///{nested_path}"
            
            # Directory should not exist initially
            assert not nested_path.parent.exists()
            
            service = DatabaseService(db_url)
            
            # Directory should be created
            assert nested_path.parent.exists()
            
            # Database should work
            with service.get_session() as session:
                languages = session.exec(select(Language)).all()
                assert isinstance(languages, list)

    def test_language_seeding(self, db_service):
        """Test that initial languages are seeded correctly."""
        languages = db_service.get_languages()
        
        # Should have exactly 3 default languages
        assert len(languages) == 3
        
        # Check specific languages
        codes = {lang.code for lang in languages}
        assert "de" in codes
        assert "en" in codes
        assert "es" in codes
        
        # Check language details
        de_lang = next(lang for lang in languages if lang.code == "de")
        assert de_lang.name == "Deutsch"
        assert de_lang.native_name == "Deutsch"
        assert de_lang.is_active is True

    def test_language_seeding_idempotent(self, db_service):
        """Test that language seeding doesn't create duplicates."""
        # Get initial count
        initial_languages = db_service.get_languages()
        initial_count = len(initial_languages)
        
        # Create new service with same database
        service2 = DatabaseService(str(db_service.engine.url))
        
        # Should have same number of languages
        languages2 = service2.get_languages()
        assert len(languages2) == initial_count
        assert len(languages2) == 3


class TestGetLanguages:
    """Test get_languages method."""

    def test_get_languages_returns_only_active(self, db_service):
        """Test that get_languages only returns active languages."""
        with db_service.get_session() as session:
            # Add inactive language
            inactive_lang = Language(
                code="fr",
                name="Français",
                native_name="Français",
                is_active=False
            )
            session.add(inactive_lang)
            session.commit()
        
        languages = db_service.get_languages()
        
        # Should not include inactive language
        codes = {lang.code for lang in languages}
        assert "fr" not in codes
        assert len(languages) == 3  # Only the 3 default active languages

    def test_get_languages_empty_database(self):
        """Test get_languages with empty database."""
        # Create service without seeding
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "empty.db"
            engine = create_engine(f"sqlite:///{db_path}")
            SQLModel.metadata.create_all(engine)
            
            service = DatabaseService.__new__(DatabaseService)
            service.engine = engine
            
            languages = service.get_languages()
            assert languages == []


class TestSaveTranslation:
    """Test save_translation method."""

    def test_save_translation_basic(self, db_service):
        """Test basic translation saving."""
        with db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        translation = Translation(
            source_text="Test text",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Test translation"
        )
        
        saved = db_service.save_translation(translation)
        
        assert saved.id is not None
        assert saved.source_text == "Test text"
        assert saved.translated_text == "Test translation"
        assert saved.created_at is not None
        assert saved.updated_at is not None

    def test_save_translation_with_metadata(self, db_service):
        """Test saving translation with additional metadata."""
        with db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        translation = Translation(
            source_text="Advanced test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Advanced translation",
            confidence_score=0.95,
            ai_provider="test-provider",
            model_used="test-model",
            learning_phase=2,
            difficulty_rating=3
        )
        
        saved = db_service.save_translation(translation)
        
        assert saved.confidence_score == 0.95
        assert saved.ai_provider == "test-provider"
        assert saved.model_used == "test-model"
        assert saved.learning_phase == 2
        assert saved.difficulty_rating == 3

    def test_save_translation_persists_in_database(self, db_service):
        """Test that saved translation persists in database."""
        with db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        translation = Translation(
            source_text="Persistence test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Persistence translation"
        )
        
        saved = db_service.save_translation(translation)
        translation_id = saved.id
        
        # Verify in new session
        with db_service.get_session() as session:
            retrieved = session.get(Translation, translation_id)
            assert retrieved is not None
            assert retrieved.source_text == "Persistence test"
            assert retrieved.translated_text == "Persistence translation"


class TestGetTranslationHistory:
    """Test get_translation_history method."""

    def test_get_translation_history_ordering(self, populated_db_service):
        """Test that translation history is ordered by creation date descending."""
        history = populated_db_service.get_translation_history(limit=10)
        
        # Should have translations
        assert len(history) > 0
        
        # Should be ordered by created_at descending (newest first)
        for i in range(len(history) - 1):
            assert history[i].created_at >= history[i + 1].created_at

    def test_get_translation_history_limit(self, populated_db_service):
        """Test that translation history respects limit parameter."""
        # Test with small limit
        history = populated_db_service.get_translation_history(limit=3)
        assert len(history) == 3
        
        # Test with large limit
        history = populated_db_service.get_translation_history(limit=100)
        assert len(history) <= 100  # Should not exceed actual number of translations

    def test_get_translation_history_default_limit(self, populated_db_service):
        """Test that translation history uses default limit."""
        history = populated_db_service.get_translation_history()
        
        # Should use default limit of 50
        assert len(history) <= 50

    def test_get_translation_history_empty_database(self, db_service):
        """Test get_translation_history with empty database."""
        history = db_service.get_translation_history()
        assert history == []

    def test_get_translation_history_contains_all_types(self, populated_db_service):
        """Test that history includes all translation types."""
        history = populated_db_service.get_translation_history()
        
        types = {t.translation_type for t in history}
        assert TranslationType.NATURAL in types
        assert TranslationType.WORD_FOR_WORD in types


class TestSearchTranslations:
    """Test search_translations method."""

    def test_search_translations_by_source_text(self, populated_db_service):
        """Test searching translations by source text."""
        results = populated_db_service.search_translations("Hola")
        
        # Should find translations with "Hola" in source text
        assert len(results) >= 2  # "Hola mundo" entries
        
        for result in results:
            assert "Hola" in result.source_text

    def test_search_translations_by_translated_text(self, populated_db_service):
        """Test searching translations by translated text."""
        results = populated_db_service.search_translations("Welt")
        
        # Should find translations with "Welt" in translated text
        assert len(results) >= 2  # Multiple "Hallo Welt" entries
        
        for result in results:
            assert "Welt" in result.translated_text

    def test_search_translations_case_sensitivity(self, populated_db_service):
        """Test search case sensitivity."""
        # SQLite LIKE is case-insensitive by default
        results_upper = populated_db_service.search_translations("HOLA")
        results_lower = populated_db_service.search_translations("hola")
        results_mixed = populated_db_service.search_translations("Hola")
        
        # Should find same results regardless of case
        assert len(results_upper) == len(results_lower) == len(results_mixed)

    def test_search_translations_partial_match(self, populated_db_service):
        """Test partial text matching."""
        results = populated_db_service.search_translations("mundo")
        
        # Should find "Hola mundo" 
        assert len(results) >= 1
        found = False
        for result in results:
            if "mundo" in result.source_text.lower():
                found = True
                break
        assert found

    def test_search_translations_limit(self, populated_db_service):
        """Test search results respect limit parameter."""
        # Add more translations to test limit
        with populated_db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
            
            # Add many translations with "test" in text
            for i in range(25):
                translation = Translation(
                    source_text=f"test text {i}",
                    source_language_id=es_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text=f"test translation {i}"
                )
                session.add(translation)
            session.commit()
        
        results = populated_db_service.search_translations("test", limit=10)
        assert len(results) == 10

    def test_search_translations_ordering(self, populated_db_service):
        """Test that search results are ordered by creation date descending."""
        results = populated_db_service.search_translations("o", limit=10)  # Should match many
        
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].created_at >= results[i + 1].created_at

    def test_search_translations_empty_query(self, populated_db_service):
        """Test searching with empty query string."""
        results = populated_db_service.search_translations("")
        
        # Should return all translations (up to limit)
        assert len(results) > 0

    def test_search_translations_no_matches(self, populated_db_service):
        """Test searching with query that has no matches."""
        results = populated_db_service.search_translations("zzz_no_match_zzz")
        
        assert len(results) == 0


class TestGetTranslationsByLanguagePair:
    """Test get_translations_by_language_pair method."""

    def test_get_translations_by_language_pair_basic(self, populated_db_service):
        """Test getting translations for specific language pair."""
        with populated_db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        results = populated_db_service.get_translations_by_language_pair(
            es_lang.id, de_lang.id
        )
        
        # Should find Spanish to German translations
        assert len(results) >= 3  # We added several ES->DE translations
        
        for result in results:
            assert result.source_language_id == es_lang.id
            assert result.target_language_id == de_lang.id

    def test_get_translations_by_language_pair_different_direction(self, populated_db_service):
        """Test language pair in different directions."""
        with populated_db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            en_lang = next(l for l in languages if l.code == "en")
        
        # EN -> ES
        en_to_es = populated_db_service.get_translations_by_language_pair(
            en_lang.id, es_lang.id
        )
        
        # ES -> EN (should be different/empty)
        es_to_en = populated_db_service.get_translations_by_language_pair(
            es_lang.id, en_lang.id
        )
        
        # Should have different results
        assert len(en_to_es) >= 1  # We added one EN->ES translation
        assert len(es_to_en) == 0   # No ES->EN translations in test data

    def test_get_translations_by_language_pair_limit(self, populated_db_service):
        """Test that language pair results respect limit."""
        with populated_db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
            
            # Add more translations to test limit
            for i in range(15):
                translation = Translation(
                    source_text=f"Spanish text {i}",
                    source_language_id=es_lang.id,
                    target_language_id=de_lang.id,
                    translation_type=TranslationType.NATURAL,
                    translated_text=f"German text {i}"
                )
                session.add(translation)
            session.commit()
        
        results = populated_db_service.get_translations_by_language_pair(
            es_lang.id, de_lang.id, limit=10
        )
        
        assert len(results) == 10

    def test_get_translations_by_language_pair_ordering(self, populated_db_service):
        """Test that language pair results are ordered by creation date descending."""
        with populated_db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        results = populated_db_service.get_translations_by_language_pair(
            es_lang.id, de_lang.id
        )
        
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].created_at >= results[i + 1].created_at

    def test_get_translations_by_language_pair_no_matches(self, populated_db_service):
        """Test getting translations for language pair with no matches."""
        with populated_db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            de_lang = next(l for l in languages if l.code == "de")
            en_lang = next(l for l in languages if l.code == "en")
        
        # DE -> EN should have no matches in our test data
        results = populated_db_service.get_translations_by_language_pair(
            de_lang.id, en_lang.id
        )
        
        assert len(results) == 0

    def test_get_translations_by_language_pair_invalid_language_ids(self, populated_db_service):
        """Test with invalid language IDs."""
        fake_id1 = uuid4()
        fake_id2 = uuid4()
        
        results = populated_db_service.get_translations_by_language_pair(
            fake_id1, fake_id2
        )
        
        assert len(results) == 0


class TestDatabaseErrorHandling:
    """Test error handling in database operations."""

    def test_database_service_with_invalid_path(self):
        """Test database service with invalid database path."""
        # This should still work as SQLite can create files
        invalid_path = "/tmp/test_invalid_123456.db"
        service = DatabaseService(f"sqlite:///{invalid_path}")
        
        # Should be able to use the service
        languages = service.get_languages()
        assert isinstance(languages, list)
        
        # Cleanup
        Path(invalid_path).unlink(missing_ok=True)

    def test_get_session_returns_valid_session(self, db_service):
        """Test that get_session returns a valid session."""
        session = db_service.get_session()
        
        assert isinstance(session, Session)
        
        # Should be able to query
        languages = session.exec(select(Language)).all()
        assert isinstance(languages, list)
        
        session.close()

    def test_save_translation_with_invalid_language_ids(self, db_service):
        """Test saving translation with invalid language IDs."""
        fake_id = uuid4()
        
        translation = Translation(
            source_text="Test",
            source_language_id=fake_id,
            target_language_id=fake_id,
            translation_type=TranslationType.NATURAL,
            translated_text="Test translation"
        )
        
        # Should save but foreign key constraints might be enforced
        # depending on SQLite configuration
        saved = db_service.save_translation(translation)
        assert saved.id is not None

    @patch('birkenbihl.main.SQLModel.metadata.create_all')
    def test_database_creation_failure_handling(self, mock_create_all):
        """Test handling of database creation failures."""
        mock_create_all.side_effect = Exception("Database creation failed")
        
        with pytest.raises(Exception, match="Database creation failed"):
            DatabaseService("sqlite:///test.db")

    def test_large_text_handling(self, db_service):
        """Test handling of large text in translations."""
        with db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        # Create large text (within field limits)
        large_text = "A" * 4000  # Under 5000 char limit
        
        translation = Translation(
            source_text=large_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text=large_text[::-1]  # Reversed as "translation"
        )
        
        saved = db_service.save_translation(translation)
        assert len(saved.source_text) == 4000
        assert len(saved.translated_text) == 4000


class TestDatabaseServiceIntegration:
    """Integration tests for database service."""

    def test_full_workflow_integration(self, db_service):
        """Test full workflow from language retrieval to translation storage and querying."""
        # 1. Get languages
        languages = db_service.get_languages()
        assert len(languages) == 3
        
        es_lang = next(l for l in languages if l.code == "es")
        de_lang = next(l for l in languages if l.code == "de")
        
        # 2. Save multiple translations
        translations_to_save = [
            ("Hola", "Hallo", TranslationType.NATURAL),
            ("Hola", "Hallo", TranslationType.WORD_FOR_WORD),
            ("Buenos días", "Guten Tag", TranslationType.NATURAL),
            ("Adiós", "Auf Wiedersehen", TranslationType.NATURAL),
        ]
        
        saved_translations = []
        for source, target, trans_type in translations_to_save:
            translation = Translation(
                source_text=source,
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=trans_type,
                translated_text=target
            )
            saved = db_service.save_translation(translation)
            saved_translations.append(saved)
        
        # 3. Test history retrieval
        history = db_service.get_translation_history(limit=10)
        assert len(history) == 4
        
        # 4. Test search functionality
        hola_results = db_service.search_translations("Hola")
        assert len(hola_results) == 2  # Natural + Word-for-word
        
        guten_results = db_service.search_translations("Guten")
        assert len(guten_results) == 1
        
        # 5. Test language pair filtering
        es_de_translations = db_service.get_translations_by_language_pair(
            es_lang.id, de_lang.id
        )
        assert len(es_de_translations) == 4
        
        # All results should be ES -> DE
        for translation in es_de_translations:
            assert translation.source_language_id == es_lang.id
            assert translation.target_language_id == de_lang.id

    def test_concurrent_database_operations(self, db_service):
        """Test that concurrent database operations work correctly."""
        with db_service.get_session() as session:
            languages = session.exec(select(Language)).all()
            es_lang = next(l for l in languages if l.code == "es")
            de_lang = next(l for l in languages if l.code == "de")
        
        # Simulate concurrent operations
        translation1 = Translation(
            source_text="Concurrent test 1",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Concurrent translation 1"
        )
        
        translation2 = Translation(
            source_text="Concurrent test 2",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Concurrent translation 2"
        )
        
        # Save both
        saved1 = db_service.save_translation(translation1)
        saved2 = db_service.save_translation(translation2)
        
        # Both should be saved successfully
        assert saved1.id != saved2.id
        
        # Both should be retrievable
        history = db_service.get_translation_history()
        saved_ids = {t.id for t in history}
        assert saved1.id in saved_ids
        assert saved2.id in saved_ids

    def test_database_persistence_across_service_instances(self, temp_db_path):
        """Test that data persists across different service instances."""
        # Create first service instance and save data
        service1 = DatabaseService(temp_db_path)
        languages1 = service1.get_languages()
        es_lang = next(l for l in languages1 if l.code == "es")
        de_lang = next(l for l in languages1 if l.code == "de")
        
        translation = Translation(
            source_text="Persistence test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Persistence translation"
        )
        saved = service1.save_translation(translation)
        saved_id = saved.id
        
        # Create second service instance with same database
        service2 = DatabaseService(temp_db_path)
        
        # Should have same languages (no re-seeding)
        languages2 = service2.get_languages()
        assert len(languages2) == 3
        
        # Should find the saved translation
        history = service2.get_translation_history()
        found_translation = next((t for t in history if t.id == saved_id), None)
        assert found_translation is not None
        assert found_translation.source_text == "Persistence test"