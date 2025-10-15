# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Birkenbihl is a Python application that digitizes the Vera F. Birkenbihl language learning method. The app provides dual translations (natural + word-by-word) to help users understand foreign language structure, particularly for English/Spanish → German.

## ⚠️ Pre-Release Project - No Legacy Code Policy

**IMPORTANT: This application has NEVER been released to production or end users.**

**Implications:**
- ❌ **NO legacy code exists** - There are no users with old versions
- ❌ **NO backwards compatibility needed** - No migration code required
- ❌ **NO deprecated features** - Remove unused code immediately
- ✅ **DELETE unused code** - If a feature/function is not used, delete it
- ✅ **Clean codebase** - Only include code that is actually executed
- ✅ **Refactor freely** - Breaking changes are acceptable and encouraged

**Rules:**
1. **Never implement migration code** for "old" versions that don't exist
2. **Never keep "backwards compatible" alternatives** - there's nothing to be compatible with
3. **Delete unused functions/classes immediately** - don't keep "just in case"
4. **Refactor aggressively** - optimize for current design, not past decisions
5. **No "legacy" or "deprecated" markers** - if something is old, delete it

**Example:**
- ❌ BAD: "Let's keep both `translate_and_save()` and `translate()` for backwards compatibility"
- ✅ GOOD: "The old `translate_and_save()` is not used anymore, delete it"

## Development Commands

### Setup
```bash
# Install dependencies
uv sync

# Configure providers and API keys
cp settings.yaml.example settings.yaml
# Edit settings.yaml: Add API keys directly in provider configs

# Alternative: Use .env for API keys (optional)
cp .env.example .env
# Edit .env and reference in settings.yaml: api_key: ${OPENAI_API_KEY}
```

### Running
```bash
# Run the application
uv run python -m birkenbihl.main
# or
birkenbihl
```

### Testing
```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/models/translation.py
```

### Linting & Type Checking
```bash
# Ruff (line length: 120 chars)
uv run ruff check .
uv run ruff format .

# Pyright (strict type checking)
uv run pyright
```

## Architecture

### Protocol-Based Design (SOLID Principles)

The codebase uses Protocol-based abstractions for dependency injection and testability:

**Translation Protocol** (`src/birkenbihl/protocols/translation.py`):
- `TranslationProvider`: Defines interface for translation providers
  - `translate()`: Returns both natural and word-by-word translations (Birkenbihl method)
  - `detect_language()`: Auto-detects source language (en, es, de)

**Providers** (`src/birkenbihl/providers/`):
- `PydanticAITranslationProvider`: Implements `TranslationProvider` using Pydantic AI
  - Supports multiple AI models (OpenAI GPT-4, Anthropic Claude, etc.)
  - Uses structured outputs (`BirkenbihTranslation` model)
  - Handles async execution with threading to avoid event loop conflicts

### Birkenbihl Method Implementation

The app implements two translation types:
1. **Natural Translation**: Fluent, idiomatic translation
2. **Word-by-Word Translation**: Each word translated individually to reveal language structure

Example:
```
Original:     "Yo te extrañaré"
Natural:      "Ich werde dich vermissen"
Word-by-Word: "Ich dich vermissen-werde"
```
It is important that all word of the `natural` translation are used in the `word-by-word`

### Data Models

**Translation Results** (`src/birkenbihl/models/translation.py`):
- Uses Pydantic models for validation and serialization
- **UUIDs for Identity:** All entities use UUIDs for cross-storage compatibility (JSON, DB, Excel)
- Domain models (not tied to specific storage implementation):
  - `WordAlignment`: Maps source_word ↔ target_word with position for UI ordering
  - `Sentence`: Single sentence with source_text, natural_translation, word_alignments[]
    - Each sentence has unique UUID for referencing in UI/storage
  - `Translation`: Root aggregate containing multiple sentences
    - Fields: id, title (optional), source_language, target_language, sentences[]
    - Timestamps: created_at, updated_at
    - Represents complete translation document/session

**ID Strategy:**
- Domain models have UUIDs (not database auto-increment IDs)
- Why: Cross-storage portability - same ID works in JSON files, SQLite, Excel exports
- Storage layer (DAOs) may use additional internal IDs but must preserve domain UUIDs

### Services Layer

Services orchestrate business logic by coordinating protocols/providers:

**TranslationService** (`src/birkenbihl/services/translation_service.py`):
- Coordinates TranslationProvider (AI) + StorageProvider (persistence)
- High-level workflows:
  - `translate_and_save()`: Translate text and persist to storage
  - `auto_detect_and_translate()`: Auto-detect language before translation
  - `get_translation()`, `list_all_translations()`: Retrieval operations
  - `update_translation()`, `delete_translation()`: Modification operations
