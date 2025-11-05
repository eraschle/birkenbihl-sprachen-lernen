"""Demo application for AudioService with gTTS.

Demonstrates:
1. Generating audio for sentences
2. Batch audio generation
3. Playing audio files
4. Audio file management

Usage:
    python demo_audio_service.py
"""

import tempfile
from pathlib import Path
from uuid import uuid4

from birkenbihl.models.translation import Sentence
from birkenbihl.providers.gtts_audio_provider import GTTSAudioProvider
from birkenbihl.services.audio_service import AudioService


def demo_single_sentence():
    """Demo generating audio for single sentence."""
    print("\n" + "=" * 70)
    print("DEMO 1: Single Sentence Audio Generation")
    print("=" * 70)

    # Create service
    provider = GTTSAudioProvider(slow=False)
    service = AudioService(provider)

    # Create sentence
    sentence = Sentence(
        uuid=uuid4(),
        source_text="Hello, welcome to the Birkenbihl language learning method!",
        natural_translation="Hallo, willkommen bei der Birkenbihl-Sprachlernmethode!",
        word_alignments=[],
    )

    print(f"\nSentence: '{sentence.source_text}'")
    print(f"UUID: {sentence.uuid}")

    # Generate audio
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_dir = Path(temp_dir)

        print("\nGenerating audio (language: en)...")
        audio_path = service.generate_sentence_audio(sentence, "en", audio_dir)

        print(f"✅ Audio generated: {audio_path.name}")
        print(f"   File size: {audio_path.stat().st_size:,} bytes")
        print(f"   Exists: {audio_path.exists()}")

        # Check existence
        exists = service.audio_exists(sentence.uuid, audio_dir)
        print(f"\n✅ Audio file exists check: {exists}")


def demo_batch_generation():
    """Demo batch audio generation."""
    print("\n" + "=" * 70)
    print("DEMO 2: Batch Audio Generation")
    print("=" * 70)

    # Create service
    provider = GTTSAudioProvider(slow=False)
    service = AudioService(provider)

    # Create multiple sentences
    sentences = [
        Sentence(
            uuid=uuid4(), source_text="I am learning Spanish", natural_translation="", word_alignments=[]
        ),
        Sentence(
            uuid=uuid4(), source_text="This method is very effective", natural_translation="", word_alignments=[]
        ),
        Sentence(
            uuid=uuid4(), source_text="Active listening is important", natural_translation="", word_alignments=[]
        ),
        Sentence(
            uuid=uuid4(), source_text="Thank you for trying this demo", natural_translation="", word_alignments=[]
        ),
    ]

    print(f"\nGenerating audio for {len(sentences)} sentences...")

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_dir = Path(temp_dir)

        audio_paths = service.batch_generate_audio(sentences, "en", audio_dir)

        print(f"\n✅ Generated {len(audio_paths)} audio files:")
        for i, (sentence, audio_path) in enumerate(zip(sentences, audio_paths, strict=False), 1):
            size = audio_path.stat().st_size
            print(f"   {i}. '{sentence.source_text[:40]}...'")
            print(f"      → {audio_path.name} ({size:,} bytes)")


def demo_multilingual():
    """Demo multilingual audio generation."""
    print("\n" + "=" * 70)
    print("DEMO 3: Multilingual Audio Generation")
    print("=" * 70)

    provider = GTTSAudioProvider(slow=False)
    service = AudioService(provider)

    examples = [
        ("Hello world", "en", "English"),
        ("Hola mundo", "es", "Spanish"),
        ("Hallo Welt", "de", "German"),
        ("Bonjour le monde", "fr", "French"),
        ("Ciao mondo", "it", "Italian"),
    ]

    print("\nGenerating audio in multiple languages...")

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_dir = Path(temp_dir)

        for text, lang_code, lang_name in examples:
            sentence = Sentence(uuid=uuid4(), source_text=text, natural_translation="", word_alignments=[])

            audio_path = service.generate_sentence_audio(sentence, lang_code, audio_dir)
            size = audio_path.stat().st_size

            print(f"   ✅ {lang_name} ({lang_code}): '{text}'")
            print(f"      → {audio_path.name} ({size:,} bytes)")


def demo_slow_mode():
    """Demo slow speech mode for learning."""
    print("\n" + "=" * 70)
    print("DEMO 4: Slow Speech Mode (For Learning)")
    print("=" * 70)

    fast_provider = GTTSAudioProvider(slow=False)
    slow_provider = GTTSAudioProvider(slow=True)

    fast_service = AudioService(fast_provider)
    slow_service = AudioService(slow_provider)

    sentence = Sentence(
        uuid=uuid4(),
        source_text="The quick brown fox jumps over the lazy dog",
        natural_translation="",
        word_alignments=[],
    )

    print(f"\nSentence: '{sentence.source_text}'")

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_dir = Path(temp_dir)

        # Generate both versions
        fast_path = fast_service.generate_sentence_audio(sentence, "en", audio_dir)
        sentence.uuid = uuid4()  # New UUID for different file
        slow_path = slow_service.generate_sentence_audio(sentence, "en", audio_dir)

        fast_size = fast_path.stat().st_size
        slow_size = slow_path.stat().st_size

        print(f"\n✅ Normal speed: {fast_path.name} ({fast_size:,} bytes)")
        print(f"✅ Slow speed: {slow_path.name} ({slow_size:,} bytes)")
        print(f"\nSlow audio is {((slow_size / fast_size - 1) * 100):.1f}% larger (longer duration)")


def demo_supported_languages():
    """Demo listing supported languages."""
    print("\n" + "=" * 70)
    print("DEMO 5: Supported Languages")
    print("=" * 70)

    provider = GTTSAudioProvider()
    service = AudioService(provider)

    languages = service.get_supported_languages()

    print(f"\nTotal supported languages: {len(languages)}")
    print(f"\nLanguage codes: {', '.join(languages)}")


def demo_error_handling():
    """Demo error handling for invalid input."""
    print("\n" + "=" * 70)
    print("DEMO 6: Error Handling")
    print("=" * 70)

    provider = GTTSAudioProvider()
    service = AudioService(provider)

    sentence = Sentence(uuid=uuid4(), source_text="Test", natural_translation="", word_alignments=[])

    print("\nAttempting to generate audio with invalid language code...")

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_dir = Path(temp_dir)

        try:
            service.generate_sentence_audio(sentence, "invalid_lang", audio_dir)
            print("❌ Should have raised ValueError")
        except ValueError as e:
            print(f"✅ Correctly raised ValueError: {e}")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("BIRKENBIHL AUDIO SERVICE DEMO")
    print("Powered by gTTS (Google Text-to-Speech)")
    print("=" * 70)

    # Run demos
    demo_single_sentence()
    demo_batch_generation()
    demo_multilingual()
    demo_slow_mode()
    demo_supported_languages()
    demo_error_handling()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nAll audio files were generated in temporary directories")
    print("and have been automatically cleaned up.")
    print("\nFor production use:")
    print("1. Store audio files in persistent directory")
    print("2. Implement caching to avoid regenerating existing audio")
    print("3. Add audio playback functionality with PySide6 QMediaPlayer")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
