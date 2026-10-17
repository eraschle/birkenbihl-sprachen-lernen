"""Entry point for Birkenbihl GUI application."""

import sys
import traceback
import types

from PySide6.QtWidgets import QApplication, QMessageBox

from birkenbihl.gui.models.app_services import AppServices
from birkenbihl.gui.styles.theme import ThemeManager
from birkenbihl.gui.views.main_window import MainWindow
from birkenbihl.providers.piper_audio_provider import PiperAudioProvider
from birkenbihl.providers.pydantic_ai_translator import translator_factory
from birkenbihl.services import path_service as ps
from birkenbihl.services.audio_service import AudioService
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


def create_services() -> AppServices:
    """Create the application services.

    Returns:
        Translation, settings and audio services
    """
    settings_service = create_settings_service()
    translation_service = create_translation_service(settings_service)
    audio_service = AudioService(
        settings_service, PiperAudioProvider(ps.get_app_path("piper-voices")), ps.get_app_path("audio-cache")
    )
    return AppServices(translation_service, settings_service, audio_service)


def create_settings_service() -> SettingsService:
    """Create SettingsService instance.

    Returns:
        SettingsService instance
    """
    return SettingsService(ps.get_setting_path())


def create_translation_service(service: SettingsService) -> TranslationService:
    """Create TranslationService instance.

    Args:
        settings_service: SettingsService instance

    Returns:
        TranslationService instance
    """
    storage_dir = ps.get_translation_path("translations")
    storage = JsonStorageProvider(storage_dir)
    settings = service.load_settings()
    if not settings:
        raise RuntimeError(f"Failed to load settings from {service._file_path}")

    factory = translator_factory(settings)
    provider = None
    if provider_config := settings.get_default_provider():
        provider = factory(provider_config)

    return TranslationService(provider, storage, factory)


def setup_exception_handler() -> None:
    """Setup global exception handler.

    Args:
        app: QApplication instance
    """

    def handle_exception(
        exc_type: type[BaseException], exc_value: BaseException, exc_traceback: types.TracebackType | None
    ) -> None:
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = f"{exc_type.__name__}: {exc_value}"
        QMessageBox.critical(None, "Fehler", f"Ein Fehler ist aufgetreten:\n\n{error_msg}\n{traceback.format_exc()}")
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

        setup_exception_handler()

        window = MainWindow(create_services())
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
