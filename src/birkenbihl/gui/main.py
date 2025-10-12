"""Entry point for Birkenbihl GUI application."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from birkenbihl.gui.styles.theme import ThemeManager
from birkenbihl.gui.views.main_window import MainWindow
from birkenbihl.providers.pydantic_ai_translator import (
    PydanticAITranslator,
)
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


def create_services() -> tuple[TranslationService, SettingsService]:
    """Create service instances.

    Returns:
        Tuple of (TranslationService, SettingsService)
    """
    settings_service = create_settings_service()
    translation_service = create_translation_service(settings_service)
    return translation_service, settings_service


def create_settings_service() -> SettingsService:
    """Create SettingsService instance.

    Returns:
        SettingsService instance
    """
    settings_path = Path.home() / ".birkenbihl" / "settings.yaml"
    return SettingsService(settings_path)


def create_translation_service(
    settings_service: SettingsService,
) -> TranslationService:
    """Create TranslationService instance.

    Args:
        settings_service: SettingsService instance

    Returns:
        TranslationService instance
    """
    storage_dir = Path.home() / ".birkenbihl" / "translations"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage = JsonStorageProvider(storage_dir)

    settings = settings_service.get_settings()
    provider_config = settings.get_default_provider()

    if not provider_config:
        raise RuntimeError("No default provider configured")

    translation_provider = PydanticAITranslator(provider_config)
    return TranslationService(translation_provider, storage)


def setup_exception_handler(app: QApplication) -> None:
    """Setup global exception handler.

    Args:
        app: QApplication instance
    """

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = f"{exc_type.__name__}: {exc_value}"
        QMessageBox.critical(None, "Fehler", f"Ein Fehler ist aufgetreten:\n\n{error_msg}")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Birkenbihl")
        app.setOrganizationName("Birkenbihl")

        theme_manager = ThemeManager()
        theme_manager.apply_theme(app)

        setup_exception_handler(app)

        translation_service, settings_service = create_services()
        window = MainWindow(translation_service, settings_service)
        window.show()

        return app.exec()

    except Exception as e:
        QMessageBox.critical(
            None,
            "Initialisierungsfehler",
            f"Die Anwendung konnte nicht gestartet werden:\n\n{str(e)}",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
