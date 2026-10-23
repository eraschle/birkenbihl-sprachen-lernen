"""Domain models for translation data."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from birkenbihl.models import dateutils
from birkenbihl.models.languages import Language
from birkenbihl.utils.text_extractor import tokenize_clean

TARGET_JOINER = "-"
SOURCE_JOINER = "-"


class AlignmentStatus(StrEnum):
    """How far a word alignment can be trusted."""

    SUGGESTED = "suggested"  # proposed by AI, no problems detected
    FLAGGED = "flagged"  # needs human review (e.g. AI output could not be matched to the sentence)
    CONFIRMED = "confirmed"  # set by the user in the editor


class WordAlignment(BaseModel):
    """One column of the word-by-word translation (Birkenbihl decoding).

    A column links one or more source words with one or more target words: "extrañaré" → "vermissen-werde",
    and also several source words sharing one target word: "estación de tren" → "Bahnhof". Words are
    referenced by their position in the tokenized sentences, not by text, so repeated words ("der Hund und
    der Mann") stay unambiguous. Tokenization: Sentence.source_tokens and Sentence.target_tokens.
    """

    source_indices: list[int]  # in sentence order, shown joined with "-" (e.g. "estación-de-tren")
    target_indices: list[int]  # in display order, joined with "-" (e.g. "vermissen-werde")
    status: AlignmentStatus = AlignmentStatus.SUGGESTED


class Sentence(BaseModel):
    """A single sentence with natural and word-by-word translation.

    Contains both translation types required by the Birkenbihl method:
    1. Natural translation (natürliche Übersetzung)
    2. Word-by-word alignment (Wort-für-Wort Dekodierung): WordAlignment columns that together contain every
       source token and every target token exactly once
    """

    uuid: UUID = Field(default_factory=uuid4)
    source_text: str
    natural_translation: str
    word_alignments: list[WordAlignment]

    created_at: datetime = Field(default_factory=dateutils.create_now)

    @property
    def source_tokens(self) -> list[str]:
        """Source words that alignments refer to by index.

        Derived from the text, so the tokenizer is part of the stored data format.
        """
        return tokenize_clean(self.source_text)

    @property
    def target_tokens(self) -> list[str]:
        """Words of the natural translation that alignments refer to by index."""
        return tokenize_clean(self.natural_translation)

    def source_word(self, alignment: WordAlignment) -> str:
        """Source words of one column, e.g. "estación-de-tren"."""
        tokens = self.source_tokens
        return SOURCE_JOINER.join(tokens[index] for index in alignment.source_indices)

    def target_text(self, alignment: WordAlignment) -> str:
        """Target words of one alignment as shown to the learner, e.g. "vermissen-werde"."""
        tokens = self.target_tokens
        return TARGET_JOINER.join(tokens[index] for index in alignment.target_indices)

    def sorted_alignments(self) -> list[WordAlignment]:
        return sorted(self.word_alignments, key=lambda alignment: min(alignment.source_indices, default=-1))

    def unassigned_target_indices(self) -> list[int]:
        used = {index for alignment in self.word_alignments for index in alignment.target_indices}
        return [index for index in range(len(self.target_tokens)) if index not in used]

    def unassigned_source_indices(self) -> list[int]:
        used = {index for alignment in self.word_alignments for index in alignment.source_indices}
        return [index for index in range(len(self.source_tokens)) if index not in used]

    def needs_review(self) -> bool:
        flagged = any(alignment.status == AlignmentStatus.FLAGGED for alignment in self.word_alignments)
        return flagged or bool(self.unassigned_target_indices()) or bool(self.unassigned_source_indices())

    def get_word_by_word(self) -> str:
        """Word-by-word translation in source word order.

        Example:
            >>> sentence.get_word_by_word()
            'Ich dich vermissen-werde'
        """
        texts = (self.target_text(alignment) for alignment in self.sorted_alignments())
        return " ".join(text for text in texts if text)


class Translation(BaseModel):
    """Complete translation document with metadata.

    Root aggregate representing a translation session. Can contain multiple
    sentences, each with natural and word-by-word translations.

    Uses UUIDs for cross-storage compatibility (JSON, DB, Excel, etc.).
    """

    uuid: UUID = Field(default_factory=uuid4)
    title: str  # Document name for organization
    source_language: Language
    target_language: Language
    sentences: list[Sentence]

    created_at: datetime = Field(default_factory=dateutils.create_now)
    updated_at: datetime = Field(default_factory=dateutils.create_now)

    def updated_str(self, format_str: str = "%d.%m.%Y %H:%M") -> str:
        return self.updated_at.strftime(format=format_str)

    def created_str(self, format_str: str = "%d.%m.%Y %H:%M") -> str:
        return self.created_at.strftime(format=format_str)
