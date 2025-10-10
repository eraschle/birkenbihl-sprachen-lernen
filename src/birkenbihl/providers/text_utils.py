"""Text processing utilities for translation providers."""

import re

from birkenbihl.providers.models import SentenceResponse, WordAlignmentResponse


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using deterministic regex-based approach.

    Handles common sentence terminators (.!?) followed by whitespace.
    Preserves sentence terminators with each sentence.

    Args:
        text: Input text to split

    Returns:
        List of sentences with whitespace stripped

    Examples:
        >>> split_into_sentences("Hello world. How are you?")
        ['Hello world.', 'How are you?']

        >>> split_into_sentences("One sentence")
        ['One sentence']

        >>> split_into_sentences("First! Second? Third.")
        ['First!', 'Second?', 'Third.']
    """
    if not text or not text.strip():
        return []

    # Pattern: Split after .!? when followed by whitespace and capital letter
    # This avoids splitting on abbreviations like "Mr. Smith"
    pattern = r"(?<=[.!?])\s+(?=[A-Z])"

    # Split the text
    sentences = re.split(pattern, text)

    # Clean and filter
    result = [s.strip() for s in sentences if s.strip()]

    return result if result else [text.strip()]


def redistribute_merged_translation(
    merged: SentenceResponse, source_sentences: list[str]
) -> list[SentenceResponse]:
    """Redistribute merged translation into separate sentences.

    When AI merges multiple sentences into one response, this function splits it back
    into separate SentenceResponse objects by matching source_words to original sentences.

    Args:
        merged: Single SentenceResponse containing merged translation
        source_sentences: Original source sentences that should have been translated separately

    Returns:
        List of SentenceResponse objects, one per source sentence

    Example:
        >>> merged = SentenceResponse(
        ...     source_text="Hello world. How are you",
        ...     natural_translation="Hallo Welt. Wie geht es dir",
        ...     word_alignments=[
        ...         WordAlignmentResponse(source_word="Hello", target_word="Hallo", position=0),
        ...         WordAlignmentResponse(source_word="world", target_word="Welt", position=1),
        ...         WordAlignmentResponse(source_word="How", target_word="Wie", position=2),
        ...         WordAlignmentResponse(source_word="are", target_word="geht-es", position=3),
        ...         WordAlignmentResponse(source_word="you", target_word="dir", position=4)
        ...     ]
        ... )
        >>> source_sents = ["Hello world", "How are you"]
        >>> result = redistribute_merged_translation(merged, source_sents)
        >>> len(result)
        2
        >>> result[0].natural_translation
        'Hallo Welt.'
        >>> result[1].word_alignments[1].target_word
        'geht-es'
    """
    # Step 1: Split natural translation into sentences
    natural_sentences = split_into_sentences(merged.natural_translation)

    # Verify we got the expected number of sentences
    if len(natural_sentences) != len(source_sentences):
        raise ValueError(
            f"Natural translation split into {len(natural_sentences)} sentences "  # type: ignore[reportImplicitStringConcatenation]
            f"but expected {len(source_sentences)}. "
            f"Natural: {natural_sentences}, Expected count: {len(source_sentences)}"
        )

    # Step 2: Create alignment buckets for each source sentence
    alignments_per_sentence: list[list[WordAlignmentResponse]] = [[] for _ in source_sentences]

    # Step 3: Match each alignment to a source sentence via source_word
    for alignment in merged.word_alignments:
        source_word = alignment.source_word.strip().lower()
        matched = False

        for i, source_sent in enumerate(source_sentences):
            # Split source sentence into words and compare (case-insensitive)
            source_words = [w.strip().lower() for w in source_sent.split()]

            if source_word in source_words:
                alignments_per_sentence[i].append(alignment)
                matched = True
                break

        if not matched:
            raise ValueError(
                f"Could not match source_word '{alignment.source_word}' "  # type: ignore[reportImplicitStringConcatenation]
                f"to any source sentence: {source_sentences}"
            )

    # Step 4: Renumber positions for each sentence (start from 0)
    for sentence_alignments in alignments_per_sentence:
        for i, alignment in enumerate(sentence_alignments):
            alignment.position = i

    # Step 5: Build separate SentenceResponse objects
    result = []
    for i in range(len(source_sentences)):
        result.append(
            SentenceResponse(
                source_text=source_sentences[i],
                natural_translation=natural_sentences[i],
                word_alignments=alignments_per_sentence[i],
            )
        )

    return result
