# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Birkenbihl is a Python application that digitizes the Vera F. Birkenbihl language learning method. The app provides dual translations (natural + word-by-word) to help users understand foreign language structure, particularly for English/Spanish → German.

## Development Commands

### Setup
```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)
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
├── protocols/       # Protocol definitions (interfaces)
├── providers/       # Protocol implementations
├── models/          # Data models (Pydantic)
├── main.py          # Application entry point
tests/               # Test files matching src/ structure
specs/               # Requirements documentation
```

## Testing Notes

- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.ui`
- Coverage configured to fail under 80%
- Async tests automatically handled with `asyncio_mode = auto`
