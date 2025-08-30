"""Shared test fixtures for Birkenbihl Language Learning App."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, MagicMock
from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

from birkenbihl.models.audio import AudioData, AudioFormat, AudioQuality
from birkenbihl.models.translation import Language, Translation, TranslationType, TranslationResult
from birkenbihl.protocols.audio import AudioService
from birkenbihl.protocols.translation import TranslationProviderProtocol


# ===== Database Fixtures =====

@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    # Cleanup happens automatically for in-memory databases


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing with test data."""
    with Session(db_engine) as session:
        # Add test languages
        for lang_data in TEST_LANGUAGES:
            language = Language(**lang_data)
            session.add(language)
        
        session.commit()
        yield session


# ===== Test Data Fixtures =====

TEST_LANGUAGES = [
    {
        "id": uuid4(),
        "code": "de",
        "name": "Deutsch", 
        "native_name": "Deutsch",
        "is_active": True,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
    },
    {
        "id": uuid4(),
        "code": "es",
        "name": "Español",
        "native_name": "Español", 
        "is_active": True,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
    },
    {
        "id": uuid4(),
        "code": "en",
        "name": "English",
        "native_name": "English",
        "is_active": True,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
    },
    {
        "id": uuid4(),
        "code": "fr", 
        "name": "Français",
        "native_name": "Français",
        "is_active": True,
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
    },
]

BIRKENBIHL_TEST_DATA = {
    "spanish_texts": [
        "Lo que parecía no importante",
        "Tenlo por seguro", 
        "Fueron tantos bellos y malos momentos",
        "Hola mundo",
        "¿Cómo estás?",
    ],
    "german_natural_translations": {
        "Lo que parecía no importante": "Das, was nicht wichtig schien",
        "Tenlo por seguro": "Du kannst sicher sein",
        "Fueron tantos bellos y malos momentos": "Es waren so viele schöne und schlechte Momente",
        "Hola mundo": "Hallo Welt",
        "¿Cómo estás?": "Wie geht es dir?",
    },
    "german_word_translations": {
        "Lo que parecía no importante": "Das was schien nicht wichtig",
        "Tenlo por seguro": "Hab-es für sicher",
        "Fueron tantos bellos y malos momentos": "Waren so-viele schöne und schlechte Momente",
        "Hola mundo": "Hallo Welt",
        "¿Cómo estás?": "Wie gehts dir",
    },
}


@pytest.fixture
def test_languages():
    """Provide test language data."""
    return TEST_LANGUAGES


@pytest.fixture
def birkenbihl_test_data():
    """Provide Birkenbihl method test data."""
    return BIRKENBIHL_TEST_DATA


@pytest.fixture
def sample_spanish_text():
    """Provide a sample Spanish text for testing."""
    return "Lo que parecía no importante"


@pytest.fixture
def sample_audio_data():
    """Provide sample audio data for testing."""
    return AudioData(
        id=uuid4(),
        file_path="/tmp/test_audio.mp3",
        file_name="test_audio.mp3",
        file_size=1024000,  # 1MB
        file_format=AudioFormat.MP3,
        duration=30.5,
        sample_rate=44100,
        bit_rate=128,
        channels=2,
        quality=AudioQuality.MEDIUM,
        language_id=uuid4(),
        is_generated=True,
        tts_engine="edge-tts",
        voice_name="de-DE-KatjaNeural",
        speech_rate=1.0,
        is_background_music=False,
        volume_level=1.0,
        title="Test Audio",
        description="Audio for testing",
        tags=["test", "tts"],
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        play_count=0,
    )


# ===== Mock Provider Fixtures =====

