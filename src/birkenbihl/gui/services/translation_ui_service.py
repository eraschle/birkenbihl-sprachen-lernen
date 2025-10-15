"""UI service layer for GUI (encapsulates storage/service initialization)."""

from threading import Lock
from typing import Self
from uuid import UUID

from birkenbihl.models.languages import Language
from birkenbihl.models.settings import ProviderConfig
from birkenbihl.models.translation import Translation
from birkenbihl.providers.pydantic_ai_translator import PydanticAITranslator
from birkenbihl.services import path_service as ps
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider


class TranslationUIService:
    """Service layer for GUI operations.

    Singleton pattern with lazy initialization.
    Encapsulates storage/service initialization.
    """

    _instance: Self | None = None
    _lock: Lock = Lock()

    def __init__(self):
        if TranslationUIService._instance is not None:
            raise RuntimeError("Use get_instance() to get singleton")
        self._storage: JsonStorageProvider | None = None
        self._service: TranslationService | None = None

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._instance.__init__()
        return cls._instance

    def _ensure_initialized(self) -> None:
        if self._storage is None:
            storage_dir = ps.get_translation_path("translations")
            self._storage = JsonStorageProvider(storage_dir)
        if self._service is None:
            self._service = TranslationService(None, self._storage)

    @property
    def storage(self) -> JsonStorageProvider:
        self._ensure_initialized()
        return self._storage  # type: ignore

    @property
    def service(self) -> TranslationService:
        self._ensure_initialized()
        return self._service  # type: ignore

    def get_translation(self, translation_id: UUID) -> Translation | None:
        return self.service.get_translation(translation_id)

    def list_translations(self) -> list[Translation]:
        return self.service.list_all_translations()

    def delete_translation(self, translation_id: UUID) -> bool:
        return self.service.delete_translation(translation_id)

    def translate_and_save(
        self, text: str, source_lang: Language, target_lang: Language, title: str, provider: ProviderConfig
    ) -> Translation:
        translator = PydanticAITranslator(provider)
        temp_service = TranslationService(translator, self.storage)
        translation = temp_service.translate(text, source_lang, target_lang, title)
        return temp_service.save_translation(translation=translation)
