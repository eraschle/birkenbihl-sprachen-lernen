"""Shared prompts for Birkenbihl translation method.

These prompts are used by all translation providers to ensure consistent
behavior across OpenAI, Anthropic, and other models.
"""

from birkenbihl.models.languages import Language

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


def create_translation_prompt(
    sentences: list[str], source_lang: Language, target_lang: Language, count: int | None = None
) -> str:
    """Create user prompt for translation request.

    Args:
        sentences: List of sentences to translate
        source_lang: Source language code (en, es, etc.)
        target_lang: Target language code (de, etc.)

    Returns:
        Formatted prompt for the AI model
    """
    src_name = source_lang.name_en
    trg_name = target_lang.name_en

    alternative_prompt = "."
    if count and count > 1:
        alternative_prompt = f" and {count} alternative translations."

    # Format sentences as numbered list
    if len(sentences) == 1:
        sentences_text = sentences[0]
    else:
        sentences_text = "\n".join(f"{i + 1}. {sent}" for i, sent in enumerate(sentences))

    return f"""Translate the following sentence(s) from {src_name} to {trg_name} using the Birkenbihl method.

Provide for EACH sentence separately:
1. A natural and fluent translation in {trg_name}{alternative_prompt}
2. Maintain the original meaning
3. Vary in formality, word choice, or structure
4. You must translate ALL {len(sentences)} sentences.

Source sentence(s):
{sentences_text}

Your response must contain exactly {len(sentences)} sentence translations - one for each source sentence.
"""


def create_word_by_word_prompt(
    source_words: list[str], target_words: list[str], source_lang: Language, target_lang: Language
) -> str:
    """Create prompt for generating word-by-word translations.

    Args:
        source_words: List of words from the source sentence
        target_words: List of words from the natural translation
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Formatted prompt for generating word-by-word translations
    """
    source_name = source_lang.name_en
    target_name = target_lang.name_en

    # Format word lists with indices for clarity
    source_list = ", ".join(f'"{word}"' for word in source_words)
    target_list = ", ".join(f'"{word}"' for word in target_words)

    return f"""Create a word-by-word alignment for the Birkenbihl method.

**Given:**
- Source words ({source_name}): '{source_list}'
- Target words from natural translation ({target_name}): '{target_list}'

**Your task:**
Map each source word to one or more target words, creating a word-by-word alignment.

**How the alignment works:**
1. **Position**: Sequential index (0, 1, 2, ...) following source word order
2. **Source word**: One word from the source sentence
3. **Target word**: Translation from the natural translation
   - Use single target word when possible: "yesterday" → "gestern"
   - Use hyphenated compound when multiple target words form one concept: "I've" → "Ich-habe"
   - **IMPORTANT**: Every target word MUST be used exactly once in alignments

**Critical rules:**
✓ Every source word MUST have at least one target word (no empty mappings)
✓ Every target word MUST appear in exactly one alignment
✓ Negations stay separate: "no importante" → "nicht" + "wichtig" (NOT "unwichtig")
✓ Use hyphens only when target words form inseparable unit: "It's" → "Es-ist"
✓ Position numbers must be sequential: 0, 1, 2, 3, ...

**Example 1 (Simple 1:1 mapping):**
Source: ["Yesterday", "I", "met", "new", "people"]
Target: ["Gestern", "ich", "traf", "neue", "Leute"]

Alignments:
- Position 0: "Yesterday" → "Gestern"
- Position 1: "I" → "ich"
- Position 2: "met" → "traf"
- Position 3: "new" → "neue"
- Position 4: "people" → "Leute"

**Example 2 (Complex: word order changes + compounds + split words):**
Source (Spanish): ["Yo", "te", "extrañaré", "mucho"]
Target (German): ["Ich", "werde", "dich", "sehr", "vermissen"]

Alignments:
- Position 0: "Yo" → "Ich"
- Position 1: "te" → "dich" (moved from position 2 in target to align with source position)
- Position 2: "extrañaré" → "werde-vermissen" (future tense split across positions 1+4 in target)
- Position 3: "mucho" → "sehr"

**Example 3 (Negation + reflexive verb):**
Source (Spanish): ["No", "es", "importante", "verte", "aquí"]
Target (German): ["Es", "ist", "nicht", "wichtig", "dich", "hier", "zu", "sehen"]

Alignments:
- Position 0: "No" → "nicht" (negation moved to position 2 in target)
- Position 1: "es" → "Es-ist" (compound: positions 0+1 in target)
- Position 2: "importante" → "wichtig"
- Position 3: "verte" → "dich-zu-sehen" (reflexive verb split: positions 4+6+7 in target)
- Position 4: "aquí" → "hier"

Note: In complex examples, target words may appear in different order than in natural translation.
The alignment follows SOURCE order, but uses target words from wherever they appear.

Generate the word-by-word alignment following these rules."""


