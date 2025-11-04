# Birkenbihl Project - Work Plan & Progress Tracking

**Branch:** `claude/project-status-review-011CUoV5gMroEvMrmr1u57LA`
**Start Date:** 2025-11-04
**Target Completion:** 2025-12-09 (5 weeks)
**Current Phase:** Planning

---

## Executive Summary

This work plan addresses the remaining tasks to bring the Birkenbihl application to production-ready status. The project has excellent architecture (⭐⭐⭐⭐⭐) and 95% complete Phase 1 functionality, but requires:

1. **Code Quality Improvements** - Refactor long functions (42-50 LOC → <20 LOC)
2. **Critical UI Feature** - Implement Interleaved Word Alignment Editor (core Birkenbihl method)
3. **Phase 2 Features** - AudioService + Excel Export

**Current Health:**
- Architecture: ⭐⭐⭐⭐⭐ (5/5)
- Code Quality: 87% compliance (target: 100%)
- Test Coverage: 80%+ (target met)
- Functional Completeness: 60% (Word Alignment Editor missing)

---

## Code Quality Standards (Must Follow)

### Clean Code Principles (Uncle Bob)
- ✅ Functions ≤20 lines (target: 100%, current: 87%)
- ✅ Parameters ≤2 per function (target: 100%, current: 88%)
- ✅ Meaningful names (intention-revealing)
- ✅ Single Responsibility Principle
- ✅ DRY - Don't Repeat Yourself
- ✅ No commented-out code
- ✅ Exceptions, not error codes

### Python Code Style
- ✅ Python 3.13+ type hints (no `typing` imports for built-ins)
- ✅ Use `list`, `dict`, `tuple` directly
- ✅ Use `|` for Union types, `| None` for Optional
- ✅ Line length: 120 characters (Ruff)
- ✅ Pyright strict type checking
- ✅ No emojis unless explicitly requested

### Architecture Standards
- ✅ SOLID principles (current: 4.7/5, target: 5/5)
- ✅ Protocol-based dependency injection
- ✅ Layer separation: Models → Services → Storage → Providers
- ✅ MVVM pattern for GUI components
- ✅ No legacy code (pre-release project - delete unused code)

### Pre-Commit Checklist
Before each commit, verify:
- [ ] All functions ≤20 lines
- [ ] All parameters ≤2 (use Parameter Objects if needed)
- [ ] Type hints on all functions
- [ ] No commented-out code
- [ ] Tests pass (`uv run pytest`)
- [ ] Ruff check passes (`uv run ruff check .`)
- [ ] Pyright check passes (`uv run pyright`)
- [ ] Meaningful commit message (why, not what)

---

## Phase Overview

| Phase | Duration | Priority | Status |
|-------|----------|----------|--------|
| Phase 1: Code Quality Refactoring | Week 1-2 | CRITICAL | ⏳ Not Started |
| Phase 2: Word Alignment Editor | Week 3-5 | CRITICAL | ⏳ Not Started |
| Phase 3: AudioService | Week 6-7 | HIGH | ⏳ Not Started |
| Phase 4: Excel Export | Optional | MEDIUM | ⏳ Not Started |

---

## Phase 1: Code Quality Refactoring (Week 1-2)

**Goal:** Achieve 100% Clean Code compliance (from 87%)
**Priority:** CRITICAL
**Estimated Duration:** 8-12 hours

### 1.1 Refactor SqliteStorageProvider (2-3 hours)

**Files:** `src/birkenbihl/storage/sqlite_storage.py`

**Tasks:**
- [ ] **1.1.1** Split `_to_dao()` method (42 LOC → <20 LOC)
  - Extract `_create_translation_dao()` - Create TranslationDAO from Translation
  - Extract `_create_sentence_daos()` - Convert sentences to DAO list
  - Extract `_create_alignment_daos()` - Convert word alignments to DAO list
  - Keep `_to_dao()` as orchestrator (max 15 LOC)

- [ ] **1.1.2** Split `_from_dao()` method (38 LOC → <20 LOC)
  - Extract `_build_translation_model()` - Create Translation from DAO
  - Extract `_build_sentences()` - Convert sentence DAOs to models
  - Extract `_build_alignments()` - Convert alignment DAOs to models
  - Keep `_from_dao()` as orchestrator (max 15 LOC)

