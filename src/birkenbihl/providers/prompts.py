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


def create_translation_prompt(text: str, source_lang: str, target_lang: str) -> str:
    """Create user prompt for translation request.

    Args:
        text: Text to translate (can contain multiple sentences)
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

    return f"""Translate the following text from {source_name} to {target_name} using the Birkenbihl method.

Source text:
{text}

Provide:
1. Natural translation in {target_name}
2. Word-by-word alignment showing how each source word maps to the target language

Split the text into individual sentences and provide both translation types for each sentence.
"""
