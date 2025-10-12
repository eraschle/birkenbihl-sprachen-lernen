"""SQLite storage provider implementation for settings."""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from birkenbihl.models import dateutils
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.storage.dao_models import ProviderConfigDAO, SettingsDAO
from birkenbihl.storage.exceptions import (
    DatabaseConnectionError,
    NotFoundError,
    StorageError,
)


class SettingsStorageProvider:
    """SQLite-based storage provider for application settings."""

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

    def save(self, settings: Settings) -> Settings:
        """Save settings to database.

        Creates or updates settings. Only one settings record should exist.

        Args:
            settings: Settings to save

        Returns:
            Saved settings with updated metadata

        Raises:
            StorageError: If save operation fails
        """
        try:
            with Session(self.engine) as session:
                existing = self._get_first_settings_dao(session)
                if existing:
                    return self._update_internal(session, existing.id, settings)

                settings_dao = self._to_dao(settings)
                session.add(settings_dao)
                session.commit()
                session.refresh(settings_dao)
                return self._from_dao(settings_dao)
        except Exception as e:
            raise StorageError(f"Failed to save settings: {e}") from e

    def load(self) -> Settings:
        """Load settings from database.

        Returns the first (and should be only) settings record.

        Returns:
            Settings instance

        Raises:
            NotFoundError: If no settings exist in database
            StorageError: If load operation fails
        """
        try:
            with Session(self.engine) as session:
                settings_dao = self._get_first_settings_dao(session)
                if not settings_dao:
                    raise NotFoundError("No settings found in database")
                return self._from_dao(settings_dao)
        except NotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to load settings: {e}") from e

    def update(self, settings: Settings) -> Settings:
        """Update existing settings.

        Args:
            settings: Settings with updated data

        Returns:
            Updated settings with new updated_at timestamp

        Raises:
            NotFoundError: If settings don't exist
            StorageError: If update operation fails
        """
        try:
            with Session(self.engine) as session:
                existing = self._get_first_settings_dao(session)
                if not existing:
                    raise NotFoundError("No settings found in database")
                return self._update_internal(session, existing.id, settings)
        except NotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to update settings: {e}") from e

    def delete_all(self) -> bool:
        """Delete all settings from database.

        Returns:
            True if deleted, False if nothing to delete
        """
        try:
            with Session(self.engine) as session:
                settings_dao = self._get_first_settings_dao(session)
                if not settings_dao:
                    return False
                session.delete(settings_dao)
                session.commit()
                return True
        except Exception as e:
            raise StorageError(f"Failed to delete settings: {e}") from e

    def _update_internal(self, session: Session, settings_id: int | None, settings: Settings) -> Settings:
        """Update settings within existing session.

        Args:
            session: Active database session
            settings_id: ID of settings to update
            settings: New settings data

        Returns:
            Updated settings
        """
        settings_dao = session.get(SettingsDAO, settings_id)
        if not settings_dao:
            raise NotFoundError(f"Settings with ID {settings_id} not found")

        session.delete(settings_dao)
        session.flush()

        new_settings_dao = self._to_dao(settings)
        new_settings_dao.id = settings_id
        new_settings_dao.updated_at = dateutils.create_now()

        session.add(new_settings_dao)
        session.commit()
        session.refresh(new_settings_dao)
        return self._from_dao(new_settings_dao)

    def _get_first_settings_dao(self, session: Session) -> SettingsDAO | None:
        """Get first settings record from database.

        Args:
            session: Active database session

        Returns:
            SettingsDAO if found, None otherwise
        """
        statement = select(SettingsDAO)
        return session.exec(statement).first()

    def _to_dao(self, settings: Settings) -> SettingsDAO:
        """Convert domain Settings to DAO.

        Args:
            settings: Domain Settings model

        Returns:
            SettingsDAO database model
        """
        settings_dao = SettingsDAO(target_language=settings.target_language)

        settings_dao.providers = [
            ProviderConfigDAO(
                name=provider.name,
                settings_id=settings_dao.id or 0,
                provider_type=provider.provider_type,
                model=provider.model,
                api_key=provider.api_key,
                base_url=provider.base_url,
                is_default=provider.is_default,
                supports_streaming=provider.supports_streaming,
            )
            for provider in settings.providers
        ]

        return settings_dao

    def _from_dao(self, settings_dao: SettingsDAO) -> Settings:
        """Convert DAO to domain Settings.

        Args:
            settings_dao: SettingsDAO database model

        Returns:
            Domain Settings model
        """
        return Settings(
            target_language=settings_dao.target_language,
            providers=[
                ProviderConfig(
                    name=provider_dao.name,
                    provider_type=provider_dao.provider_type,
                    model=provider_dao.model,
                    api_key=provider_dao.api_key,
                    base_url=provider_dao.base_url,
                    is_default=provider_dao.is_default,
                    supports_streaming=provider_dao.supports_streaming,
                )
                for provider_dao in settings_dao.providers
            ],
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *_):
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