- [ ] **1.1.3** Add unit tests for extracted functions
- [ ] **1.1.4** Run Pyright + Ruff validation
- [ ] **1.1.5** Commit: "refactor(storage): Split SqliteStorage DAO converters to <20 LOC"

**Success Criteria:**
- All functions in SqliteStorageProvider ≤20 LOC
- Type hints complete
- Tests pass with 80%+ coverage
- No regression in functionality

---

### 1.2 Refactor CLI translate() Command (3-4 hours)

**Files:** `src/birkenbihl/cli.py`

**Tasks:**
- [ ] **1.2.1** Split `translate()` command (50 LOC → <20 LOC)
  - Extract `_get_translation_config()` - Parse CLI options to config object
  - Extract `_execute_translation()` - Call service with config
  - Extract `_display_translation_result()` - Format and display output
  - Extract `_handle_translation_error()` - Error handling
  - Keep `translate()` as orchestrator (max 15 LOC)

- [ ] **1.2.2** Introduce `TranslationConfig` dataclass
  - Parameters: source_language, target_language, title, provider_name, storage_type
  - Reduce CLI function parameters from 6 to 2 (ctx, config)

- [ ] **1.2.3** Add unit tests for extracted functions
- [ ] **1.2.4** Run Pyright + Ruff validation
- [ ] **1.2.5** Commit: "refactor(cli): Split translate command to <20 LOC with config object"

**Success Criteria:**
- All CLI functions ≤20 LOC
- Parameters ≤2 per function
- Type hints complete
- CLI still works identically

---

### 1.3 Implement Presenter Layer (3-4 hours)

**Files:** `src/birkenbihl/presenters/` (new directory)

**Tasks:**
- [ ] **1.3.1** Create `TranslationPresenter` class
  - Method: `format_translation_display(translation)` → DisplayModel
  - Method: `format_sentence_display(sentence)` → SentenceDisplayModel
  - Method: `format_word_alignment_display(alignment)` → AlignmentDisplayModel
  - Consolidates display logic shared by CLI and GUI

- [ ] **1.3.2** Create `DisplayModel` dataclasses
  - `DisplayModel`: Formatted translation data for display
  - `SentenceDisplayModel`: Formatted sentence data
  - `AlignmentDisplayModel`: Formatted alignment data

- [ ] **1.3.3** Refactor CLI to use TranslationPresenter
  - Replace inline formatting with presenter calls
  - Eliminates code duplication

- [ ] **1.3.4** Refactor GUI to use TranslationPresenter
  - Replace GUI-specific formatting with presenter calls
  - Shared display logic

- [ ] **1.3.5** Add unit tests for presenter
- [ ] **1.3.6** Run Pyright + Ruff validation
- [ ] **1.3.7** Commit: "feat(presenters): Add Presenter layer to eliminate CLI/GUI duplication"

**Success Criteria:**
- No display logic duplication between CLI and GUI
- All presenter functions ≤20 LOC
- DRY compliance improved to 95%+

---

### 1.4 Error Handling Alignment (2 hours)

**Files:** All service files

**Tasks:**
- [ ] **1.4.1** Review exception handling across services
  - Ensure layered error handling (no swallowed exceptions)
  - Consistent error messages

- [ ] **1.4.2** Create custom exception classes if needed
  - `TranslationError`, `StorageError`, `ProviderError`
  - Inherit from base `BirkenbihError`

- [ ] **1.4.3** Add error tests
- [ ] **1.4.4** Run Pyright + Ruff validation
- [ ] **1.4.5** Commit: "refactor(errors): Align error handling across services"

**Success Criteria:**
- All errors properly propagated
- Context provided with exceptions
- Error tests pass

---

### 1.5 Parameter Object Implementation (2 hours)

**Files:** Services with >2 parameters

**Tasks:**
- [ ] **1.5.1** Identify functions with >2 parameters
  - `TranslationService.translate()` - 4 parameters
  - `CreateTranslationViewModel.create_translation()` - 5 parameters

