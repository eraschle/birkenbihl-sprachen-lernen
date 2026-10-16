"""AI response models for translation providers.

These models represent the structured output from AI models, without UUIDs
or timestamps. They are converted to domain models (Translation, Sentence)
by the translation providers.
"""

from pydantic import BaseModel, Field


class NaturalSentenceResponse(BaseModel):
    """Natural translation only (Step 1 of two-step process).

    Contains only source text and natural translation, without word alignments.
    Word alignments are generated in Step 2.
    """

    source_text: str = Field(description="Original sentence in source language")
    natural_translation: str = Field(description="Natural, fluent translation in target language")


class NaturalTranslationResponse(BaseModel):
    """Natural translation response (Step 1 of two-step process).

    Root model for Step 1 AI structured output. Contains one or more sentences
    with natural translations only. Word alignments are generated separately in Step 2.
    """

    sentences: list[NaturalSentenceResponse] = Field(
        description="List of sentences with natural translations only",
        min_length=1,
    )


class WordAlignmentResponse(BaseModel):
    """Word-by-word alignment from AI response.

    Unlike the domain WordAlignment model, this doesn't enforce position
    as the AI will generate them sequentially.
    """

    source_word: str = Field(description="Original word from source language")
    target_word: str = Field(description="Translated word in target language")
    position: int = Field(description="Sequential position in sentence (0-indexed)")


class AlignmentResponse(BaseModel):
    """Word-by-word alignment response from AI.

    Contains only word alignments for a single sentence, used when
    regenerating alignment based on a user-chosen natural translation.
    """

    word_alignments: list[WordAlignmentResponse] = Field(
        description="Word-by-word alignment for Birkenbihl decoding method",
        min_length=1,
    )
