"""TranslationPresenter for converting domain models to presentation models."""

from datetime import datetime

from birkenbihl.models.translation import Sentence, Translation
from birkenbihl.presenters.models import SentencePresentation, TranslationPresentation


class TranslationPresenter:
    """Prepares Translation data for display (CLI/GUI agnostic).

    Converts domain models to presentation models with:
    - Computed fields (title with fallback, formatted dates)
    - Display indices (1-based for user display)
    - Structured data ready for rendering
    """

    def present(self, translation: Translation) -> TranslationPresentation:
        """Convert Translation to presentation model.

        Args:
            translation: Domain translation object

        Returns:
            Immutable presentation model with display-ready data
        """
        return TranslationPresentation(
            uuid=translation.uuid,
            title=self._format_title(translation),
            source_language_name=translation.source_language.name_de,
            target_language_name=translation.target_language.name_de,
            sentence_count=len(translation.sentences),
            created_at=self._format_datetime(translation.created_at),
            updated_at=self._format_datetime(translation.updated_at),
            sentences=[self._present_sentence(sentence, idx) for idx, sentence in enumerate(translation.sentences, 1)],
        )

    def _format_title(self, translation: Translation) -> str:
        """Format title with fallback for empty titles.

        Args:
            translation: Translation object

        Returns:
            Title or fallback string with short UUID
        """
        return translation.title or f"Translation {str(translation.uuid)[:8]}"

    def _format_datetime(self, date_time: datetime) -> str:
        """Format datetime for display.

        Args:
            date_time: Datetime to format

        Returns:
            Formatted string (YYYY-MM-DD HH:MM)
        """
        return date_time.strftime("%Y-%m-%d %H:%M")

    def _present_sentence(self, sentence: Sentence, index: int) -> SentencePresentation:
        """Convert Sentence to presentation model.

        Args:
            sentence: Domain sentence object
            index: Display index (1-based)

        Returns:
            Immutable sentence presentation
        """
        alignments = [(wa.source_word, wa.target_word) for wa in sentence.word_alignments]

        return SentencePresentation(
            uuid=sentence.uuid,
            index=index,
            source_text=sentence.source_text,
            natural_translation=sentence.natural_translation,
            alignment_count=len(alignments),
            has_alignments=bool(alignments),
            alignments=alignments,
        )