- [ ] **1.5.2** Create parameter objects
  - `TranslationRequest` dataclass
  - `CreateTranslationRequest` dataclass

- [ ] **1.5.3** Refactor functions to use parameter objects
- [ ] **1.5.4** Update tests
- [ ] **1.5.5** Run Pyright + Ruff validation
- [ ] **1.5.6** Commit: "refactor(services): Introduce parameter objects to reduce argument count"

**Success Criteria:**
- 100% of functions have ≤2 parameters
- Type hints complete
- Tests pass

---

### 1.6 Two-Step Translation Refactoring (4-5 hours)

**Goal:** Separate natural translation from word alignment generation
**Priority:** HIGH (Improves translation quality and follows Birkenbihl method)
**Estimated Duration:** 4-5 hours

**Context:**
Currently, `BaseTranslator.translate()` uses a single prompt to generate both
natural translation AND word alignments in one AI call. This approach:
- Violates NLP best practices (word alignment is separate task in state-of-the-art systems)
- Contradicts the original Birkenbihl method (4 separate steps)
- Reduces control over translation quality
- Prevents user editing of natural translation before alignment

**New Approach (Two-Step Process):**
1. **Step 1 - Natural Translation Only:**
   - Input: Source text
   - Output: Natural translation
   - Save to storage

2. **Step 2 - Word Alignment Generation:**
   - Input: Source text + source words list + target words list
   - Output: Word alignments
   - Rules: Each target word used exactly once, multiple words connected with hyphens

**Files:**
- `src/birkenbihl/providers/prompts.py`
- `src/birkenbihl/providers/base_translator.py`
- `src/birkenbihl/providers/models.py`
- `tests/providers/test_base_translator.py`

**Tasks:**
- [ ] **1.6.1** Create new prompts for Step 1 (natural translation only)
  - New system prompt: Remove word-by-word requirements
  - New user prompt: Request only natural translation
  - Keep focus on fluent, idiomatic translation
  - Prefer separate words over compounds for better alignment
  - Create `NaturalTranslationResponse` model (without alignments)
  - Max 20 LOC per function

- [ ] **1.6.2** Refactor `BaseTranslator.translate()` to two steps
  - **Step 1**: Call new natural translation agent
    - Input: sentences, source_lang, target_lang
    - Output: List of natural translations
    - Store intermediate result
  - **Step 2**: For each sentence, generate word alignments
    - Use existing `create_word_by_word_prompt()` or `create_regenerate_alignment_prompt()`
    - Input: source_text, natural_translation, source_words[], target_words[]
    - Output: WordAlignment[]
  - Combine results into final Translation model
  - Extract to helper functions (max 20 LOC each):
    - `_generate_natural_translations()` - Step 1 logic
    - `_generate_word_alignments_for_sentence()` - Step 2 logic for single sentence
    - `_generate_all_alignments()` - Step 2 orchestration
  - Keep main `translate()` as orchestrator (max 15 LOC)

- [ ] **1.6.3** Update `translate_stream()` for two-step process
  - Yield progress after Step 1 (50% completion)
  - Yield progress during Step 2 (50%-100%)
  - Extract streaming logic to helper functions (max 20 LOC each)

- [ ] **1.6.4** Verify existing `regenerate_alignment()` still works
  - This method already implements Step 2 logic
  - May need alignment with new `_generate_word_alignments_for_sentence()`
  - Avoid code duplication (DRY principle)

- [ ] **1.6.5** Add/update unit tests
  - Test natural translation generation (Step 1)
  - Test word alignment generation (Step 2)
  - Test end-to-end two-step workflow
  - Test edge cases (empty alignments, missing words)
  - Mock AI responses for deterministic tests

- [ ] **1.6.6** Update integration tests
  - Verify Spanish alignment test still passes
  - Verify Unit 1.1 tests still pass
  - Check that validation still catches misalignments

- [ ] **1.6.7** Add logging for debugging
  - Log Step 1 API call and response
  - Log Step 2 API call per sentence
  - Log intermediate state between steps
  - Performance metrics (time per step)

