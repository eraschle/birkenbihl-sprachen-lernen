"""Qt tests for the create mode: AI calls go through TranslationService."""

from pathlib import Path
from unittest.mock import MagicMock

from pytestqt.qtbot import QtBot

from birkenbihl.gui.models.app_state import AppState
from birkenbihl.gui.views.create_mode_panel import CreateModePanel
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.services.language_service import get_language_by
from birkenbihl.services.settings_service import SettingsService
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


def _panel(qtbot: QtBot, tmp_path: Path, factory: MagicMock) -> CreateModePanel:
    service = TranslationService(None, JsonStorageProvider(tmp_path / "translations.json"), factory)
    settings = SettingsService(tmp_path / "settings.yaml")
    settings.load_settings()
    panel = CreateModePanel(service, settings, AppState())
    qtbot.addWidget(panel)
    return panel


class TestCreateModePanel:
    def test_ai_translation_goes_through_service_with_chosen_provider(self, qtbot: QtBot, tmp_path: Path) -> None:
        factory = MagicMock()
        panel = _panel(qtbot, tmp_path, factory)
        provider = ProviderConfig(name="Claude", provider_type="anthropic", model="m", api_key="k")

        result = panel._create_ai_translation(
            "Titel", "Yo te extrañaré", get_language_by("es"), get_language_by("de"), provider
        )

        factory.assert_called_once_with(provider)
        factory.return_value.translate.assert_called_once()
        assert result is factory.return_value.translate.return_value

    def test_auto_detect_needs_no_ai_provider(self, qtbot: QtBot, tmp_path: Path) -> None:
        factory = MagicMock()
        panel = _panel(qtbot, tmp_path, factory)
        panel._source_selector.set_language("auto")
        panel._text_input.setPlainText("Mas comprendo que llegó tu tiempo, que Dios te ha llamado.")

        assert panel._get_source_language().code == "es"
        factory.assert_not_called()
