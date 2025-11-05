"""Presenter for formatting translations for display."""

from birkenbihl.models.translation import Sentence, Translation, WordAlignment
from birkenbihl.presenters.display_models import (
    AlignmentDisplayModel,
    SentenceDisplayModel,
    TranslationDisplayModel,
)


class TranslationPresenter:
    """Formats Translation domain models for display.

    Follows Single Responsibility Principle - only concerned with
    presentation logic, not domain logic or UI rendering.
    """

    def format_translation(self, translation: Translation) -> TranslationDisplayModel:
        """Format Translation for display.

        Args:
            translation: Domain Translation model

        Returns:
            TranslationDisplayModel with formatted data
        """
        return TranslationDisplayModel(
            title=self._format_title(translation),
            short_id=str(translation.uuid)[:8],
            source_language=str(translation.source_language),
            target_language=str(translation.target_language),
            language_pair=self._format_language_pair(translation),
            sentences=self._format_sentences(translation.sentences),
        )

    def _format_title(self, translation: Translation) -> str:
        """Format translation title.

        Args:
            translation: Translation with title

        Returns:
            Formatted title with fallback
        """
        if translation.title:
            return translation.title
        return f"Translation {str(translation.uuid)[:8]}"

    def _format_language_pair(self, translation: Translation) -> str:
        """Format language pair display.

        Args:
            translation: Translation with languages

        Returns:
            Formatted language pair (e.g., "en → de")
        """
        return f"{translation.source_language} → {translation.target_language}"

    def _format_sentences(self, sentences: list[Sentence]) -> list[SentenceDisplayModel]:
        """Format list of sentences.

        Args:
            sentences: List of Sentence domain models

        Returns:
            List of formatted SentenceDisplayModel
        """
        return [self._format_sentence(idx + 1, sent) for idx, sent in enumerate(sentences)]

    def _format_sentence(self, index: int, sentence: Sentence) -> SentenceDisplayModel:
        """Format single sentence.

        Args:
            index: Sentence number (1-indexed)
            sentence: Sentence domain model

        Returns:
            SentenceDisplayModel with formatted data
        """
        return SentenceDisplayModel(
            index=index,
            source_text=sentence.source_text,
            natural_translation=sentence.natural_translation,
            word_by_word=sentence.get_word_by_word(),
            alignments=self._format_alignments(sentence.word_alignments),
        )

    def _format_alignments(self, alignments: list[WordAlignment]) -> list[AlignmentDisplayModel]:
        """Format word alignments.

        Args:
            alignments: List of WordAlignment domain models

        Returns:
            List of AlignmentDisplayModel
        """
        return [
            AlignmentDisplayModel(
                source_word=align.source_word, target_word=align.target_word, position=align.position
            )
            for align in alignments
        ]
