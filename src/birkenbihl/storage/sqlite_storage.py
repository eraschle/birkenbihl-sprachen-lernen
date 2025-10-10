"""SQLite storage provider implementation using SQLModel."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlmodel import Session, SQLModel, create_engine, desc, select

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.storage.dao_models import SentenceDAO, TranslationDAO, WordAlignmentDAO
from birkenbihl.storage.exceptions import DatabaseConnectionError, NotFoundError, StorageError


class SqliteStorageProvider:
    """SQLite-based storage provider for translations."""

    def __init__(self, database_path: str | Path = "birkenbihl.db"):
        """Initialize SQLite storage provider.

        Args:
            database_path: Path to SQLite database file

        Raises:
            DatabaseConnectionError: If database initialization fails
        """
        self.database_path = Path(database_path)
        try:
            self.engine = create_engine(f"sqlite:///{self.database_path}", echo=False)
            SQLModel.metadata.create_all(self.engine)
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize database: {e}") from e

    def save(self, translation: Translation) -> Translation:
        """Save a new translation or update existing one.

        Args:
            translation: Translation to save

        Returns:
            Saved translation with updated metadata

        Raises:
            StorageError: If save operation fails
        """
        try:
            with Session(self.engine) as session:
                existing = session.get(TranslationDAO, translation.id)
                if existing:
                    return self.update(translation)

                translation_dao = self._to_dao(translation)
                session.add(translation_dao)
                session.commit()
                session.refresh(translation_dao)
                return self._from_dao(translation_dao)
        except Exception as e:
            raise StorageError(f"Failed to save translation: {e}") from e

    def get(self, translation_id: UUID) -> Translation | None:
        """Retrieve translation by ID.

        Args:
            translation_id: UUID of the translation

        Returns:
            Translation if found, None otherwise
        """
        try:
            with Session(self.engine) as session:
                translation_dao = session.get(TranslationDAO, translation_id)
                if not translation_dao:
                    return None
                return self._from_dao(translation_dao)
        except Exception as e:
            raise StorageError(f"Failed to retrieve translation: {e}") from e

    def list_all(self) -> list[Translation]:
        """List all stored translations.

        Returns:
            List of all translations, ordered by updated_at (newest first)
        """
        try:
            with Session(self.engine) as session:
                statement = select(TranslationDAO).order_by(desc(TranslationDAO.updated_at))
                results = session.exec(statement).all()
                return [self._from_dao(dao) for dao in results]
        except Exception as e:
            raise StorageError(f"Failed to list translations: {e}") from e

    def delete(self, translation_id: UUID) -> bool:
        """Delete translation by ID.

        Args:
            translation_id: UUID of the translation to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            with Session(self.engine) as session:
                translation_dao = session.get(TranslationDAO, translation_id)
                if not translation_dao:
                    return False
                session.delete(translation_dao)
                session.commit()
                return True
        except Exception as e:
            raise StorageError(f"Failed to delete translation: {e}") from e

    def update(self, translation: Translation) -> Translation:
        """Update existing translation.

        Args:
            translation: Translation with updated data

        Returns:
            Updated translation with new updated_at timestamp

        Raises:
            NotFoundError: If translation doesn't exist
            StorageError: If update operation fails
        """
        try:
            with Session(self.engine) as session:
                translation_dao = session.get(TranslationDAO, translation.id)
                if not translation_dao:
                    raise NotFoundError(f"Translation with ID {translation.id} not found")

                session.delete(translation_dao)
                session.flush()

                updated_translation = Translation(
                    id=translation.id,
                    title=translation.title,
                    source_language=translation.source_language,
                    target_language=translation.target_language,
                    sentences=translation.sentences,
                    created_at=translation.created_at,
                    updated_at=datetime.now(timezone.utc),
                )

                new_translation_dao = self._to_dao(updated_translation)
                session.add(new_translation_dao)
                session.commit()
                session.refresh(new_translation_dao)
                return self._from_dao(new_translation_dao)
        except NotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to update translation: {e}") from e

    def _to_dao(self, translation: Translation) -> TranslationDAO:
        """Convert domain Translation to DAO.

        Args:
            translation: Domain Translation model

        Returns:
            TranslationDAO database model
        """
        translation_dao = TranslationDAO(
            id=translation.id,
            title=translation.title,
            source_language=translation.source_language,
            target_language=translation.target_language,
            created_at=translation.created_at,
            updated_at=translation.updated_at,
        )

        translation_dao.sentences = [
            SentenceDAO(
                id=sentence.id,
                translation_id=translation.id,
                source_text=sentence.source_text,
                natural_translation=sentence.natural_translation,
                created_at=sentence.created_at,
                word_alignments=[
                    WordAlignmentDAO(
                        sentence_id=sentence.id,
                        source_word=wa.source_word,
                        target_word=wa.target_word,
                        position=wa.position,
                    )
                    for wa in sentence.word_alignments
                ],
            )
            for sentence in translation.sentences
        ]

        return translation_dao

    def _from_dao(self, translation_dao: TranslationDAO) -> Translation:
        """Convert DAO to domain Translation.

        Args:
            translation_dao: TranslationDAO database model

        Returns:
            Domain Translation model
        """
        return Translation(
            id=translation_dao.id,
            title=translation_dao.title,
            source_language=translation_dao.source_language,
            target_language=translation_dao.target_language,
            created_at=translation_dao.created_at,
            updated_at=translation_dao.updated_at,
            sentences=[
                Sentence(
                    id=sentence_dao.id,
                    source_text=sentence_dao.source_text,
                    natural_translation=sentence_dao.natural_translation,
                    created_at=sentence_dao.created_at,
                    word_alignments=[
                        WordAlignment(
                            source_word=wa_dao.source_word,
                            target_word=wa_dao.target_word,
                            position=wa_dao.position,
                        )
                        for wa_dao in sorted(sentence_dao.word_alignments, key=lambda x: x.position)
                    ],
                )
                for sentence_dao in translation_dao.sentences
            ],
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures engine is closed."""
        self.close()
        return False

    def close(self):
        """Close the database engine and release resources."""
        if hasattr(self, "engine"):
            self.engine.dispose()

    def __del__(self):
        """Cleanup on object deletion."""
        self.close()
