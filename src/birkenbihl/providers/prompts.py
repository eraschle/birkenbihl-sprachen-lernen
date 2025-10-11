"""Shared prompts for Birkenbihl translation method.

These prompts are used by all translation providers to ensure consistent
behavior across OpenAI, Anthropic, and other models.
"""

from birkenbihl.models.languages import get_english_name

BIRKENBIHL_SYSTEM_PROMPT = """You are a language translation expert specializing in the Vera F. Birkenbihl \
language learning method.

Your task is to provide TWO types of translations:

1. **Natural Translation (Natürliche Übersetzung)**:
   - Fluent, idiomatic translation that sounds natural in the target language
   - Maintains the meaning and tone of the original text
   - Uses proper grammar and sentence structure
   - **IMPORTANT**: Prefer separate words over compound words to maintain 1:1 word mapping where possible

2. **Word-by-Word Translation (Wort-für-Wort Dekodierung)**:
   - Each word from the source text is aligned with its translation
   - Shows the structure of the source language
   - Helps learners understand how the source language constructs meaning
   - Uses hyphens to connect words that translate to a single concept (e.g., "vermissen-werde")
   - Position indicates the sequential order for proper alignment in the UI

**Critical Requirements:**
- Every word from the natural translation MUST appear in the word-by-word alignments
- Every source word MUST have at least one non-empty target word
- Word alignments should follow the source language word order
- For compound translations (multiple source words → single target word), use hyphens
- Maintain consistent position numbering starting from 0

**Special Rules for Word-by-Word Alignment:**
- Negations MUST be separate words to maintain 1:1 mapping:
  ✓ CORRECT: "no importante" → "nicht wichtig" (2→2 words)
  ✗ WRONG: "no importante" → "unwichtig" (2→1 words)
- Compound words should be avoided where linguistically acceptable:
  ✓ CORRECT: "no es" → "ist nicht"
  ✗ WRONG: "no es" → "ist-nicht" (only if grammatically required)
- Every source word must map to at least one target word (no empty mappings)

**Example 1 (English to German - Simple sentence):**
Source: "Yesterday I met some new people."
Natural: "Gestern ich traf einige neue Leute."
Word-by-word:
  - "Yesterday" → "Gestern" (position 0)
  - "I" → "ich" (position 1)
  - "met" → "traf" (position 2)
  - "some" → "einige" (position 3)
  - "new" → "neue" (position 4)
  - "people" → "Leute" (position 5)

**Example 2 (Contractions - use hyphens):**
Source: "It's a Greek name."
Natural: "Es ist ein griechischer Name."
Word-by-word:
  - "It's" → "Es-ist" (position 0)
  - "a" → "ein" (position 1)
  - "Greek" → "griechischer" (position 2)
  - "name" → "Name" (position 3)

**Example 3 (Compound words - keep separate where possible):**
Source: "I've met Greek people"
Natural: "Ich habe getroffen griechische Leute" (NOT "Ich habe-getroffen...")
Word-by-word:
  - "I've" → "Ich-habe" (position 0)
  - "met" → "getroffen" (position 1)
  - "Greek" → "griechische" (position 2)
  - "people" → "Leute" (position 3)

**Example 4 (Negations - MUST be separate words):**
Source (ES): "no importante"
Natural: "nicht wichtig" (NOT "unwichtig" - compound word loses mapping!)
Word-by-word:
  - "no" → "nicht" (position 0)
  - "importante" → "wichtig" (position 1)

**Example 5 (Reflexive verbs - avoid compound infinitives):**
Source (ES): "para verte de nuevo"
Natural: "um dich wieder zu sehen" (NOT "um dich wiederzusehen" - compound verb!)
Word-by-word:
  - "para" → "um" (position 0)
  - "verte" → "dich" (position 1)
  - "de" → "wieder" (position 2)
  - "nuevo" → "zu-sehen" (position 3)

**Example 6 (Multi-word phrases):**
Source: "girl friend"
Natural: "Mädchen Freund" (keep as two words, NOT "Mädchenfreund")
Word-by-word:
  - "girl" → "Mädchen" (position 0)
  - "friend" → "Freund" (position 1)

Provide accurate, pedagogically useful translations that help language learners understand sentence structure.
"""


def create_translation_prompt(sentences: list[str], source_lang: str, target_lang: str) -> str:
    """Create user prompt for translation request.

    Args:
        sentences: List of sentences to translate
        source_lang: Source language code (en, es, etc.)
        target_lang: Target language code (de, etc.)

    Returns:
        Formatted prompt for the AI model
    """
    source_name = get_english_name(source_lang)
    target_name = get_english_name(target_lang)

    # Format sentences as numbered list
    if len(sentences) == 1:
        sentences_text = sentences[0]
    else:
        sentences_text = "\n".join(f"{i + 1}. {sent}" for i, sent in enumerate(sentences))

    if len(sentences) == 1:
        return f"""Translate the following sentence from {source_name} to {target_name} using the Birkenbihl method.

Source sentence:
{sentences_text}

Provide:
1. Natural translation in {target_name}
2. Word-by-word alignment showing how each source word maps to the target language
"""
    else:
        return f"""Translate ALL {len(sentences)} sentences from {source_name} to {target_name} using the \
Birkenbihl method.

Source sentences:
{sentences_text}

CRITICAL: You must translate ALL {len(sentences)} sentences listed above.
Provide for EACH sentence separately:
1. Natural translation in {target_name}
2. Word-by-word alignment showing how each source word maps to the target language

Your response must contain exactly {len(sentences)} sentence translations - one for each source sentence.
"""


def create_alternatives_prompt(source_text: str, source_lang: str, target_lang: str, count: int) -> str:
    """Create prompt for generating alternative natural translations.

    Args:
        source_text: Source sentence to translate
        source_lang: Source language code
        target_lang: Target language code
        count: Number of alternatives to generate

    Returns:
        Formatted prompt for generating alternatives
    """
    source_name = get_english_name(source_lang)
    target_name = get_english_name(target_lang)

    return f"""Generate {count} different natural translations for the following {source_name} sentence \
into {target_name}.

Source sentence:
{source_text}

Provide {count} alternative translations that:
1. Are all natural and fluent in {target_name}
2. Maintain the original meaning
3. Vary in formality, word choice, or structure
4. Are all equally valid translations

Return only the list of alternatives, no explanations needed."""


def create_regenerate_alignment_prompt(
    source_text: str, natural_translation: str, source_lang: str, target_lang: str
) -> str:
    """Create prompt for regenerating word-by-word alignment.

    Args:
        source_text: Original source sentence
        natural_translation: Natural translation chosen by user
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Formatted prompt for alignment generation
    """
    source_name = get_english_name(source_lang)
    target_name = get_english_name(target_lang)

    return f"""Create a word-by-word alignment for the Birkenbihl method based on the given natural translation.

Source sentence ({source_name}):
{source_text}

Natural translation ({target_name}):
{natural_translation}

Create word alignments that:
1. Map each source word to its translation in the natural translation
2. Use hyphens for compound translations (e.g., "vermissen-werde")
3. Ensure EVERY word from the natural translation appears in the alignments
4. Follow the source language word order with sequential position numbers (0-indexed)

Provide only the word-by-word alignment, following the Birkenbihl decoding method."""
