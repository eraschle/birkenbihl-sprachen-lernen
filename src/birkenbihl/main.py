"""Main entry point for the Birkenbihl app."""

import os
from dotenv import load_dotenv
from nicegui import ui

from .providers.pydantic_ai_provider import PydanticAITranslationProvider
from .services.translation_service import TranslationService
from .services.audio_service import AudioService
from .ui.main_ui import BirkenbihUI


def main() -> None:
    """Main function to start the app."""
    # Load environment variables
    load_dotenv()
    
    # Initialize services
    provider = PydanticAITranslationProvider()
    translation_service = TranslationService(provider)
    audio_service = AudioService()
    
    # Initialize UI
    BirkenbihUI(translation_service, audio_service)
    
    # Start the app
    ui.run(
        title="Birkenbihl Sprachlern-App",
        port=8080,
        show=True
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
