"""Tests for TranslationPresenter."""

from datetime import datetime
from uuid import uuid4

import pytest

from birkenbihl.models import dateutils
from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.presenters.models import SentencePresentation, TranslationPresentation
from birkenbihl.presenters.translation_presenter import TranslationPresenter
from birkenbihl.services import language_service as ls


@pytest.fixture
def sample_translation() -> Translation:
    """Create sample translation for testing."""
    sentence_uuid = uuid4()
    translation_uuid = uuid4()

    sentence = Sentence(
        uuid=sentence_uuid,
        source_text="Yo te extrañaré",
        natural_translation="Ich werde dich vermissen",
        word_alignments=[
            WordAlignment(source_word="Yo", target_word="Ich", position=0),
            WordAlignment(source_word="te", target_word="dich", position=1),
            WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),
        ],
        created_at=dateutils.create_now(),
    )

    return Translation(
        uuid=translation_uuid,
        title="Test Translation",
        source_language=ls.get_language_by("es"),
        target_language=ls.get_language_by("de"),
        sentences=[sentence],
        created_at=datetime(2025, 10, 16, 12, 0, 0),
        updated_at=datetime(2025, 10, 16, 14, 30, 0),
    )


@pytest.fixture
def presenter() -> TranslationPresenter:
    """Create TranslationPresenter instance."""
    return TranslationPresenter()


@pytest.mark.unit
class TestTranslationPresenterBasic:
    """Tests for basic presentation functionality."""

    def test_present_returns_presentation_model(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that present() returns TranslationPresentation."""
        result = presenter.present(sample_translation)

        assert isinstance(result, TranslationPresentation)
        assert result.uuid == sample_translation.uuid

    def test_present_formats_title(self, presenter: TranslationPresenter, sample_translation: Translation) -> None:
        """Test that present() uses the translation title."""
        result = presenter.present(sample_translation)

        assert result.title == "Test Translation"

    def test_present_formats_title_with_fallback(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that present() provides fallback for empty title."""
        sample_translation.title = ""
        result = presenter.present(sample_translation)

        assert result.title.startswith("Translation ")
        assert str(sample_translation.uuid)[:8] in result.title

    def test_present_includes_language_names(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that present() includes language display names."""
        result = presenter.present(sample_translation)

        assert result.source_language_name == sample_translation.source_language.name_de
        assert result.target_language_name == sample_translation.target_language.name_de

    def test_present_includes_sentence_count(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that present() includes correct sentence count."""
        result = presenter.present(sample_translation)

        assert result.sentence_count == 1


@pytest.mark.unit
class TestTranslationPresenterDates:
    """Tests for datetime formatting."""

    def test_present_formats_created_at(self, presenter: TranslationPresenter, sample_translation: Translation) -> None:
        """Test that present() formats created_at timestamp."""
        result = presenter.present(sample_translation)

        assert result.created_at == "2025-10-16 12:00"

    def test_present_formats_updated_at(self, presenter: TranslationPresenter, sample_translation: Translation) -> None:
        """Test that present() formats updated_at timestamp."""
        result = presenter.present(sample_translation)

        assert result.updated_at == "2025-10-16 14:30"


@pytest.mark.unit
class TestTranslationPresenterSentences:
    """Tests for sentence presentation."""

    def test_present_includes_sentences(self, presenter: TranslationPresenter, sample_translation: Translation) -> None:
        """Test that present() includes sentence presentations."""
        result = presenter.present(sample_translation)

        assert len(result.sentences) == 1
        assert isinstance(result.sentences[0], SentencePresentation)

    def test_sentence_presentation_has_correct_index(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that sentences have 1-based display indices."""
        result = presenter.present(sample_translation)

        assert result.sentences[0].index == 1

    def test_sentence_presentation_includes_texts(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that sentence presentation includes source and natural texts."""
        result = presenter.present(sample_translation)
        sentence = result.sentences[0]

        assert sentence.source_text == "Yo te extrañaré"
        assert sentence.natural_translation == "Ich werde dich vermissen"

    def test_sentence_presentation_includes_alignments(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that sentence presentation includes word alignments."""
        result = presenter.present(sample_translation)
        sentence = result.sentences[0]

        assert sentence.has_alignments is True
        assert sentence.alignment_count == 3
        assert sentence.alignments == [
            ("Yo", "Ich"),
            ("te", "dich"),
            ("extrañaré", "werde-vermissen"),
        ]

    def test_sentence_without_alignments(self, presenter: TranslationPresenter) -> None:
        """Test sentence presentation with no alignments."""
        translation = Translation(
            uuid=uuid4(),
            title="No Alignments",
            source_language=ls.get_language_by("en"),
            target_language=ls.get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="Test",
                    natural_translation="Test",
                    word_alignments=[],
                    created_at=dateutils.create_now(),
                )
            ],
            created_at=dateutils.create_now(),
            updated_at=dateutils.create_now(),
        )

        result = presenter.present(translation)
        sentence = result.sentences[0]

        assert sentence.has_alignments is False
        assert sentence.alignment_count == 0
        assert sentence.alignments == []


@pytest.mark.unit
class TestTranslationPresenterMultipleSentences:
    """Tests for translations with multiple sentences."""

    def test_present_multiple_sentences(self, presenter: TranslationPresenter) -> None:
        """Test presentation of translation with multiple sentences."""
        translation = Translation(
            uuid=uuid4(),
            title="Multi-Sentence",
            source_language=ls.get_language_by("en"),
            target_language=ls.get_language_by("de"),
            sentences=[
                Sentence(
                    uuid=uuid4(),
                    source_text="First",
                    natural_translation="Erste",
                    word_alignments=[],
                    created_at=dateutils.create_now(),
                ),
                Sentence(
                    uuid=uuid4(),
                    source_text="Second",
                    natural_translation="Zweite",
                    word_alignments=[],
                    created_at=dateutils.create_now(),
                ),
                Sentence(
                    uuid=uuid4(),
                    source_text="Third",
                    natural_translation="Dritte",
                    word_alignments=[],
                    created_at=dateutils.create_now(),
                ),
            ],
            created_at=dateutils.create_now(),
            updated_at=dateutils.create_now(),
        )

        result = presenter.present(translation)

        assert result.sentence_count == 3
        assert len(result.sentences) == 3
        assert result.sentences[0].index == 1
        assert result.sentences[1].index == 2
        assert result.sentences[2].index == 3


@pytest.mark.unit
class TestPresentationModelImmutability:
    """Tests for immutability of presentation models."""

    def test_translation_presentation_is_frozen(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that TranslationPresentation is immutable."""
        result = presenter.present(sample_translation)

        with pytest.raises(Exception, match="cannot assign to field"):
            result.title = "Modified"  # type: ignore

    def test_sentence_presentation_is_frozen(
        self, presenter: TranslationPresenter, sample_translation: Translation
    ) -> None:
        """Test that SentencePresentation is immutable."""
        result = presenter.present(sample_translation)
        sentence = result.sentences[0]

        with pytest.raises(Exception, match="cannot assign to field"):
            sentence.source_text = "Modified"  # type: ignore
