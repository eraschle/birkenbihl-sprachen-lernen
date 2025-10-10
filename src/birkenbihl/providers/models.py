"""AI response models for translation providers.

These models represent the structured output from AI models, without UUIDs
or timestamps. They are converted to domain models (Translation, Sentence)
by the translation providers.
"""

from pydantic import BaseModel, Field


class WordAlignmentResponse(BaseModel):
    """Word-by-word alignment from AI response.

    Unlike the domain WordAlignment model, this doesn't enforce position
    as the AI will generate them sequentially.
    """

    source_word: str = Field(description="Original word from source language")
    target_word: str = Field(description="Translated word in target language")
    position: int = Field(description="Sequential position in sentence (0-indexed)")


class SentenceResponse(BaseModel):
    """Single sentence translation from AI response.

    Contains both natural and word-by-word translations as required
    by the Birkenbihl method. No UUID or timestamp - these are added
    when converting to domain Sentence model.
    """

    source_text: str = Field(description="Original sentence in source language")
    natural_translation: str = Field(description="Natural, fluent translation in target language")
    word_alignments: list[WordAlignmentResponse] = Field(
        description="Word-by-word alignment for Birkenbihl decoding method"
    )


class TranslationResponse(BaseModel):
    """Complete translation response from AI.

    Root model for AI structured output. Contains one or more sentences
    with both translation types (natural + word-by-word).

    This is converted to the domain Translation model by providers.
    """

    sentences: list[SentenceResponse] = Field(
        description="List of translated sentences with natural and word-by-word translations",
        min_length=1,
    )