- [ ] **1.6.8** Run Pyright + Ruff validation
- [ ] **1.6.9** Commit: "refactor(providers): Split translation into two-step process (natural + alignment)"

**Success Criteria:**
- Translation quality improved (better alignments)
- Natural translation can be edited before alignment generation
- All functions ≤20 LOC
- Existing `regenerate_alignment()` logic reused (DRY)
- All tests pass (unit + integration)
- Performance acceptable (two API calls vs one)
- Logging shows clear two-step process

**Benefits:**
- ✅ Follows NLP best practices (BinaryAlign, TransAlign approach)
- ✅ Aligns with original Birkenbihl method (separate steps)
- ✅ Better control over translation quality
- ✅ User can edit natural translation before alignment
- ✅ Word alignment can be regenerated independently
- ✅ Separation of Concerns (SRP principle)
- ✅ Easier debugging (isolate which step failed)

**Performance Considerations:**
- Two API calls instead of one (latency increases)
- Mitigation: Use streaming for real-time progress feedback
- Mitigation: Cache natural translations for regeneration scenarios
- Trade-off: Better quality justifies slightly longer wait

---

### Phase 1 Completion Checklist

Before moving to Phase 2, verify:
- [ ] All functions ≤20 LOC (100% compliance)
- [ ] All functions ≤2 parameters (100% compliance)
- [ ] Presenter layer implemented
- [ ] Error handling aligned
- [ ] Two-step translation process implemented
  - [ ] Natural translation generation works independently
  - [ ] Word alignment generation works independently
  - [ ] End-to-end workflow produces correct results
  - [ ] Integration tests pass (Spanish, Unit 1.1)
- [ ] All tests pass
- [ ] Ruff check passes
- [ ] Pyright check passes
- [ ] Code quality score: ⭐⭐⭐⭐⭐ (5/5)

**Expected Completion:** 2025-11-20 (adjusted for Phase 1.6)

---

## Phase 2: Interleaved Word Alignment Editor (Week 3-5)

**Goal:** Implement core UI feature of Birkenbihl method
**Priority:** CRITICAL (Without this, app is incomplete)
**Estimated Duration:** 2-3 weeks (15-20 hours)

### 2.1 Architecture & Design (2 hours)

**Files:** `specs/UI_ALIGNMENT_EDITOR.md` (new spec doc)

**Tasks:**
- [ ] **2.1.1** Define UI requirements
  - Drag-and-drop interaction model
  - Interleaved grid layout (source word | target word | source word | ...)
  - Unassigned words pool
  - Multi-word alignment support

- [ ] **2.1.2** Create widget hierarchy
  - `InterleavedAlignmentEditor` (container)
  - `DraggableWordTag` (individual word)
  - `AlignmentDropZone` (drop target)
  - `UnassignedWordsPool` (unmatched words)
  - `AlignmentGrid` (interleaved layout)

- [ ] **2.1.3** Define data flow
  - Model: `WordAlignment` (domain model)
  - ViewModel: `AlignmentEditorViewModel` (state management)
  - View: `InterleavedAlignmentEditor` (Qt widget)

- [ ] **2.1.4** Create mockups/wireframes
- [ ] **2.1.5** Commit: "docs(specs): Add Word Alignment Editor specification"

**Success Criteria:**
- Clear UI specification
- Widget hierarchy defined
- MVVM pattern followed

---

### 2.2 Base Widgets (4-5 hours)

**Files:** `src/birkenbihl/gui/widgets/alignment/`

**Tasks:**
- [ ] **2.2.1** Create `DraggableWordTag` widget
  - Displays single word (source or target)
  - Drag support (QDrag)
  - Visual states: normal, dragging, selected
  - Methods: `start_drag()`, `set_state()`
  - Max 20 LOC per method

- [ ] **2.2.2** Create `AlignmentDropZone` widget
  - Accepts dropped words
  - Drop validation (source/target type checking)
  - Visual feedback on drag-over
  - Methods: `accept_drop()`, `validate_drop()`, `highlight()`
  - Max 20 LOC per method

- [ ] **2.2.3** Create `UnassignedWordsPool` widget
  - Container for unaligned words
  - Separate pools for source/target words
  - Flow layout for word tags
  - Methods: `add_word()`, `remove_word()`, `clear()`
  - Max 20 LOC per method

