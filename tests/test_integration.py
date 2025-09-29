"""Integration tests for complete Birkenbihl translation workflow.

This module tests the complete end-to-end functionality of the Birkenbihl language
learning app, including natural translation, word-by-word dekodierung, database
storage, and proper formatting according to the Birkenbihl method.

Tests use existing conftest fixtures and focus on the real-world examples from
ORIGINAL_REQUIREMENTS.md to ensure compliance with the Birkenbihl method.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlmodel import select

from birkenbihl.models.translation import Translation, Language, TranslationType


class TestCompleteTranslationFlow:
    """Test complete translation workflow from input to storage."""

    @pytest.mark.asyncio
    async def test_complete_birkenbihl_workflow_lo_que_parecia(
        self, mock_translation_provider, db_session, birkenbihl_test_data
    ):
        """Test complete Birkenbihl workflow for 'Lo que parecía no importante'."""
        original_text = "Lo que parecía no importante"
        source_lang = "es"
        target_lang = "de"

        # Get complete Birkenbihl translation
        result = await mock_translation_provider.translate_birkenbihl(original_text, source_lang, target_lang)

        # Verify natural translation matches expected
        expected_natural = birkenbihl_test_data["german_natural_translations"][original_text]
        assert result.natural_translation == expected_natural

        # Verify word-by-word translation
        expected_word_by_word = birkenbihl_test_data["german_word_translations"][original_text]
        assert result.word_by_word_translation == expected_word_by_word

        # Verify formatted dekodierung has proper structure
        lines = result.formatted_decoding.split("\n")
        assert len(lines) == 2

        # Check that all original words are present
        orig_line = lines[0]
        for word in original_text.split():
            assert word in orig_line

        # Check that translation words are present
        trans_line = lines[1]
        for word in expected_word_by_word.split():
            assert word in trans_line

        # Verify double spacing (Birkenbihl method requirement)
        assert "  " in orig_line
        assert "  " in trans_line

        # Store both translations in database
        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        # Store natural translation
        natural_translation = Translation(
            id=uuid4(),
            source_text=original_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text=result.natural_translation,
            created_at=datetime.utcnow(),
        )
        db_session.add(natural_translation)

        # Store dekodierung with formatted alignment
        dekodierung_translation = Translation(
            id=uuid4(),
            source_text=original_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text=result.formatted_decoding,
            word_breakdown={"Lo": "Das", "que": "was", "parecía": "schien", "no": "nicht", "importante": "wichtig"},
            learning_phase=1,
            created_at=datetime.utcnow(),
        )
        db_session.add(dekodierung_translation)
        db_session.commit()

        # Verify both are stored correctly
        stored_translations = db_session.exec(select(Translation).where(Translation.source_text == original_text)).all()

        assert len(stored_translations) == 2
        types = [t.translation_type for t in stored_translations]
        assert TranslationType.NATURAL in types
        assert TranslationType.WORD_FOR_WORD in types

        # Verify dekodierung formatting is preserved
        dekodierung = next(t for t in stored_translations if t.translation_type == TranslationType.WORD_FOR_WORD)
        assert dekodierung.translated_text == result.formatted_decoding
        assert dekodierung.is_dekodierung == True
        assert dekodierung.word_breakdown is not None
        assert "Lo" in dekodierung.word_breakdown

    @pytest.mark.asyncio
    async def test_complete_birkenbihl_workflow_tenlo_por_seguro(
        self, mock_translation_provider, db_session, birkenbihl_test_data
    ):
        """Test complete workflow for 'Tenlo por seguro' - alignment test."""
        original_text = "Tenlo por seguro"
        source_lang = "es"
        target_lang = "de"

        # Get complete Birkenbihl translation
        result = await mock_translation_provider.translate_birkenbihl(original_text, source_lang, target_lang)

        # Verify natural translation
        expected_natural = birkenbihl_test_data["german_natural_translations"][original_text]
        assert result.natural_translation == expected_natural

        # Verify word-by-word translation with compound word handling
        expected_word_by_word = birkenbihl_test_data["german_word_translations"][original_text]
        assert result.word_by_word_translation == expected_word_by_word
        assert "Hab-es" in result.word_by_word_translation  # Compound word test

        # Verify alignment according to specification:
        # Tenlo   por  seguro
        # Hab-es  für  sicher
        lines = result.formatted_decoding.split("\n")
        assert len(lines) == 2

        orig_words = [w.strip() for w in lines[0].split("  ") if w.strip()]
        trans_words = [w.strip() for w in lines[1].split("  ") if w.strip()]

        # Should have same number of word positions
        assert len(orig_words) == len(trans_words) == 3

        # Verify specific word mappings
        assert "Tenlo" in orig_words
        assert "por" in orig_words
        assert "seguro" in orig_words
        assert "Hab-es" in trans_words  # Compound word preserved
        assert "für" in trans_words
        assert "sicher" in trans_words

        # Test database storage
        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        translation = Translation(
            id=uuid4(),
            source_text=original_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text=result.formatted_decoding,
            word_breakdown={"Tenlo": "Hab-es", "por": "für", "seguro": "sicher"},
            learning_phase=1,
            created_at=datetime.utcnow(),
        )

        db_session.add(translation)
        db_session.commit()

        # Verify compound word handling is preserved
        saved = db_session.get(Translation, translation.id)
        assert saved.word_breakdown["Tenlo"] == "Hab-es"
        assert "Hab-es" in saved.translated_text

    @pytest.mark.asyncio
    async def test_complete_birkenbihl_workflow_longer_sentence(
        self, mock_translation_provider, db_session, birkenbihl_test_data
    ):
        """Test complete workflow for longer sentence: 'Fueron tantos bellos y malos momentos'."""
        original_text = "Fueron tantos bellos y malos momentos"
        source_lang = "es"
        target_lang = "de"

        # Get complete Birkenbihl translation
        result = await mock_translation_provider.translate_birkenbihl(original_text, source_lang, target_lang)

        # Verify natural translation handles longer sentence
        expected_natural = birkenbihl_test_data["german_natural_translations"][original_text]
        assert result.natural_translation == expected_natural
        assert len(result.natural_translation) > len(original_text)  # German tends to be longer

        # Verify word-by-word translation
        expected_word_by_word = birkenbihl_test_data["german_word_translations"][original_text]
        assert result.word_by_word_translation == expected_word_by_word

        # Verify formatted dekodierung handles all 6 words
        lines = result.formatted_decoding.split("\n")
        assert len(lines) == 2

        # All original words should be present and aligned
        original_words = ["Fueron", "tantos", "bellos", "y", "malos", "momentos"]
        orig_line = lines[0]
        for word in original_words:
            assert word in orig_line

        # All translation words should be present
        expected_translations = ["Waren", "so-viele", "schöne", "und", "schlechte", "Momente"]
        trans_line = lines[1]
        for word in expected_translations:
            # Check if word or similar word is present (case insensitive)
            assert any(word.lower() in w.lower() for w in trans_line.split())

        # Test storage of longer sentence
        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        translation = Translation(
            id=uuid4(),
            source_text=original_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text=result.formatted_decoding,
            word_breakdown={
                "Fueron": "Waren",
                "tantos": "so-viele",
                "bellos": "schöne",
                "y": "und",
                "malos": "schlechte",
                "momentos": "momente",
            },
            learning_phase=1,
            created_at=datetime.utcnow(),
        )

        db_session.add(translation)
        db_session.commit()

        # Verify longer text storage
        saved = db_session.get(Translation, translation.id)
        assert len(saved.source_text) > 30
        assert saved.translated_text.count("\n") == 1  # Exactly one line break for alignment
        assert len(saved.word_breakdown) == 6  # All 6 words mapped


class TestDatabaseStorageBothTypes:
    """Test database storage for both translation types."""

    def test_store_natural_and_dekodierung_for_same_text(self, db_session):
        """Test storing both natural and dekodierung translations for same source text."""
        # Get languages from database
        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        source_text = "Hola mundo"

        # Store natural translation
        natural = Translation(
            id=uuid4(),
            source_text=source_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.NATURAL,
            translated_text="Hallo Welt",
            learning_phase=1,
            created_at=datetime.utcnow(),
        )

        # Store dekodierung with formatting
        formatted_dekodierung = "Hola  mundo\nHallo Welt"
        dekodierung = Translation(
            id=uuid4(),
            source_text=source_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text=formatted_dekodierung,
            word_breakdown={"Hola": "Hallo", "mundo": "Welt"},
            learning_phase=2,  # Different learning phase
            created_at=datetime.utcnow(),
        )

        db_session.add(natural)
        db_session.add(dekodierung)
        db_session.commit()

        # Verify both are stored
        all_translations = db_session.exec(select(Translation).where(Translation.source_text == source_text)).all()

        assert len(all_translations) == 2

        # Verify types are different
        types = [t.translation_type for t in all_translations]
        assert TranslationType.NATURAL in types
        assert TranslationType.WORD_FOR_WORD in types

        # Verify content differences
        natural_stored = next(t for t in all_translations if t.translation_type == TranslationType.NATURAL)
        dekodierung_stored = next(t for t in all_translations if t.translation_type == TranslationType.WORD_FOR_WORD)

        assert natural_stored.translated_text == "Hallo Welt"
        assert dekodierung_stored.translated_text == formatted_dekodierung
        assert dekodierung_stored.is_dekodierung == True
        assert natural_stored.word_breakdown is None
        assert dekodierung_stored.word_breakdown is not None
        assert len(dekodierung_stored.word_breakdown) == 2

    def test_dekodierung_preserves_formatting_through_storage(self, db_session):
        """Test that dekodierung formatting is preserved through database save/load cycle."""
        # Create formatted dekodierung according to Birkenbihl method
        original_text = "Buenos días"
        formatted_dekodierung = "Buenos días\nGuten Tag"

        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        translation = Translation(
            id=uuid4(),
            source_text=original_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text=formatted_dekodierung,
            word_breakdown={"Buenos": "Guten", "días": "Tag"},
            learning_phase=1,
            created_at=datetime.utcnow(),
        )

        db_session.add(translation)
        db_session.commit()

        # Retrieve and verify formatting is preserved
        saved = db_session.get(Translation, translation.id)

        assert saved.translated_text == formatted_dekodierung
        assert saved.translated_text.count("\n") == 1
        assert "Buenos" in saved.translated_text
        assert "Guten" in saved.translated_text

        # Verify line structure is maintained
        lines = saved.translated_text.split("\n")
        assert len(lines) == 2
        assert lines[0] == "Buenos días"
        assert lines[1] == "Guten Tag"

    def test_multiple_dekodierung_entries_different_texts(self, db_session, birkenbihl_test_data):
        """Test storing multiple dekodierung entries for different Spanish texts."""
        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        # Store dekodierung for multiple texts from test data
        spanish_texts = birkenbihl_test_data["spanish_texts"][:3]  # First 3 texts
        stored_translations = []

        for spanish_text in spanish_texts:
            german_word_translation = birkenbihl_test_data["german_word_translations"][spanish_text]

            # Create simple formatted version
            formatted = f"{spanish_text}\n{german_word_translation}"

            translation = Translation(
                id=uuid4(),
                source_text=spanish_text,
                source_language_id=es_lang.id,
                target_language_id=de_lang.id,
                translation_type=TranslationType.WORD_FOR_WORD,
                translated_text=formatted,
                learning_phase=1,
                created_at=datetime.utcnow(),
            )

            stored_translations.append(translation)
            db_session.add(translation)

        db_session.commit()

        # Verify all are stored
        all_dekodierung = db_session.exec(
            select(Translation).where(Translation.translation_type == TranslationType.WORD_FOR_WORD)
        ).all()

        assert len(all_dekodierung) >= len(spanish_texts)

        # Verify each text has its dekodierung
        stored_texts = [t.source_text for t in all_dekodierung]
        for text in spanish_texts:
            assert text in stored_texts

        # Verify dekodierung properties
        for translation in all_dekodierung:
            if translation.source_text in spanish_texts:
                assert translation.is_dekodierung == True
                assert "\n" in translation.translated_text
                assert translation.learning_phase >= 1


class TestBirkenbihIFormattingEndToEnd:
    """Test Birkenbihl formatting from end to end."""

    def test_formatting_algorithm_with_test_data(self, mock_translation_provider, birkenbihl_test_data):
        """Test formatting algorithm with various text examples."""
        spanish_texts = birkenbihl_test_data["spanish_texts"]

        for spanish_text in spanish_texts:
            german_word = birkenbihl_test_data["german_word_translations"][spanish_text]

            # Test formatting
            formatted = mock_translation_provider._format_birkenbihl_simple(spanish_text, german_word)

            # Verify basic structure
            lines = formatted.split("\n")
            assert len(lines) == 2, f"Failed for text: {spanish_text}"

            # Verify original text is in first line
            assert spanish_text.replace(" ", "  ") in lines[0] or all(
                word in lines[0] for word in spanish_text.split()
            ), f"Original text not properly formatted: {spanish_text}"

            # Verify translation is in second line
            assert all(word in lines[1] for word in german_word.split()), (
                f"Translation not properly formatted: {german_word}"
            )

            # Verify double spacing (Birkenbihl requirement)
            if len(spanish_text.split()) > 1:
                assert "  " in lines[0], f"Missing double spacing in: {spanish_text}"

    def test_alignment_edge_cases(self, mock_translation_provider):
        """Test alignment algorithm with edge cases."""
        test_cases = [
            # Different word counts
            ("Hola", "Hallo lieber Freund"),
            ("Buenos días amigo", "Hallo"),
            # Very long words
            ("supercalifragilistico", "unglaublichkompliziert"),
            # Empty cases
            ("", ""),
            ("Hola", ""),
            ("", "Hallo"),
        ]

        for original, translation in test_cases:
            if not original and not translation:
                continue  # Skip double empty case

            formatted = mock_translation_provider._format_birkenbihl_simple(original, translation)
            lines = formatted.split("\n")

            assert len(lines) == 2, f"Failed structure for: '{original}' -> '{translation}'"

            # Both lines should exist (even if empty)
            assert isinstance(lines[0], str)
            assert isinstance(lines[1], str)

            # If original has content, it should be in first line
            if original:
                assert any(word in lines[0] for word in original.split())

            # If translation has content, it should be in second line
            if translation:
                assert any(word in lines[1] for word in translation.split())

    @pytest.mark.asyncio
    async def test_end_to_end_formatting_with_database_round_trip(self, mock_translation_provider, db_session):
        """Test formatting preservation through complete workflow including database."""
        original_text = "¿Cómo estás?"
        source_lang = "es"
        target_lang = "de"

        # Get formatted translation
        result = await mock_translation_provider.translate_birkenbihl(original_text, source_lang, target_lang)

        # Store in database
        de_lang = db_session.exec(select(Language).where(Language.code == "de")).first()
        es_lang = db_session.exec(select(Language).where(Language.code == "es")).first()

        translation = Translation(
            id=uuid4(),
            source_text=original_text,
            source_language_id=es_lang.id,
            target_language_id=de_lang.id,
            translation_type=TranslationType.WORD_FOR_WORD,
            translated_text=result.formatted_decoding,
            word_breakdown={"¿Cómo": "Wie", "estás?": "gehts dir"},
            learning_phase=1,
            created_at=datetime.utcnow(),
        )

        db_session.add(translation)
        db_session.commit()

        # Retrieve and verify formatting integrity
        saved = db_session.get(Translation, translation.id)
        retrieved_formatting = saved.translated_text

        # Verify formatting matches original
        assert retrieved_formatting == result.formatted_decoding

        # Verify structure is maintained
        lines = retrieved_formatting.split("\n")
        assert len(lines) == 2

        # Verify content is preserved
        assert "¿Cómo estás?" in lines[0] or all(
            word.replace("¿", "").replace("?", "") in lines[0] for word in original_text.split()
        )

        # Verify alignment characteristics
        orig_words = [w for w in lines[0].split("  ") if w.strip()]
        trans_words = [w for w in lines[1].split("  ") if w.strip()]

        # Should have consistent word positions
        assert len(orig_words) == len(trans_words)


class TestRealWorldBirkenbihIExamples:
    """Test with specific real examples from ORIGINAL_REQUIREMENTS.md."""

    @pytest.mark.asyncio
    async def test_specification_example_lo_que_parecia_formatting(self, mock_translation_provider):
        """Test: 'Lo que parecía no importante' -> richtige Formatierung according to spec."""
        text = "Lo que parecía no importante"
        result = await mock_translation_provider.translate_birkenbihl(text, "es", "de")

        # Expected from specification:
        # Lo   que  parecía  no     importante
        # Das  was  schien   nicht  wichtig
        lines = result.formatted_decoding.split("\n")
        assert len(lines) == 2

        # Verify "parecía" (longest word) gets proper space allocation
        orig_line = lines[0]
        assert "parecía" in orig_line
        assert "importante" in orig_line

        # Verify alignment - words should be consistently spaced
        orig_words = orig_line.split("  ")
        trans_words = lines[1].split("  ")

        # Should have same number of segments
        assert len(orig_words) == len(trans_words)

        # Find position of longest word to verify alignment
        parecia_pos = None
        for i, word in enumerate(orig_words):
            if "parecía" in word:
                parecia_pos = i
                break

        assert parecia_pos is not None
        # Corresponding translation position should have "schien"
        assert "schien" in trans_words[parecia_pos]

    @pytest.mark.asyncio
    async def test_specification_example_tenlo_por_seguro_alignment(self, mock_translation_provider):
        """Test: 'Tenlo por seguro' -> Alignment Test according to spec."""
        text = "Tenlo por seguro"
        result = await mock_translation_provider.translate_birkenbihl(text, "es", "de")

        # Expected from specification:
        # Tenlo   por  seguro
        # Hab-es  für  sicher
        lines = result.formatted_decoding.split("\n")

        # Verify compound word handling
        assert "Hab-es" in result.word_by_word_translation

        # Verify alignment structure
        orig_words = [w.strip() for w in lines[0].split("  ") if w.strip()]
        trans_words = [w.strip() for w in lines[1].split("  ") if w.strip()]

        assert len(orig_words) == 3  # Tenlo, por, seguro
        assert len(trans_words) == 3  # Hab-es, für, sicher

        # Verify specific mappings
        word_pairs = list(zip(orig_words, trans_words))
        mapping = dict(word_pairs)

        assert mapping.get("Tenlo") == "Hab-es"  # Compound word preserved
        assert mapping.get("por") == "für"
        assert mapping.get("seguro") == "sicher"

    @pytest.mark.asyncio
    async def test_specification_example_fueron_tantos_longer_sentences(self, mock_translation_provider):
        """Test: 'Fueron tantos bellos y malos momentos' -> längere Sätze handling."""
        text = "Fueron tantos bellos y malos momentos"
        result = await mock_translation_provider.translate_birkenbihl(text, "es", "de")

        # Expected from specification:
        # Fueron  tantos    bellos y    malos momentos
        # Waren   so-viele  schöne und  schlechte momente
        lines = result.formatted_decoding.split("\n")
        assert len(lines) == 2

        # Verify all 6 original words are present and spaced
        original_words = ["Fueron", "tantos", "bellos", "y", "malos", "momentos"]
        orig_line = lines[0]

        for word in original_words:
            assert word in orig_line, f"Missing word: {word}"

        # Verify all translation words are present
        expected_trans = ["Waren", "so-viele", "schöne", "und", "schlechte", "momente"]
        trans_line = lines[1]

        for word in expected_trans:
            # Case insensitive check since capitalization may vary
            assert any(word.lower() in w.lower() for w in trans_line.split()), f"Missing translation: {word}"

        # Verify compound word "so-viele" is preserved
        assert "so-viele" in result.word_by_word_translation

        # Verify longer sentence alignment
        orig_segments = [w for w in lines[0].split("  ") if w.strip()]
        trans_segments = [w for w in lines[1].split("  ") if w.strip()]

        # Should maintain word count alignment
        assert len(orig_segments) == len(trans_segments)

        # Sentence should be longer than single words - verify complexity handling
        assert len(orig_segments) >= 6  # At least 6 word positions
        assert len(" ".join(orig_segments).split()) >= 6  # At least 6 words total


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
