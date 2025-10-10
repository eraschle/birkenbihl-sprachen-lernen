---
description: Convert Birkenbihl RTF file to JSON test fixture
---

You are helping to convert a Birkenbihl method RTF file into a structured JSON test fixture.

## Task

1. Ask the user for the RTF file path (if not already provided)
2. Read the RTF file
3. Extract English source texts and German word-by-word translations:
   - English text: Normal font (not bold)
   - German word-by-word: Bold font (\\b marker in RTF)
   - Remove speaker names (e.g., "Jane:", "Mike:")
4. Create a JSON fixture file in `tests/fixtures/` with format:
   ```json
   {
     "description": "Unit X - English to German word-by-word translations",
     "source_language": "en",
     "target_language": "de",
     "test_cases": [
       {
         "source_text": "English text here",
         "expected_word_by_word": "German word-by-word here"
       }
     ]
   }
   ```
5. Ask the user for the output filename (suggest based on unit name)
6. Save the file to `tests/fixtures/<filename>.json`

## RTF Parsing Rules

- English text appears before German translation
- German word-by-word is marked with `\b` (bold) in RTF
- Remove speaker names (pattern: `Name:\tab`)
- Clean up extra whitespace and tabs
- Preserve punctuation and special characters (ü, ö, ä, ß)
- Handle multi-line sentences (combine into single entry)

## Output

Confirm the number of test cases extracted and the file path where saved.
