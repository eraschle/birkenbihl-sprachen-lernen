"""Storage-related exceptions."""


class StorageError(Exception):
    """Base exception for storage operations."""


class NotFoundError(StorageError):
    """Raised when a requested entity is not found."""


class DatabaseConnectionError(StorageError):
    """Raised when database connection fails."""


class DatabaseIntegrityError(StorageError):
    """Raised when database integrity constraint is violated."""