def create_alternatives_prompt(source_text: str, source_lang: Language, target_lang: Language, count: int) -> str:
    """Create prompt for generating alternative translations.

    Args:
        source_text: Original text to translate
        source_lang: Source language
        target_lang: Target language
        count: Number of alternatives to generate

    Returns:
        Formatted prompt for generating alternatives
    """
    source_name = source_lang.name_en
    target_name = target_lang.name_en

    return f"""Generate {count} alternative natural translations for the following text.

Source text ({source_name}):
{source_text}

Provide {count} different translations in {target_name} that:
1. Maintain the original meaning
2. Vary in formality, word choice, or structure
3. Are all fluent and natural-sounding

Return only the alternative translations."""


def create_regenerate_alignment_prompt(
    source_text: str, natural_translation: str, source_lang: Language, target_lang: Language
) -> str:
    """Create prompt for regenerating word-by-word alignment.

    Args:
        source_text: Original source sentence
        natural_translation: Natural translation chosen by user
        source_lang: Source language
        target_lang: Target language

    Returns:
        Formatted prompt for alignment generation
    """
    source_name = source_lang.name_en
    target_name = target_lang.name_en

    # Extract words from natural translation to show them explicitly
    target_words = natural_translation.split()
    target_words_list = ", ".join(f'"{word}"' for word in target_words)

    return f"""Create a word-by-word alignment for the Birkenbihl method.

**Source sentence ({source_name}):**
{source_text}

**Natural translation ({target_name}):**
{natural_translation}

**Target words available (from natural translation):**
{target_words_list}

**Critical rules:**
1. **EVERY target word MUST be used EXACTLY ONCE** in the alignments
2. **Use target words AS THEY APPEAR** in the natural translation (if "werde" and "vermissen" are separate words, keep them separate!)
3. Map each source word to one or more target words
4. Use hyphens to connect target words ONLY when mapping multiple target words to ONE source word (e.g., "I've" → "Ich-habe")
5. **DO NOT create compound words** if the target words appear separately in the natural translation
6. Follow source word order with sequential position numbers (0-indexed)

**Example 1 (Correct - separate words):**
Source: "Yo te extrañaré"
Natural: "Ich werde dich vermissen"
Target words: "Ich", "werde", "dich", "vermissen"

✓ CORRECT Alignments:
- Position 0: "Yo" → "Ich"
- Position 1: "te" → "dich"
- Position 2: "extrañaré" → "werde-vermissen"  (combines "werde" + "vermissen" for one source word)

✗ WRONG: Do not create "werde vermissen" or omit words!

**Example 2 (Simple 1:1):**
Source: "Ich mag Hunde"
Natural: "I like dogs"
Target words: "I", "like", "dogs"

Alignments:
- Position 0: "Ich" → "I"
- Position 1: "mag" → "like"
- Position 2: "Hunde" → "dogs"

Generate the word-by-word alignment following these rules. Ensure ALL target words are used exactly once."""