- [ ] **2.2.4** Add unit tests for widgets (mocked Qt)
- [ ] **2.2.5** Run Pyright + Ruff validation
- [ ] **2.2.6** Commit: "feat(gui): Add base widgets for word alignment (DraggableTag, DropZone, Pool)"

**Success Criteria:**
- All widget methods ≤20 LOC
- Drag-and-drop works
- Visual feedback present
- Unit tests pass

---

### 2.3 Alignment Grid (3-4 hours)

**Files:** `src/birkenbihl/gui/widgets/alignment/alignment_grid.py`

**Tasks:**
- [ ] **2.3.1** Create `AlignmentGrid` widget
  - Interleaved layout: Source | Target | Source | Target | ...
  - Dynamic row generation based on WordAlignment list
  - Insert/delete alignment support
  - Methods: `build_grid()`, `add_alignment_row()`, `remove_alignment_row()`
  - Max 20 LOC per method

- [ ] **2.3.2** Implement alignment rendering
  - Render `WordAlignment` objects as grid rows
  - Multi-word alignment support (multiple tags in cell)
  - Empty cell placeholders

- [ ] **2.3.3** Add keyboard navigation
  - Tab/Shift+Tab between cells
  - Delete key to remove alignment
  - Arrow keys for navigation

- [ ] **2.3.4** Add unit tests
- [ ] **2.3.5** Run Pyright + Ruff validation
- [ ] **2.3.6** Commit: "feat(gui): Add AlignmentGrid with interleaved layout"

**Success Criteria:**
- Grid renders correctly
- Keyboard navigation works
- All methods ≤20 LOC
- Tests pass

---

### 2.4 Alignment Editor ViewModel (2-3 hours)

**Files:** `src/birkenbihl/gui/viewmodels/alignment_editor_viewmodel.py`

**Tasks:**
- [ ] **2.4.1** Create `AlignmentEditorViewModel`
  - State: current_sentence, word_alignments, unassigned_source, unassigned_target
  - Signals: alignment_changed, validation_error
  - Methods: `load_sentence()`, `add_alignment()`, `remove_alignment()`, `validate()`
  - Max 20 LOC per method

- [ ] **2.4.2** Implement alignment logic
  - `create_alignment(source_word, target_word)` → WordAlignment
  - `split_alignment(alignment_id)` → separate words
  - `merge_alignments(ids)` → multi-word alignment
  - Validation: ensure all words aligned

- [ ] **2.4.3** Add change tracking
  - Dirty flag for unsaved changes
  - Undo/redo support (optional)

- [ ] **2.4.4** Add unit tests
- [ ] **2.4.5** Run Pyright + Ruff validation
- [ ] **2.4.6** Commit: "feat(gui): Add AlignmentEditorViewModel with alignment logic"

**Success Criteria:**
- ViewModel manages state correctly
- Signals emit on changes
- All methods ≤20 LOC
- Tests pass

---

### 2.5 Interleaved Alignment Editor (3-4 hours)

**Files:** `src/birkenbihl/gui/views/alignment_editor_view.py`

**Tasks:**
- [ ] **2.5.1** Create `InterleavedAlignmentEditor` view
  - Compose: AlignmentGrid + UnassignedWordsPool
  - Connect to AlignmentEditorViewModel
  - Layout: Grid on top, pools below
  - Methods: `setup_ui()`, `bind_viewmodel()`, `on_alignment_changed()`
  - Max 20 LOC per method

- [ ] **2.5.2** Implement drag-and-drop coordination
  - Word dragged from pool → dropped on grid
  - Word dragged from grid → dropped in pool (unassign)
  - Word dragged from grid cell to grid cell (reorder)

- [ ] **2.5.3** Add toolbar actions
  - Save alignment button
  - Reset button
  - Validate alignment button

- [ ] **2.5.4** Add integration tests
- [ ] **2.5.5** Run Pyright + Ruff validation
- [ ] **2.5.6** Commit: "feat(gui): Add InterleavedAlignmentEditor view with full workflow"

