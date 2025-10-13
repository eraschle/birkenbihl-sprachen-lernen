"""Unit tests for SqliteStorageProvider.

Tests SQLite-based storage implementation including CRUD operations,
DAO model mapping, and error handling.
"""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.services.language_service import get_language_by
from birkenbihl.storage import NotFoundError, SqliteStorageProvider


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create temporary database file path."""
    return tmp_path / "test_birkenbihl.db"


@pytest.fixture
def storage_provider(temp_db: Path) -> Generator[SqliteStorageProvider, None, None]:
    """Create SqliteStorageProvider with temporary database."""
    provider = SqliteStorageProvider(temp_db)
    yield provider
    provider.close()


@pytest.fixture
def sample_translation() -> Translation:
    """Create sample translation for testing."""
    return Translation(
        uuid=uuid4(),
        title="Spanish Lesson 1",
        source_language=get_language_by("es"),
        target_language=get_language_by("de"),
        sentences=[
            Sentence(
                uuid=uuid4(),
                source_text="Yo te extrañaré",
                natural_translation="Ich werde dich vermissen",
                word_alignments=[
                    WordAlignment(source_word="Yo", target_word="Ich", position=0),
                    WordAlignment(source_word="te", target_word="dich", position=1),
                    WordAlignment(source_word="extrañaré", target_word="vermissen-werde", position=2),
                ],
            ),
            Sentence(
                uuid=uuid4(),
                source_text="Buenos días",
                natural_translation="Guten Morgen",
                word_alignments=[
                    WordAlignment(source_word="Buenos", target_word="Guten", position=0),
                    WordAlignment(source_word="días", target_word="Morgen", position=1),
                ],
            ),
        ],
    )


@pytest.mark.unit
class TestSqliteStorageProviderInitialization:
    """Test database initialization."""

    def test_creates_database_file(self, temp_db: Path) -> None:
        """Test that database file is created on initialization."""
        assert not temp_db.exists()
        with SqliteStorageProvider(temp_db):
            assert temp_db.exists()

    def test_creates_tables_on_initialization(self, storage_provider: SqliteStorageProvider) -> None:
        """Test that database tables are created."""
        from sqlmodel import Session, select

        from birkenbihl.storage.dao_models import TranslationDAO

        with Session(storage_provider.engine) as session:
            result = session.exec(select(TranslationDAO)).all()
            assert result == []


@pytest.mark.unit
class TestSqliteStorageProviderSave:
    """Test save operation."""

    def test_save_new_translation(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test saving a new translation."""
        saved = storage_provider.save(sample_translation)

        assert saved.uuid == sample_translation.uuid
        assert saved.title == sample_translation.title
        assert saved.source_language == sample_translation.source_language
        assert saved.target_language == sample_translation.target_language
        assert len(saved.sentences) == 2

    def test_save_preserves_uuids(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that UUIDs are preserved across save operations."""
        original_uuid = sample_translation.uuid
        original_sentence_uuids = [s.uuid for s in sample_translation.sentences]

        saved = storage_provider.save(sample_translation)

        assert saved.uuid == original_uuid
        saved_sentence_uuids = [s.uuid for s in saved.sentences]
        assert saved_sentence_uuids == original_sentence_uuids

    def test_save_preserves_word_alignments(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that word alignments are correctly saved and retrieved."""
        saved = storage_provider.save(sample_translation)

        first_sentence = saved.sentences[0]
        assert len(first_sentence.word_alignments) == 3
        assert first_sentence.word_alignments[0].source_word == "Yo"
        assert first_sentence.word_alignments[0].target_word == "Ich"
        assert first_sentence.word_alignments[0].position == 0

    def test_save_existing_translation_updates_it(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that saving an existing translation updates it."""
        storage_provider.save(sample_translation)

        sample_translation.title = "Updated Title"
        updated = storage_provider.save(sample_translation)

        assert updated.title == "Updated Title"
        assert updated.uuid == sample_translation.uuid


@pytest.mark.unit
class TestSqliteStorageProviderGet:
    """Test get operation."""

    def test_get_existing_translation(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test retrieving an existing translation."""
        storage_provider.save(sample_translation)
        retrieved = storage_provider.get(sample_translation.uuid)

        assert retrieved is not None
        assert retrieved.uuid == sample_translation.uuid
        assert retrieved.title == sample_translation.title
        assert len(retrieved.sentences) == 2

    def test_get_nonexistent_translation_returns_none(self, storage_provider: SqliteStorageProvider) -> None:
        """Test that getting a non-existent translation returns None."""
        nonexistent_uuid = uuid4()
        result = storage_provider.get(nonexistent_uuid)

        assert result is None

    def test_get_preserves_sentence_order(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that sentence order is preserved."""
        storage_provider.save(sample_translation)
        retrieved = storage_provider.get(sample_translation.uuid)

        assert retrieved is not None
        original_texts = [s.source_text for s in sample_translation.sentences]
        retrieved_texts = [s.source_text for s in retrieved.sentences]
        assert retrieved_texts == original_texts

    def test_get_preserves_word_alignment_order(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that word alignment order is preserved by position."""
        storage_provider.save(sample_translation)
        retrieved = storage_provider.get(sample_translation.uuid)

        assert retrieved is not None
        first_sentence = retrieved.sentences[0]
        positions = [wa.position for wa in first_sentence.word_alignments]
        assert positions == sorted(positions)


@pytest.mark.unit
class TestSqliteStorageProviderListAll:
    """Test list_all operation."""

    def test_list_all_empty_database(self, storage_provider: SqliteStorageProvider) -> None:
        """Test listing all translations from empty database."""
        result = storage_provider.list_all()
        assert result == []

    def test_list_all_returns_all_translations(self, storage_provider: SqliteStorageProvider) -> None:
        """Test that list_all returns all saved translations."""
        translation1 = Translation(
            uuid=uuid4(),
            title="Translation 1",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Hola",
                    natural_translation="Hallo",
                    word_alignments=[WordAlignment(source_word="Hola", target_word="Hallo", position=0)],
                )
            ],
        )
        translation2 = Translation(
            uuid=uuid4(),
            title="Translation 2",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Hello",
                    natural_translation="Hallo",
                    word_alignments=[WordAlignment(source_word="Hello", target_word="Hallo", position=0)],
                )
            ],
        )

        storage_provider.save(translation1)
        storage_provider.save(translation2)

        result = storage_provider.list_all()
        assert len(result) == 2
        uuids = {t.uuid for t in result}
        assert translation1.uuid in uuids
        assert translation2.uuid in uuids

    def test_list_all_ordered_by_updated_at_desc(self, storage_provider: SqliteStorageProvider) -> None:
        """Test that list_all returns translations ordered by updated_at (newest first)."""
        translation1 = Translation(
            uuid=uuid4(),
            title="First",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Uno",
                    natural_translation="Eins",
                    word_alignments=[WordAlignment(source_word="Uno", target_word="Eins", position=0)],
                )
            ],
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )
        translation2 = Translation(
            uuid=uuid4(),
            title="Second",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Dos",
                    natural_translation="Zwei",
                    word_alignments=[WordAlignment(source_word="Dos", target_word="Zwei", position=0)],
                )
            ],
            created_at=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
        )

        storage_provider.save(translation1)
        storage_provider.save(translation2)

        result = storage_provider.list_all()
        assert len(result) == 2
        assert result[0].title == "Second"
        assert result[1].title == "First"


