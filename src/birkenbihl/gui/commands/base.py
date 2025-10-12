"""Base protocol for Command pattern implementation."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class CommandResult:
    """Result of command execution.

    Encapsulates the outcome of a command with success status,
    optional message, and optional return data.
    """

    success: bool
    message: str = ""
    data: object | None = None


class Command(Protocol):
    """Protocol for Command pattern.

    Commands encapsulate user actions (Create, Update, Delete).
    They execute business logic via Services and return CommandResult.

    Examples:
        CreateTranslationCommand, UpdateSentenceCommand, SaveProviderCommand
    """

    def execute(self) -> CommandResult:
        """Execute the command.

        Returns:
            CommandResult with success status and optional data

        Raises:
            Exception: If command execution fails critically
        """
        ...

    def can_execute(self) -> bool:
        """Check if command can be executed.

        Validates preconditions before execution (e.g., required fields filled).

        Returns:
            True if command is valid and can execute, False otherwise
        """
        return True
