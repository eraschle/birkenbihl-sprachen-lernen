"""Shared prompts for Birkenbihl translation method.

These prompts are used by all translation providers to ensure consistent
behavior across OpenAI, Anthropic, and other models.
"""

BIRKENBIHL_SYSTEM_PROMPT = """You are a language translation expert specializing in the Vera F. Birkenbihl language learning method.

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
        return f"""Translate ALL {len(sentences)} sentences from {source_name} to {target_name} using the Birkenbihl method.

Source sentences:
{sentences_text}

CRITICAL: You must translate ALL {len(sentences)} sentences listed above.
Provide for EACH sentence separately:
1. Natural translation in {target_name}
2. Word-by-word alignment showing how each source word maps to the target language

Your response must contain exactly {len(sentences)} sentence translations - one for each source sentence.
"""