class MockTranslationProvider:
    """Mock translation provider for testing."""
    
    def __init__(self):
        self.provider_name = "MockProvider"
        self.supported_languages = ["en", "de", "es", "fr"]
    
    async def translate_natural(
        self, 
        text: str, 
        source_language: str, 
        target_language: str,
        context: str | None = None,
    ) -> str:
        """Mock natural translation."""
        # Return German translations for Spanish texts
        if source_language == "es" and target_language == "de":
            return BIRKENBIHL_TEST_DATA["german_natural_translations"].get(
                text, f"[Natural DE] {text}"
            )
        return f"[Natural {target_language.upper()}] {text}"
    
    async def translate_word_for_word(
        self,
        text: str,
        source_language: str,
        target_language: str,
        preserve_structure: bool = True,
    ) -> str:
        """Mock word-for-word translation."""
        # Return German word-for-word translations for Spanish texts
        if source_language == "es" and target_language == "de":
            return BIRKENBIHL_TEST_DATA["german_word_translations"].get(
                text, f"[Word-for-word DE] {text}"
            )
        return f"[Word-for-word {target_language.upper()}] {text}"
    
    async def translate_birkenbihl(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: str | None = None,
    ) -> TranslationResult:
        """Mock Birkenbihl translation with complete result."""
        natural = await self.translate_natural(text, source_language, target_language, context)
        word_by_word = await self.translate_word_for_word(text, source_language, target_language)
        
        # Create formatted decoding (simplified for testing)
        formatted = self._format_birkenbihl_simple(text, word_by_word)
        
        return TranslationResult(
            natural_translation=natural,
            word_by_word_translation=word_by_word,
            formatted_decoding=formatted,
        )
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if language is supported."""
        return language_code in self.supported_languages
    
    def _format_birkenbihl_simple(self, original: str, translation: str) -> str:
        """Simple Birkenbihl formatting for testing."""
        orig_words = original.split()
        trans_words = translation.split()
        
        # Ensure same length
        max_len = max(len(orig_words), len(trans_words))
        while len(orig_words) < max_len:
            orig_words.append("")
        while len(trans_words) < max_len:
            trans_words.append("")
        
        # Simple alignment
        orig_line = "  ".join(orig_words)
        trans_line = "  ".join(trans_words)
        
        return f"{orig_line}\n{trans_line}"


class MockAudioService:
    """Mock audio service for testing."""
    
    def __init__(self):
        self.provider_name = "MockAudioProvider"
        self._is_playing = False
        self._current_audio = None
    
    def generate_speech(
        self,
        text: str,
        language_code: str,
        voice_name: str | None = None,
        speech_rate: float = 1.0,
        quality: AudioQuality = AudioQuality.MEDIUM,
    ) -> AudioData:
        """Mock speech generation."""
        return AudioData(
            id=uuid4(),
            file_path=f"/tmp/mock_{uuid4()}.mp3",
            file_name=f"mock_tts_{language_code}.mp3",
            file_size=len(text) * 100,  # Mock size based on text length
            file_format=AudioFormat.MP3,
            duration=len(text.split()) * 0.5,  # Mock duration: 0.5s per word
            sample_rate=44100,
            bit_rate=128 if quality == AudioQuality.MEDIUM else 192,
            channels=2,
            quality=quality,
            is_generated=True,
            tts_engine="mock-tts",
            voice_name=voice_name or f"{language_code}-DEFAULT",
            speech_rate=speech_rate,
            is_background_music=False,
            volume_level=1.0,
            title=f"TTS: {text[:30]}...",
            description=f"Generated TTS for {language_code}",
            tags=["tts", "mock", language_code],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            play_count=0,
        )
    
    def play_audio(self, audio_data: AudioData) -> None:
        """Mock audio playback."""
        self._is_playing = True
        self._current_audio = audio_data
    
    def play_audio_file(self, file_path: Path) -> None:
        """Mock file playback."""
        self._is_playing = True
        self._current_audio = file_path
    
    def stop_playback(self) -> None:
        """Mock stop playback."""
        self._is_playing = False
        self._current_audio = None
    
    def convert_audio_format(
        self,
        input_data: AudioData,
        target_format: AudioFormat,
        target_quality: AudioQuality | None = None,
    ) -> AudioData:
        """Mock audio conversion."""
        # Create new AudioData with different format
        converted = AudioData(**input_data.model_dump())
        converted.id = uuid4()
        converted.file_format = target_format
        converted.file_path = converted.file_path.replace(
            f".{input_data.file_format.value}", f".{target_format.value}"
        )
        converted.file_name = converted.file_name.replace(
            f".{input_data.file_format.value}", f".{target_format.value}"
        )
        if target_quality:
            converted.quality = target_quality
        return converted
    
    def get_audio_info(self, file_path: Path) -> AudioData:
        """Mock getting audio file info."""
        return AudioData(
            id=uuid4(),
            file_path=str(file_path),
            file_name=file_path.name,
            file_size=1024000,  # Mock size
            file_format=AudioFormat.MP3,
            duration=30.0,
            sample_rate=44100,
            bit_rate=128,
            channels=2,
            quality=AudioQuality.MEDIUM,
            is_generated=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            play_count=0,
        )
    
    def is_format_supported(self, format_type: AudioFormat) -> bool:
        """Check if format is supported."""
        return format_type in [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.OGG]
    
    def get_available_voices(self, language_code: str | None = None) -> list[str]:
        """Mock available voices."""
        if language_code == "de":
            return ["de-DE-KatjaNeural", "de-DE-ConradNeural"]
        elif language_code == "es":
            return ["es-ES-ElviraNeural", "es-ES-AlvaroNeural"]
        elif language_code == "en":
            return ["en-US-JennyNeural", "en-US-GuyNeural"]
        return ["default-voice"]
    
    def validate_speech_rate(self, rate: float) -> bool:
        """Validate speech rate."""
        return 0.1 <= rate <= 3.0
    
    def create_background_audio(
        self,
        primary_audio: AudioData,
        background_music_path: Path | None = None,
        volume_ratio: float = 0.3,
    ) -> AudioData:
        """Mock background audio creation."""
        bg_audio = AudioData(**primary_audio.model_dump())
        bg_audio.id = uuid4()
        bg_audio.is_background_music = True
        bg_audio.volume_level = volume_ratio
        bg_audio.file_name = f"bg_{bg_audio.file_name}"
        bg_audio.title = f"Background: {bg_audio.title}"
        return bg_audio
    
    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._is_playing
    
    @property
    def current_audio(self) -> Any:
        """Get currently playing audio."""
        return self._current_audio


@pytest.fixture
def mock_translation_provider():
    """Create mock translation provider."""
    return MockTranslationProvider()


@pytest.fixture
def mock_audio_service():
    """Create mock audio service."""
    return MockAudioService()


# ===== Service Fixtures =====

@pytest.fixture
def translation_service(mock_translation_provider, db_session):
    """Create translation service with mock provider."""
    # Import here to avoid module loading issues
    from birkenbihl.services.translation_service import TranslationService
    return TranslationService(mock_translation_provider, db_session)


@pytest.fixture
def audio_service_instance(mock_audio_service):
    """Create audio service instance with mock."""
    # This would normally be the concrete audio service
    # but for testing we'll use the mock
    return mock_audio_service


# ===== Utility Fixtures =====

@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary audio file for testing."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data for testing")
    return audio_file


@pytest.fixture
def sample_translations(db_session, test_languages):
    """Create sample translation records in the database."""
    translations = []
    
    # Get language IDs
    de_lang = db_session.query(Language).filter(Language.code == "de").first()
    es_lang = db_session.query(Language).filter(Language.code == "es").first()
    
    sample_data = [
        {
            "source_text": "Hola mundo",
            "source_language_id": es_lang.id,
            "target_language_id": de_lang.id,
            "translation_type": TranslationType.NATURAL,
            "translated_text": "Hallo Welt",
            "learning_phase": 1,
            "is_reviewed": False,
            "review_count": 0,
        },
        {
            "source_text": "Hola mundo", 
            "source_language_id": es_lang.id,
            "target_language_id": de_lang.id,
            "translation_type": TranslationType.WORD_FOR_WORD,
            "translated_text": "Hallo Welt",
            "learning_phase": 2,
            "is_reviewed": True,
            "review_count": 3,
            "difficulty_rating": 2,
        },
    ]
    
    for data in sample_data:
        translation = Translation(**data)
        translations.append(translation)
        db_session.add(translation)
    
    db_session.commit()
    return translations


# ===== Async Test Support =====

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


# ===== Parametrized Test Data =====

@pytest.fixture(params=["es", "de", "en", "fr"])
def language_code(request):
    """Parametrized language codes for multi-language tests."""
    return request.param


@pytest.fixture(params=[
    AudioFormat.MP3,
    AudioFormat.WAV,
    AudioFormat.OGG,
])
def audio_format(request):
    """Parametrized audio formats for testing."""
    return request.param


@pytest.fixture(params=[
    AudioQuality.LOW,
    AudioQuality.MEDIUM,
    AudioQuality.HIGH,
])
def audio_quality(request):
    """Parametrized audio qualities for testing."""
    return request.param


@pytest.fixture(params=[0.5, 1.0, 1.5, 2.0])
def speech_rate(request):
    """Parametrized speech rates for testing."""
    return request.param