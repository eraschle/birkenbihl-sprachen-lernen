"""Commands for settings operations."""

from birkenbihl.gui.commands.base import Command, CommandResult
from birkenbihl.models.settings import ProviderConfig, Settings
from birkenbihl.services.settings_service import SettingsService


class AddProviderCommand:
    """Command to add a new provider."""

    def __init__(self, service: SettingsService, provider: ProviderConfig):
        """Initialize command."""
        self._service = service
        self._provider = provider

    def can_execute(self) -> bool:
        """Check if command can execute."""
        return bool(self._provider.name) and bool(self._provider.model)

    def execute(self) -> CommandResult:
        """Execute add provider."""
        if not self.can_execute():
            return CommandResult(success=False, message="Provider name and model are required")

        error = self._service.validate_provider_config(self._provider)
        if error:
            return CommandResult(success=False, message=error)

        return CommandResult(
            success=True,
            message=f"Provider '{self._provider.name}' added successfully",
            data=self._provider,
        )


class DeleteProviderCommand:
    """Command to delete a provider."""

    def __init__(self, providers: list[ProviderConfig], index: int):
        """Initialize command."""
        self._providers = providers
        self._index = index

    def can_execute(self) -> bool:
        """Check if command can execute."""
        return 0 <= self._index < len(self._providers)

    def execute(self) -> CommandResult:
        """Execute delete provider."""
        if not self.can_execute():
            return CommandResult(success=False, message="Invalid provider index")

        provider_name = self._providers[self._index].name
        return CommandResult(
            success=True,
            message=f"Provider '{provider_name}' deleted successfully",
        )


class SaveSettingsCommand:
    """Command to save settings."""

    def __init__(self, service: SettingsService, settings: Settings):
        """Initialize command."""
        self._service = service
        self._settings = settings

    def can_execute(self) -> bool:
        """Check if command can execute."""
        return True

    def execute(self) -> CommandResult:
        """Execute save settings."""
        try:
            self._service.save_settings(self._settings)
            return CommandResult(
                success=True,
                message="Settings saved successfully",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to save settings: {str(e)}",
            )
