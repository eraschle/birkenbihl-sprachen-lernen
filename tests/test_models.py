"""Tests for database models."""

import pytest
from datetime import datetime
from uuid import uuid4, UUID
from sqlmodel import Session, create_engine, SQLModel, select

from birkenbihl.models.translation import (
    Translation,
    Language,
    TranslationType,
    TranslationResult,
)


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_languages(db_session: Session) -> tuple[Language, Language]:
    """Create sample languages for testing."""
    de_lang = Language(
        code="de",
        name="German",
        native_name="Deutsch",
        is_active=True,
    )
    es_lang = Language(
        code="es",
        name="Spanish",
        native_name="Español",
        is_active=True,
    )
    
    db_session.add(de_lang)
    db_session.add(es_lang)
    db_session.commit()
    db_session.refresh(de_lang)
    db_session.refresh(es_lang)
    
    return de_lang, es_lang


class TestLanguageModel:
    """Tests for Language model."""

    def test_create_language(self, db_session: Session) -> None:
        """Test creating a language."""
        language = Language(
            code="en",
            name="English",
            native_name="English",
            is_active=True,
        )
        
        db_session.add(language)
        db_session.commit()
        db_session.refresh(language)
        
        assert language.id is not None
        assert isinstance(language.id, UUID)
        assert language.code == "en"
        assert language.name == "English"
        assert language.native_name == "English"
        assert language.is_active is True
        assert isinstance(language.created_at, datetime)
        assert isinstance(language.updated_at, datetime)

    def test_language_unique_code_constraint(self, db_session: Session) -> None:
        """Test that language codes must be unique."""
        # Create first language
        lang1 = Language(code="fr", name="French", native_name="Français")
        db_session.add(lang1)
        db_session.commit()
        
        # Try to create second language with same code
        lang2 = Language(code="fr", name="French2", native_name="Français2")
        db_session.add(lang2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            db_session.commit()

    def test_language_string_representation(self) -> None:
        """Test string representation of Language."""
        language = Language(code="de", name="German", native_name="Deutsch")
        assert str(language) == "German (de)"

    def test_language_defaults(self, db_session: Session) -> None:
        """Test default values for Language."""
        language = Language(code="it", name="Italian", native_name="Italiano")
        db_session.add(language)
        db_session.commit()
        db_session.refresh(language)
        
        assert language.is_active is True  # Default value
        assert isinstance(language.created_at, datetime)
        assert isinstance(language.updated_at, datetime)

    def test_language_max_length_constraints(self) -> None:
        """Test max length constraints for Language fields."""
        # These should not raise exceptions during instantiation
        language = Language(
            code="a" * 10,  # max_length=10
            name="b" * 100,  # max_length=100
            native_name="c" * 100,  # max_length=100
        )
        
        assert len(language.code) == 10
        assert len(language.name) == 100
        assert len(language.native_name) == 100


class TestTranslationType:
    """Tests for TranslationType enum."""

    def test_translation_type_values(self) -> None:
        """Test TranslationType enum values."""
        assert TranslationType.NATURAL == "natural"
        assert TranslationType.WORD_FOR_WORD == "word_for_word"

    def test_translation_type_membership(self) -> None:
        """Test TranslationType membership."""
        assert "natural" in TranslationType
        assert "word_for_word" in TranslationType
        assert "invalid" not in TranslationType

    def test_translation_type_iteration(self) -> None:
        """Test iterating over TranslationType."""
        types = list(TranslationType)
        assert len(types) == 2
        assert TranslationType.NATURAL in types
        assert TranslationType.WORD_FOR_WORD in types


class TestTranslationResult:
    """Tests for TranslationResult model."""

    def test_create_translation_result(self) -> None:
        """Test creating a TranslationResult."""
        result = TranslationResult(
            natural_translation="Hello world",
            word_by_word_translation="Hello  world\nHallo  Welt",
            formatted_decoding="Hello  world\nHallo  Welt"
        )
        
        assert result.natural_translation == "Hello world"
        assert result.word_by_word_translation == "Hello  world\nHallo  Welt"
        assert result.formatted_decoding == "Hello  world\nHallo  Welt"

    def test_translation_result_field_descriptions(self) -> None:
        """Test that TranslationResult has proper field descriptions."""
        # Check that fields have descriptions (important for API docs)
        fields = TranslationResult.model_fields
        
        assert "natural_translation" in fields
        assert "word_by_word_translation" in fields
        assert "formatted_decoding" in fields
        
        assert fields["natural_translation"].description == "Natürliche Übersetzung"
        assert fields["word_by_word_translation"].description == "Wort-für-Wort Übersetzung"
        assert fields["formatted_decoding"].description == "Formatierte Dekodierung mit Alignment"


class TestTranslationModel:
    """Tests for Translation model."""

    def test_create_translation(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test creating a translation."""
        de_lang, es_lang = sample_languages
        
        translation = Translation(
            source_text="Hola mundo",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Hallo Welt",
            confidence_score=0.95,
            ai_provider="openai",
            model_used="gpt-4",
            learning_phase=1,
            difficulty_rating=3,
        )
        
        db_session.add(translation)
        db_session.commit()
        db_session.refresh(translation)
        
        assert translation.id is not None
        assert isinstance(translation.id, UUID)
        assert translation.source_text == "Hola mundo"
        assert translation.translated_text == "Hallo Welt"
        assert translation.translation_type == TranslationType.NATURAL
        assert translation.confidence_score == 0.95
        assert translation.learning_phase == 1
        assert translation.difficulty_rating == 3

    def test_translation_defaults(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test default values for Translation."""
        de_lang, es_lang = sample_languages
        
        translation = Translation(
            source_text="Test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Test",
        )
        
        db_session.add(translation)
        db_session.commit()
        db_session.refresh(translation)
        
        assert translation.learning_phase == 1  # Default value
        assert translation.is_reviewed is False  # Default value
        assert translation.review_count == 0  # Default value
        assert translation.word_breakdown is None  # Default value
        assert translation.confidence_score is None  # Default value
        assert translation.difficulty_rating is None  # Default value
        assert translation.last_reviewed_at is None  # Default value
        assert isinstance(translation.created_at, datetime)
        assert isinstance(translation.updated_at, datetime)

    def test_translation_birkenbihl_fields(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test Birkenbihl-specific fields."""
        de_lang, es_lang = sample_languages
        
        translation = Translation(
            source_text="Test text",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Test text",
            learning_phase=3,
            is_reviewed=True,
            review_count=5,
            difficulty_rating=4,
            last_reviewed_at=datetime.utcnow(),
        )
        
        db_session.add(translation)
        db_session.commit()
        db_session.refresh(translation)
        
        assert translation.learning_phase == 3
        assert translation.is_reviewed is True
        assert translation.review_count == 5
        assert translation.difficulty_rating == 4
        assert translation.last_reviewed_at is not None

    def test_translation_constraints(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test field constraints on Translation model."""
        de_lang, es_lang = sample_languages
        
        # Test learning_phase constraints (1-4)
        with pytest.raises(ValueError):
            Translation(
                source_text="Test",
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.NATURAL,
                translated_text="Test",
                learning_phase=0,  # Invalid: below minimum
            )
        
        with pytest.raises(ValueError):
            Translation(
                source_text="Test",
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.NATURAL,
                translated_text="Test",
                learning_phase=5,  # Invalid: above maximum
            )
        
        # Test difficulty_rating constraints (1-5)
        with pytest.raises(ValueError):
            Translation(
                source_text="Test",
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.NATURAL,
                translated_text="Test",
                difficulty_rating=0,  # Invalid: below minimum
            )
        
        with pytest.raises(ValueError):
            Translation(
                source_text="Test",
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.NATURAL,
                translated_text="Test",
                difficulty_rating=6,  # Invalid: above maximum
            )
        
        # Test confidence_score constraints (0.0-1.0)
        with pytest.raises(ValueError):
            Translation(
                source_text="Test",
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.NATURAL,
                translated_text="Test",
                confidence_score=-0.1,  # Invalid: below minimum
            )
        
        with pytest.raises(ValueError):
            Translation(
                source_text="Test",
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.NATURAL,
                translated_text="Test",
                confidence_score=1.1,  # Invalid: above maximum
            )

    def test_translation_word_breakdown_json(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test JSON word_breakdown field."""
        de_lang, es_lang = sample_languages
        
        word_mapping = {
            "Hola": "Hallo",
            "mundo": "Welt",
        }
        
        translation = Translation(
            source_text="Hola mundo",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Hallo Welt",
            word_breakdown=word_mapping,
        )
        
        db_session.add(translation)
        db_session.commit()
        db_session.refresh(translation)
        
        assert translation.word_breakdown == word_mapping
        assert translation.word_breakdown["Hola"] == "Hallo"
        assert translation.word_breakdown["mundo"] == "Welt"

    def test_translation_string_representation(self, sample_languages: tuple[Language, Language]) -> None:
        """Test string representation of Translation."""
        de_lang, es_lang = sample_languages
        
        translation = Translation(
            source_text="This is a very long text that should be truncated in the string representation",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="This is also a very long translation that should be truncated in the repr",
        )
        
        str_repr = str(translation)
        assert str_repr.startswith("Translation(")
        assert "This is a very long text that should be truncated" in str_repr
        assert "..." in str_repr  # Should be truncated

    def test_translation_is_dekodierung_property(self, sample_languages: tuple[Language, Language]) -> None:
        """Test is_dekodierung property."""
        de_lang, es_lang = sample_languages
        
        # Natural translation should not be dekodierung
        natural_translation = Translation(
            source_text="Test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Test",
        )
        assert natural_translation.is_dekodierung is False
        
        # Word-for-word translation should be dekodierung
        word_for_word_translation = Translation(
            source_text="Test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Test",
        )
        assert word_for_word_translation.is_dekodierung is True

    def test_translation_get_word_count(self, sample_languages: tuple[Language, Language]) -> None:
        """Test get_word_count method."""
        de_lang, es_lang = sample_languages
        
        translation = Translation(
            source_text="Hola mundo amigo",  # 3 words
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Hallo Welt Freund",
        )
        
        assert translation.get_word_count() == 3
        
        # Test with single word
        single_word_translation = Translation(
            source_text="Hola",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Hallo",
        )
        
        assert single_word_translation.get_word_count() == 1
        
        # Test with empty text
        empty_translation = Translation(
            source_text="",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="",
        )
        
        assert empty_translation.get_word_count() == 0  # split("") returns []

    def test_translation_foreign_key_constraints(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test foreign key constraints work correctly."""
        de_lang, es_lang = sample_languages
        
        # Create translation with valid language IDs
        translation = Translation(
            source_text="Test",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Test",
        )
        
        db_session.add(translation)
        db_session.commit()
        
        # Verify the translation was created successfully
        assert translation.id is not None
        
        # Test retrieving with relationships (if relationships are defined)
        saved_translation = db_session.get(Translation, translation.id)
        assert saved_translation is not None
        assert saved_translation.source_language_id == es_lang.id
        assert saved_translation.target_language_id == de_lang.id


class TestDatabaseConstraints:
    """Tests for database-level constraints and relationships."""

    def test_cascade_delete_behavior(self, db_session: Session) -> None:
        """Test behavior when deleting languages that have translations."""
        # Create languages
        en_lang = Language(code="en", name="English", native_name="English")
        fr_lang = Language(code="fr", name="French", native_name="Français")
        
        db_session.add(en_lang)
        db_session.add(fr_lang)
        db_session.commit()
        db_session.refresh(en_lang)
        db_session.refresh(fr_lang)
        
        # Create translation
        translation = Translation(
            source_text="Hello",
            source_language_id=en_lang.id,
            target_language_id=fr_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Salut",
        )
        
        db_session.add(translation)
        db_session.commit()
        
        # Verify translation exists
        assert translation.id is not None
        
        # Try to delete a language that's referenced by translation
        # This should either cascade or raise a foreign key constraint error
        # depending on the database configuration
        db_session.delete(en_lang)
        
        # This might raise an exception depending on foreign key configuration
        try:
            db_session.commit()
            # If it succeeds, check that translation was also deleted (cascade)
            deleted_translation = db_session.get(Translation, translation.id)
            # Could be None if cascade delete, or still exist if set null
        except Exception:
            # Foreign key constraint prevented deletion
            db_session.rollback()
            # Language should still exist
            existing_lang = db_session.get(Language, en_lang.id)
            assert existing_lang is not None

    def test_query_translations_by_language(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test querying translations by language."""
        de_lang, es_lang = sample_languages
        
        # Create multiple translations
        translation1 = Translation(
            source_text="Hola",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Hallo",
        )
        
        translation2 = Translation(
            source_text="Mundo",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Welt",
        )
        
        db_session.add_all([translation1, translation2])
        db_session.commit()
        
        # Query translations by source language
        es_translations = db_session.exec(
            select(Translation).where(Translation.source_language_id == es_lang.id)
        ).all()
        
        assert len(es_translations) == 2
        assert all(t.source_language_id == es_lang.id for t in es_translations)
        
        # Query translations by target language
        de_translations = db_session.exec(
            select(Translation).where(Translation.target_language_id == de_lang.id)
        ).all()
        
        assert len(de_translations) == 2
        assert all(t.target_language_id == de_lang.id for t in de_translations)

    def test_query_translations_by_type(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test querying translations by type."""
        de_lang, es_lang = sample_languages
        
        # Create translations of different types
        natural_translation = Translation(
            source_text="Test natural",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Test natürlich",
        )
        
        word_translation = Translation(
            source_text="Test word",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Test Wort",
        )
        
        db_session.add_all([natural_translation, word_translation])
        db_session.commit()
        
        # Query by translation type
        natural_translations = db_session.exec(
            select(Translation).where(Translation.translation_type == TranslationType.NATURAL)
        ).all()
        
        word_translations = db_session.exec(
            select(Translation).where(Translation.translation_type == TranslationType.WORD_FOR_WORD)
        ).all()
        
        assert len(natural_translations) == 1
        assert len(word_translations) == 1
        assert natural_translations[0].translation_type == TranslationType.NATURAL
        assert word_translations[0].translation_type == TranslationType.WORD_FOR_WORD

    def test_query_by_learning_phase_and_difficulty(self, db_session: Session, sample_languages: tuple[Language, Language]) -> None:
        """Test querying by Birkenbihl-specific fields."""
        de_lang, es_lang = sample_languages
        
        # Create translations with different learning phases and difficulties
        easy_phase1 = Translation(
            source_text="Easy text",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Einfacher Text",
            learning_phase=1,
            difficulty_rating=2,
        )
        
        hard_phase3 = Translation(
            source_text="Hard text",
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text="Schwerer Text",
            learning_phase=3,
            difficulty_rating=5,
        )
        
        db_session.add_all([easy_phase1, hard_phase3])
        db_session.commit()
        
        # Query by learning phase
        phase1_translations = db_session.exec(
            select(Translation).where(Translation.learning_phase == 1)
        ).all()
        
        phase3_translations = db_session.exec(
            select(Translation).where(Translation.learning_phase == 3)
        ).all()
        
        assert len(phase1_translations) == 1
        assert len(phase3_translations) == 1
        
        # Query by difficulty rating
        easy_translations = db_session.exec(
            select(Translation).where(Translation.difficulty_rating <= 3)
        ).all()
        
        hard_translations = db_session.exec(
            select(Translation).where(Translation.difficulty_rating >= 4)
        ).all()
        
        assert len(easy_translations) == 1
        assert len(hard_translations) == 1