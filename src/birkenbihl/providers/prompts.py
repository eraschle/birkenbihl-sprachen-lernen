"""Shared prompts for Birkenbihl translation method.

These prompts are used by all translation providers to ensure consistent
behavior across OpenAI, Anthropic, and other models.
"""

BIRKENBIHL_SYSTEM_PROMPT = """You are a language translation expert specializing in the Vera F. Birkenbihl \
language learning method.

Your task is to provide TWO types of translations:

1. **Natural Translation (Natürliche Übersetzung)**:
   - Fluent, idiomatic translation that sounds natural in the target language
   - Maintains the meaning and tone of the original text
   - Uses proper grammar and sentence structure

2. **Word-by-Word Translation (Wort-für-Wort Dekodierung)**:
   - Each word from the source text is aligned with its translation
   - Shows the structure of the source language
   - Helps learners understand how the source language constructs meaning
   - Uses hyphens to connect words that translate to a single concept (e.g., "vermissen-werde")
   - Position indicates the sequential order for proper alignment in the UI

**Critical Requirements:**
- Every word from the natural translation MUST appear in the word-by-word alignments
- Word alignments should follow the source language word order
- For compound translations (multiple source words → single target word), use hyphens
- Maintain consistent position numbering starting from 0

**Example:**
Source (Spanish): "Yo te extrañaré"
Natural (German): "Ich werde dich vermissen"
Word-by-word:
  - "Yo" → "Ich" (position 0)
  - "te" → "dich" (position 1)
  - "extrañaré" → "vermissen-werde" (position 2)

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
    # Map language codes to full names for clarity
    lang_names = {
        "en": "English",
        "es": "Spanish",
        "de": "German",
        "fr": "French",
        "it": "Italian",
        "pt": "Portuguese",
    }

    source_name = lang_names.get(source_lang, source_lang.upper())
    target_name = lang_names.get(target_lang, target_lang.upper())

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
    lang_names = {
        "en": "English",
        "es": "Spanish",
        "de": "German",
        "fr": "French",
        "it": "Italian",
        "pt": "Portuguese",
    }

    source_name = lang_names.get(source_lang, source_lang.upper())
    target_name = lang_names.get(target_lang, target_lang.upper())

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
    lang_names = {
        "en": "English",
        "es": "Spanish",
        "de": "German",
        "fr": "French",
        "it": "Italian",
        "pt": "Portuguese",
    }

    source_name = lang_names.get(source_lang, source_lang.upper())
    target_name = lang_names.get(target_lang, target_lang.upper())

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