- Follows dependency injection via Protocol-based constructors
- No business logic in providers - services orchestrate the flow

**AudioService** (`src/birkenbihl/services/audio_service.py`) - Phase 2:
- Coordinates AudioProvider for text-to-speech operations
- Supports active listening phase of Birkenbihl method
- Workflows:
  - `generate_sentence_audio()`: Create audio file for single sentence
  - `play_sentence()`: Direct playback of sentence audio
  - `batch_generate_audio()`: Generate audio for multiple sentences
- Status: Stub implementation (raises NotImplementedError)

### Storage Layer

**Storage Protocol** (`src/birkenbihl/protocols/storage.py`):
- `StorageProvider`: Defines CRUD interface for Translation persistence
- Operations: `save()`, `get()`, `list_all()`, `update()`, `delete()`
- All operations use UUIDs for entity identification

**Planned Implementations:**
- `JsonStorageProvider`: File-based storage in `.json` format (Phase 1)
- `SqliteStorageProvider`: SQLite database with SQLModel (Phase 2)
- `ExcelStorageProvider`: Export translations to Excel format (Phase 2)

**DAO Pattern:**
- Storage implementations may use internal DAO models for persistence
- DAOs must map to/from domain models (`Translation`, `Sentence`, `WordAlignment`)
- Domain UUIDs must be preserved across all storage backends

## Code Style Requirements

- **Python Version**: 3.13+
- **Type Hints**: Modern syntax (no `typing` imports for built-in collections)
  - Use `list`, `dict`, `tuple` directly
  - Use `|` for Union types
  - Use `| None` for Optional
- **Line Length**: 120 characters (Ruff)
- **Type Checking**: Standard mode enabled (Pyright)
- **Architecture**: Follow SOLID principles and design patterns

### Clean Code Principles (Uncle Bob)

**Meaningful Names**
- Use intention-revealing names that communicate purpose
- Avoid abbreviations unless universally understood
- Use pronounceable, searchable names
- Classes: Noun phrases (`TranslationProvider`, `AudioService`)
- Functions: Verb phrases (`translate()`, `detect_language()`)
- Avoid mental mapping - be explicit

**Functions**
- Small functions (5-20 lines ideally)
- Do one thing and do it well
- Single level of abstraction per function
- No side effects - function does what name suggests
- Prefer fewer arguments (0-2 ideal, max 3)
- Use exceptions instead of error codes
- Extract try/except blocks into separate functions

**Don't Repeat Yourself (DRY)**
- Extract duplicate logic into reusable functions
- Use protocols for shared interfaces
- Avoid copy-paste programming

**Comments**
- Code should be self-documenting
- Use comments to explain **why**, not **what**
- Docstrings for public APIs only
- Remove commented-out code (use git history)
- Avoid redundant comments that just restate the code

**Error Handling**
- Use exceptions, not return codes
- Provide context with exceptions
- Don't return `None` - raise exceptions or use type-safe optionals
- Write tests for error cases

**Formatting**
- Vertical density: Related code stays together
- Vertical distance: Related concepts close, unrelated concepts separated
- Consistent indentation and spacing
- Group imports: stdlib → third-party → local

**Classes**
- Small and focused (Single Responsibility Principle)
- High cohesion: Methods use instance variables
- Low coupling: Minimal dependencies
- Organize: public methods first, private methods last

### Future Components (Currently Stubbed)

- **UI Layer**: interface (planned)
- **Storage Layer**: SQLite + SQLModel for persistence (planned)
- **Audio Service**: Text-to-speech for original language playback (planned)

## Project Structure

```
src/birkenbihl/
├── protocols/           # Protocol definitions (interfaces)
│   ├── translation.py   # TranslationProvider protocol
│   ├── storage.py       # StorageProvider protocol
│   └── audio.py         # AudioProvider protocol (Phase 2)
├── providers/           # Protocol implementations
│   └── (translation providers - to be implemented)
├── models/              # Domain models (Pydantic)
│   └── translation.py   # Translation, Sentence, WordAlignment
├── services/            # Business logic orchestration
│   ├── translation_service.py  # Translation + Storage coordination
│   └── audio_service.py        # Audio/TTS (Phase 2 stub)
├── storage/             # Storage implementations (planned)
│   ├── json_storage.py      # JSON file storage
│   ├── sqlite_storage.py    # SQLite + SQLModel
│   └── excel_storage.py     # Excel export
└── main.py              # Application entry point
tests/                   # Test files matching src/ structure
specs/                   # Requirements documentation
```

## Testing Notes

- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.ui`
- Coverage configured to fail under 80%
- Async tests automatically handled with `asyncio_mode = auto`