**Success Criteria:**
- Complete alignment workflow works
- Drag-and-drop between all zones
- All methods ≤20 LOC
- Integration tests pass

---

### 2.6 Integration with TranslationService (2 hours)

**Files:** `src/birkenbihl/services/translation_service.py`, GUI views

**Tasks:**
- [ ] **2.6.1** Add `update_sentence_alignment()` method to TranslationService
  - Parameters: translation_id, sentence_id, new_alignments
  - Updates WordAlignment list for sentence
  - Persists to storage

- [ ] **2.6.2** Connect editor to service
  - Load sentence from translation
  - Save alignment changes
  - Error handling

- [ ] **2.6.3** Add integration tests
- [ ] **2.6.4** Run Pyright + Ruff validation
- [ ] **2.6.5** Commit: "feat(gui): Integrate AlignmentEditor with TranslationService"

**Success Criteria:**
- Alignments persist to storage
- Service integration works
- Tests pass

---

### Phase 2 Completion Checklist

Before moving to Phase 3, verify:
- [ ] Word Alignment Editor fully functional
- [ ] Drag-and-drop works smoothly
- [ ] All widgets ≤20 LOC per method
- [ ] MVVM pattern followed
- [ ] Integration tests pass
- [ ] Manual UI testing completed
- [ ] Ruff check passes
- [ ] Pyright check passes

**Expected Completion:** 2025-12-02

---

## Phase 3: AudioService Implementation (Week 6-7)

**Goal:** Implement text-to-speech for active listening phase
**Priority:** HIGH
**Estimated Duration:** 1-2 weeks (8-12 hours)

### 3.1 Audio Protocol & Provider Architecture (2 hours)

**Files:** `src/birkenbihl/protocols/audio.py`, `src/birkenbihl/providers/`

**Tasks:**
- [ ] **3.1.1** Review `IAudioProvider` protocol
  - Methods: `generate_audio()`, `play_audio()`, `batch_generate()`
  - Ensure protocol is complete

- [ ] **3.1.2** Create `TTSProviderConfig` dataclass
  - Parameters: provider_name, api_key, voice, language, speed

- [ ] **3.1.3** Choose TTS provider(s)
  - Option 1: OpenAI TTS (gpt-4-audio)
  - Option 2: Google Cloud Text-to-Speech
  - Option 3: Eleven Labs
  - Option 4: Local TTS (pyttsx3)

- [ ] **3.1.4** Commit: "refactor(audio): Review and enhance IAudioProvider protocol"

**Success Criteria:**
- Protocol is complete
- Provider architecture planned

---

### 3.2 TTS Provider Implementation (4-5 hours)

**Files:** `src/birkenbihl/providers/openai_tts_provider.py` (or similar)

**Tasks:**
- [ ] **3.2.1** Create TTS provider class
  - Implements `IAudioProvider`
  - Methods: `generate_audio()`, `play_audio()`, `batch_generate()`
  - Max 20 LOC per method
  - Uses asyncio for API calls

- [ ] **3.2.2** Implement audio generation
  - Text → API call → audio file (mp3/wav)
  - Language detection support
  - Voice selection based on language

- [ ] **3.2.3** Implement audio playback
  - Use pygame/sounddevice for playback
  - Streaming support for long audio

- [ ] **3.2.4** Add unit tests (mocked API)
- [ ] **3.2.5** Run Pyright + Ruff validation
- [ ] **3.2.6** Commit: "feat(providers): Add OpenAI TTS provider implementation"

**Success Criteria:**
- TTS provider works
- Audio files generated correctly
- All methods ≤20 LOC
- Tests pass

---

### 3.3 AudioService Implementation (2-3 hours)

**Files:** `src/birkenbihl/services/audio_service.py`

**Tasks:**
- [ ] **3.3.1** Replace stubs with real implementation
  - `generate_sentence_audio()` - Calls TTS provider
  - `play_sentence()` - Plays audio directly
  - `batch_generate_audio()` - Batch processing
  - Max 20 LOC per method

- [ ] **3.3.2** Add caching
  - Cache generated audio files by sentence ID
  - Avoid re-generating same audio

