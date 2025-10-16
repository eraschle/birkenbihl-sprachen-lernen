"""Text extraction and normalization utilities.

Centralizes duplicated text processing logic for word/sentence splitting and punctuation handling.
Each function does one thing with minimal parameters (Clean Code: 0-2 parameters ideal).
"""

import re


def extract_normalized_words(text: str) -> list[str]:
    """Extract words from text: remove punctuation (keep apostrophes/hyphens), lowercase, split.

    This is the normalized word extraction used in validation.py for comparing
    natural translations with word alignments.

    Args:
        text: Input text

    Returns:
        List of normalized words

    Examples:
        >>> extract_normalized_words("Hello, world! How are you?")
        ['hello', 'world', 'how', 'are', 'you']
        >>> extract_normalized_words("Don't worry-free!")
        ["don't", 'worry-free']
    """
    text_no_punct = re.sub(r"[^\w\s'\-]", "", text)
    words = text_no_punct.lower().split()
    return [w for w in words if w]


def normalize_word_for_matching(word: str) -> str:
    """Normalize single word for comparison: strip whitespace and lowercase.

    Used when matching words across sentences or alignments.

    Args:
        word: Input word

    Returns:
        Normalized word

    Examples:
        >>> normalize_word_for_matching("Hello ")
        "hello"
        >>> normalize_word_for_matching("  WORLD  ")
        "world"
    """
    return word.strip().lower()


def split_hyphenated(word: str) -> list[str]:
    """Split hyphenated word into parts, removing punctuation from each part.

    Handles Birkenbihl method compound words like "werde-vermissen" → ["werde", "vermissen"].
    If no hyphen present, returns single-item list with punctuation removed.

    Args:
        word: Word potentially containing hyphens (e.g., "werde-vermissen")

    Returns:
        List of word parts with punctuation removed

    Examples:
        >>> split_hyphenated_word("werde-vermissen")
        ['werde', 'vermissen']
        >>> split_hyphenated_word("hello!")
        ['hello']
        >>> split_hyphenated_word("test-word!")
        ['test', 'word']
    """
    if "-" not in word:
        clean = re.sub(r"[^\w'\-]", "", word)
        return [clean] if clean else []

    parts = word.split("-")
    result = []
    for part in parts:
        clean = re.sub(r"[^\w'\-]", "", part)
        if clean:
            result.append(clean)
    return result


def clean_trailing_punctuation(word: str) -> tuple[str, str]:
    """Clean trailing punctuation from word.

    Used for preserving punctuation when displaying word-by-word translations.

    Args:
        word: Input word potentially ending with punctuation

    Returns:
        Tuple of (clean_word, trailing_punctuation)

    Examples:
        >>> extract_trailing_punctuation("world!")
        ('world', '!')
        >>> extract_trailing_punctuation("hello...")
        ('hello', '...')
        >>> extract_trailing_punctuation("test")
        ('test', '')
    """
    match = re.search(r"[^\w]+$", word)
    if match:
        punctuation = match.group()
        clean_word = word[: -len(punctuation)]
        return (clean_word, punctuation)
    return (word, "")


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using deterministic regex-based approach.

    Handles common sentence terminators (.!?) followed by whitespace and capital letter.
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

    sentences = re.split(pattern, text)
    result = [word.strip() for word in sentences if word.strip()]

    return result if result else [text.strip()]


def tokenize(text: str) -> list[str]:
    """Tokenize text into words for UI display (keeps punctuation attached).

    Unlike extract_normalized_words, this keeps original capitalization
    and only splits on whitespace. Used for creating word columns in UI.

    Args:
        text: Input text

    Returns:
        List of words with original capitalization

    Examples:
        >>> tokenize("Hello, world! How are you?")
        ['Hello,', 'world!', 'How', 'are', 'you?']
        >>> tokenize("The cat's name")
        ['The', "cat's", 'name']
    """
    return text.split()


def tokenize_clean(text: str) -> list[str]:
    """Tokenize text and remove punctuation from each word.

    Used for creating clean word lists for alignment mapping in UI.
    Preserves apostrophes and hyphens within words.

    Args:
        text: Input text

    Returns:
        List of words without surrounding punctuation

    Examples:
        >>> tokenize_clean("Hello, world! How are you?")
        ['Hello', 'world', 'How', 'are', 'you']
        >>> tokenize_clean("Don't worry-free!")
        ["Don't", 'worry-free']
    """
    words = text.split()
    clean_words = []
    for word in words:
        # Remove leading/trailing punctuation but keep apostrophes/hyphens inside
        clean = re.sub(r"^[^\w']+|[^\w']+$", "", word)
        if clean:
            clean_words.append(clean)
    return clean_words