@pytest.mark.unit
class TestSqliteStorageProviderDelete:
    """Test delete operation."""

    def test_delete_existing_translation(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test deleting an existing translation."""
        storage_provider.save(sample_translation)
        result = storage_provider.delete(sample_translation.uuid)

        assert result is True
        assert storage_provider.get(sample_translation.uuid) is None

    def test_delete_nonexistent_translation(self, storage_provider: SqliteStorageProvider) -> None:
        """Test deleting a non-existent translation returns False."""
        nonexistent_uuid = uuid4()
        result = storage_provider.delete(nonexistent_uuid)

        assert result is False

    def test_delete_cascades_to_sentences_and_alignments(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that deleting a translation cascades to sentences and word alignments."""
        storage_provider.save(sample_translation)
        storage_provider.delete(sample_translation.uuid)

        from sqlmodel import Session, select

        from birkenbihl.storage.dao_models import SentenceDAO, WordAlignmentDAO

        with Session(storage_provider.engine) as session:
            sentences = session.exec(select(SentenceDAO)).all()
            assert len(sentences) == 0

            alignments = session.exec(select(WordAlignmentDAO)).all()
            assert len(alignments) == 0


@pytest.mark.unit
class TestSqliteStorageProviderUpdate:
    """Test update operation."""

    def test_update_existing_translation(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test updating an existing translation."""
        storage_provider.save(sample_translation)

        sample_translation.title = "Updated Title"
        sample_translation.sentences[0].natural_translation = "Updated translation"

        updated = storage_provider.update(sample_translation)

        assert updated.title == "Updated Title"
        assert updated.sentences[0].natural_translation == "Updated translation"
        assert updated.updated_at >= updated.created_at

    def test_update_nonexistent_translation_raises_error(self, storage_provider: SqliteStorageProvider) -> None:
        """Test that updating a non-existent translation raises NotFoundError."""
        nonexistent_translation = Translation(
            uuid=uuid4(),
            title="Does not exist",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[],
        )

        with pytest.raises(NotFoundError):
            storage_provider.update(nonexistent_translation)

    def test_update_preserves_created_at(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that update preserves original created_at timestamp."""
        saved = storage_provider.save(sample_translation)
        original_created_at = saved.created_at

        saved.title = "Updated Title"
        updated = storage_provider.update(saved)

        assert updated.created_at == original_created_at
        assert updated.updated_at > original_created_at

    def test_update_replaces_sentences(
        self, storage_provider: SqliteStorageProvider, sample_translation: Translation
    ) -> None:
        """Test that update correctly replaces sentences."""
        storage_provider.save(sample_translation)

        sample_translation.sentences = [
            Sentence(
                uuid=uuid4(),
                source_text="New sentence",
                natural_translation="Neuer Satz",
                word_alignments=[
                    WordAlignment(source_word="New", target_word="Neuer", position=0),
                    WordAlignment(source_word="sentence", target_word="Satz", position=1),
                ],
            )
        ]

        updated = storage_provider.update(sample_translation)

        assert len(updated.sentences) == 1
        assert updated.sentences[0].source_text == "New sentence"


@pytest.mark.unit
class TestSqliteStorageProviderEdgeCases:
    """Test edge cases and error handling."""

    def test_save_translation_with_empty_sentences(self, storage_provider: SqliteStorageProvider) -> None:
        """Test saving a translation with no sentences."""
        translation = Translation(
            uuid=uuid4(),
            title="Empty",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[],
        )

        saved = storage_provider.save(translation)
        assert len(saved.sentences) == 0

    def test_save_sentence_with_empty_word_alignments(self, storage_provider: SqliteStorageProvider) -> None:
        """Test saving a sentence with no word alignments."""
        translation = Translation(
            uuid=uuid4(),
            title="No alignments",
            source_language=get_language_by("es"),
            target_language=get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Hola",
                    natural_translation="Hallo",
                    word_alignments=[],
                )
            ],
        )

        saved = storage_provider.save(translation)
        assert len(saved.sentences[0].word_alignments) == 0

    def test_multiple_operations_on_same_database(self, temp_db: Path) -> None:
        """Test that multiple provider instances can access same database."""
        with SqliteStorageProvider(temp_db) as provider1:
            translation = Translation(
                uuid=uuid4(),
                title="Test",
                source_language=get_language_by("es"),
                target_language=get_language_by("de"),
                sentences=[
                    Sentence(
                        uuid=uuid4(),
                        source_text="Hola",
                        natural_translation="Hallo",
                        word_alignments=[WordAlignment(source_word="Hola", target_word="Hallo", position=0)],
                    )
                ],
            )
            provider1.save(translation)

        with SqliteStorageProvider(temp_db) as provider2:
            retrieved = provider2.get(translation.uuid)

            assert retrieved is not None
            assert retrieved.uuid == translation.uuid