- [ ] **3.3.3** Add error handling
  - Handle API failures gracefully
  - Fallback to alternative provider

- [ ] **3.3.4** Add unit tests
- [ ] **3.3.5** Run Pyright + Ruff validation
- [ ] **3.3.6** Commit: "feat(services): Implement AudioService with TTS support"

**Success Criteria:**
- AudioService fully functional
- Caching works
- All methods ≤20 LOC
- Tests pass

---

### 3.4 GUI Integration (2 hours)

**Files:** `src/birkenbihl/gui/views/`, GUI widgets

**Tasks:**
- [ ] **3.4.1** Add audio playback controls to sentence view
  - Play button per sentence
  - Stop/pause controls
  - Volume slider

- [ ] **3.4.2** Connect to AudioService
  - Click play → calls `audio_service.play_sentence()`
  - Visual feedback during playback

- [ ] **3.4.3** Add batch generation option
  - "Generate all audio" button
  - Progress indicator

- [ ] **3.4.4** Add integration tests
- [ ] **3.4.5** Run Pyright + Ruff validation
- [ ] **3.4.6** Commit: "feat(gui): Add audio playback controls to sentence view"

**Success Criteria:**
- Audio playback works in GUI
- Controls are responsive
- Integration tests pass

---

### Phase 3 Completion Checklist

Before moving to Phase 4, verify:
- [ ] AudioService fully implemented
- [ ] TTS provider works
- [ ] GUI audio controls functional
- [ ] All methods ≤20 LOC
- [ ] Tests pass
- [ ] Ruff check passes
- [ ] Pyright check passes

**Expected Completion:** 2025-12-09

---

## Phase 4: Excel Export (Optional)

**Goal:** Enable export of translations to Excel format
**Priority:** MEDIUM
**Estimated Duration:** 3-5 days (6-8 hours)

### 4.1 Excel Storage Provider (4-5 hours)

**Files:** `src/birkenbihl/storage/excel_storage.py`

**Tasks:**
- [ ] **4.1.1** Create `ExcelStorageProvider`
  - Implements `IStorageProvider` (read-only or write-only)
  - Uses `openpyxl` or `xlsxwriter`
  - Methods: `export_translation()`, `export_all()`
  - Max 20 LOC per method

- [ ] **4.1.2** Define Excel format
  - Sheet 1: Translation metadata (title, languages, dates)
  - Sheet 2: Sentences (source text, natural translation, word-by-word)
  - Sheet 3: Word alignments (source word, target word, position)
  - Formatting: headers bold, borders, colors

- [ ] **4.1.3** Implement export logic
  - Translation → Excel workbook
  - Multiple sheets for different data
  - Proper formatting

- [ ] **4.1.4** Add unit tests
- [ ] **4.1.5** Run Pyright + Ruff validation
- [ ] **4.1.6** Commit: "feat(storage): Add Excel export provider"

**Success Criteria:**
- Excel files generated correctly
- Formatting is clean
- All methods ≤20 LOC
- Tests pass

---

### 4.2 CLI/GUI Integration (2 hours)

**Files:** `src/birkenbihl/cli.py`, GUI views

**Tasks:**
- [ ] **4.2.1** Add `export` CLI command
  - `birkenbihl export <translation-id> --format excel --output file.xlsx`
  - Calls ExcelStorageProvider

- [ ] **4.2.2** Add export button to GUI
  - Translation list view → Export selected
  - File dialog for save location

- [ ] **4.2.3** Add integration tests
- [ ] **4.2.4** Run Pyright + Ruff validation
- [ ] **4.2.5** Commit: "feat(cli,gui): Add Excel export command and button"

**Success Criteria:**
- Export works from CLI and GUI
- User can choose file location
- Tests pass

---

### Phase 4 Completion Checklist

- [ ] Excel export functional
- [ ] CLI and GUI integration complete
- [ ] All methods ≤20 LOC
- [ ] Tests pass
- [ ] Ruff check passes
- [ ] Pyright check passes

**Expected Completion:** TBD (Optional)

---

## Progress Tracking

### Completed Tasks

**2025-11-04 - Initial Setup & Cleanup:**
- [x] Created PROJECT_PROGRESS.md work plan
- [x] Defined 4 phases with detailed tasks
- [x] Established code quality standards and checklists
- [x] Fixed Pyright errors - removed all missing imports from __init__ files
  - Cleaned up gui/components/__init__.py
  - Cleaned up gui/controllers/__init__.py
  - Cleaned up gui/hooks/__init__.py
  - Cleaned up gui/viewmodels/__init__.py (removed create_vm import)
  - Cleaned up gui/widgets/__init__.py (removed non-existent widgets)
- [x] Simplified main_window.py to only use SettingsView (removed legacy views)
- [x] Created missing ui_state.py with SettingsViewState dataclass
- [x] Created language_combo.py as alias for LanguageSelector
- [x] Fixed all Ruff E501 errors (lines >120 chars):
  - models/validation.py - split long error message
  - providers/prompts.py - split long prompt rules
  - tests/integration/test_birkenbihl_unit1_1.py - extracted variables
  - tests/integration/test_settings_workflow.py - multi-line ProviderConfig
  - tests/integration/test_spanish_sentence_alignment.py - split docstring
- [x] Fixed pytest warnings (PT011, PT012):
  - Added match parameter to pytest.raises(ValueError)
  - Refactored pytest.raises blocks to single statement
- [x] **All Ruff checks passing ✅**
- [x] **Pyright errors reduced** (only warnings and test errors remain)

### Next Steps

1. Start Phase 1.1: Refactor SqliteStorageProvider
2. Follow pre-commit checklist for every commit
3. Update this document after each completed task

---

## Metrics Dashboard

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Functions ≤20 LOC | 87% | 100% | 🟡 In Progress |
| Parameters ≤2 | 88% | 100% | 🟡 In Progress |
| Test Coverage | 80%+ | 80%+ | ✅ Met |
| SOLID Compliance | 4.7/5 | 5/5 | 🟡 In Progress |
| DRY Compliance | 80% | 95%+ | 🟡 In Progress |
| Architecture Score | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Met |
| Feature Completeness | 60% | 100% | 🔴 Critical Missing |

---

## Notes & Decisions

### 2025-11-04 - Initial Planning
- Decided to prioritize code quality (Phase 1) before new features
- Word Alignment Editor identified as most critical missing feature
- AudioService deferred to Phase 3 (can be released without it initially)
- Excel export marked as optional (nice-to-have)

### 2025-11-04 - Translation Architecture Decision
- **Added Phase 1.6**: Two-Step Translation Refactoring (user request)
- **Problem identified**: Current implementation uses single prompt for both natural translation + word alignment
- **Research findings**:
  - NLP best practice (2024): Word alignment is separate task AFTER translation (BinaryAlign, TransAlign)
  - Original Birkenbihl method: 4 separate steps, decoding is intentionally separate
  - Current approach violates both principles
- **Decision**: Split into two-step process:
  - Step 1: Generate natural translation only
  - Step 2: Generate word alignments based on natural translation + word lists
- **Benefits**:
  - Follows state-of-the-art NLP practices
  - Aligns with original Birkenbihl pedagogy
  - User can edit natural translation before alignment
  - Better control over translation quality
  - Easier debugging (isolate which step fails)
- **Trade-off**: Two API calls vs one (acceptable for quality improvement)
- **Implementation note**: Existing `create_word_by_word_prompt()` and `regenerate_alignment()` already implement parts of Step 2

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Qt library issues in test environment | Medium | Low | Use mocked tests, manual UI testing |
| TTS provider API changes | Medium | Low | Abstract behind IAudioProvider protocol |
| Word Alignment Editor complexity | High | Medium | Break into small widgets, iterative testing |
| Scope creep | High | Medium | Stick to defined phases, no new features |

---

## References

- **CLAUDE.md** - Project overview and code standards
- **specs/02_CORE_CODE_ANALYSIS.md** - Detailed code analysis (Oct 2025)
- **specs/03_GUI_CODE_ANALYSIS.md** - GUI analysis
- **specs/04_CORE_GUI_ALIGNMENT.md** - Integration strategy

---

**Last Updated:** 2025-11-04 (Planning phase complete)
