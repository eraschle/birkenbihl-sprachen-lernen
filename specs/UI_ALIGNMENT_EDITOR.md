# Word Alignment Editor - Technical Specification

**Status:** Phase 2 - Implementation
**Priority:** CRITICAL
**Created:** 2025-11-05
**Architecture Pattern:** MVVM (Model-View-ViewModel)

---

## 1. Overview

The Word Alignment Editor is the core UI component of the Birkenbihl language learning method. It provides an **interleaved grid layout** where users can visually map source words to target words through drag-and-drop interaction.

### Core Concept: Interleaved Grid Layout

```
┌────────────────────────────────────┐
│  The   cat    sat                  │  ← Original words (fixed)
│   │     │     │                     │  ← Visual connections
│  Die   Katze  saß                  │  ← Translated words (draggable)
└────────────────────────────────────┘
```

**Key Principles:**
- **1 Original Word = 1 Column**: Each source word gets its own column
- **Vertical Stacking**: Multiple target words stack vertically under one source word
- **Drag-and-Drop**: Target words can be dragged between columns
- **Validation**: All columns must have at least one target word before saving

---

## 2. Architecture

### 2.1 MVVM Pattern

```
┌──────────────────────────────────────────────────────┐
│                    Domain Model                       │
│  - Sentence (source_text, natural_translation)       │
│  - WordAlignment (source_word, target_word, position)│
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│              AlignmentEditorViewModel                 │
│  State:                                               │
│  - current_sentence: Sentence                         │
│  - source_words: list[str]                           │
│  - assigned_words: dict[int, list[str]]              │
│  - unassigned_words: list[str]                       │
│                                                       │
│  Signals (Qt):                                        │
│  - alignment_changed(position, words)                 │
│  - validation_changed(is_valid, errors)               │
│  - word_assigned(word, column)                        │
│  - word_unassigned(word, column)                      │
│                                                       │
│  Methods:                                             │
│  - load_sentence(sentence)                            │
│  - assign_word(word, column_index)                    │
│  - unassign_word(word, column_index)                  │
│  - validate() -> (bool, list[str])                    │
│  - to_word_alignments() -> list[WordAlignment]        │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│         InterleavedAlignmentEditor (View)             │
│  Components:                                          │
│  - AlignmentGrid (interleaved columns)                │
│  - UnassignedWordsPool (target words not assigned)    │
│  - ValidationPanel (error/warning messages)           │
│  - Toolbar (Save, Reset, Regenerate actions)          │
└──────────────────────────────────────────────────────┘
```

### 2.2 Widget Hierarchy

```
InterleavedAlignmentEditor (QWidget)
├── Toolbar (QToolBar)
│   ├── SaveButton
│   ├── ResetButton
│   └── RegenerateButton
├── AlignmentGrid (QWidget)
│   └── AlignmentColumn[] (one per source word)
│       ├── SourceWordLabel (QLabel, fixed)
│       ├── ConnectionLine (QWidget, optional)
│       └── DropZone (QWidget)
│           └── DraggableWordTag[] (stacked vertically)
├── UnassignedWordsPool (QWidget)
│   ├── SourceWordsPool (read-only, for reference)
│   └── TargetWordsPool (draggable words not yet assigned)
└── ValidationPanel (QWidget)
    └── ValidationMessages (QLabel or QListWidget)
```

---

## 3. Component Specifications

### 3.1 DraggableWordTag

**Purpose:** Displays a single word that can be dragged between columns.

**Visual States:**
- **Normal**: Light gray background, rounded corners
- **Hover**: Slightly darker background
- **Dragging**: Semi-transparent, cursor changes to "grabbing"
- **Invalid**: Red border (if validation fails)

**Interface:**
```python
class DraggableWordTag(QWidget):
    """Draggable word chip for alignment editor.

    Signals:
        drag_started(str): Emitted when drag begins
        drag_ended(str): Emitted when drag ends
        clicked(): Emitted on click (keyboard alternative)
    """

    def __init__(self, word: str, tag_type: TagType):
        """Initialize tag.

        Args:
            word: Text to display
            tag_type: SOURCE or TARGET
        """

    def set_state(self, state: TagState) -> None:
        """Update visual state (Normal, Hover, Dragging, Invalid)."""

    def start_drag(self) -> None:
        """Initiate drag operation with QDrag."""

    def get_word(self) -> str:
        """Return the word text."""
```

**Clean Code Requirements:**
- All methods ≤20 LOC
- No business logic (delegates to parent)
- Emits signals for interactions

**Styling:**
- Border-radius: 4px
- Padding: 5px 10px
- Background: #f0f0f0 (normal), #e0e0e0 (hover)
- Box-shadow: 0 2px 4px rgba(0,0,0,0.1)
- Font: 11pt sans-serif
- Cursor: grab → grabbing

---

### 3.2 AlignmentDropZone

**Purpose:** Accept dropped words and provide visual feedback during drag operations.

**Visual States:**
- **Hidden**: Not visible during normal state
- **Active**: Semi-transparent blue background with dashed border (during drag)
- **Hover**: Solid blue border and brighter background (when word hovers over)
- **Error**: Red background (when column has no words)

**Interface:**
```python
class AlignmentDropZone(QWidget):
    """Drop zone for word alignment columns.

    Signals:
        word_dropped(str, int): Emitted when word dropped (word, column_index)
        hover_entered(int): Emitted when drag enters zone
        hover_exited(int): Emitted when drag leaves zone
    """

    def __init__(self, column_index: int):
        """Initialize drop zone.

        Args:
            column_index: Index of this column in grid
        """

    def set_active(self, active: bool) -> None:
        """Show/hide drop zone during drag operations."""

    def set_highlight(self, highlight: bool) -> None:
        """Highlight zone when word hovers over."""

    def set_error(self, error: bool) -> None:
        """Mark zone as error (empty column)."""

    def accept_drop(self, word: str) -> bool:
        """Validate and accept dropped word."""
```

**Clean Code Requirements:**
- Validation logic in ViewModel, not widget
- All methods ≤20 LOC
- Clear visual feedback for each state

**Styling:**
- Active: background rgba(0, 150, 255, 0.1), border 2px dashed #0096ff
- Hover: background rgba(0, 150, 255, 0.2), border 2px solid #0096ff
- Error: background rgba(255, 0, 0, 0.05), border 2px solid #ff0000

---

### 3.3 AlignmentColumn

**Purpose:** Container for one source word and its aligned target words.

**Layout:**
```
┌─────────────┐
│   Source    │  ← Fixed header (QLabel)
├─────────────┤
│   ┌───────┐ │  ← Drop zone (visible during drag)
│   │  die  │ │  ← First target word tag
│   ├───────┤ │
│   │  der  │ │  ← Second target word tag (stacked)
│   └───────┘ │
└─────────────┘
```

**Interface:**
```python
class AlignmentColumn(QWidget):
    """Single column in interleaved alignment grid.

    Contains one source word (fixed header) and multiple
    target words (draggable tags) stacked vertically.

    Signals:
        word_added(str, int): Word added to column
        word_removed(str, int): Word removed from column
    """

    def __init__(self, source_word: str, column_index: int):
        """Initialize column.

        Args:
            source_word: Original word to display in header
            column_index: Position in grid (0-indexed)
        """

    def add_word(self, word: str) -> None:
        """Add target word tag to column (stacks vertically)."""

    def remove_word(self, word: str) -> None:
        """Remove target word tag from column."""

    def get_words(self) -> list[str]:
        """Return all target words in this column."""

    def is_empty(self) -> bool:
        """Check if column has no target words."""

    def set_error_state(self, error: bool) -> None:
        """Highlight column header if empty (validation error)."""
```

**Clean Code Requirements:**
- Vertical layout managed by QVBoxLayout
- All methods ≤20 LOC
- No validation logic (delegates to ViewModel)

---

### 3.4 UnassignedWordsPool

**Purpose:** Container for target words not yet assigned to any column.

**Layout:**
```
┌─────────────────────────────────────────┐
│  Unassigned Words (3)                   │
├─────────────────────────────────────────┤
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │  und  │ │  aber │ │  auch │         │
│  └───────┘ └───────┘ └───────┘         │
└─────────────────────────────────────────┘
```

**Interface:**
```python
class UnassignedWordsPool(QWidget):
    """Pool of target words not assigned to source words.

    Words can be dragged from pool to alignment columns.
    Pool should be empty for valid alignment.

    Signals:
        word_count_changed(int): Emitted when pool size changes
        pool_emptied(): Emitted when last word removed
    """

    def __init__(self):
        """Initialize empty pool."""

    def add_word(self, word: str) -> None:
        """Add word to pool."""

    def remove_word(self, word: str) -> None:
        """Remove word from pool."""

    def set_words(self, words: list[str]) -> None:
        """Replace all words in pool."""

    def get_words(self) -> list[str]:
        """Return all words in pool."""

    def clear(self) -> None:
        """Remove all words from pool."""

    def is_empty(self) -> bool:
        """Check if pool has no words."""
```

**Clean Code Requirements:**
- Flow layout for horizontal word arrangement (QFlowLayout)
- All methods ≤20 LOC
- Emits signals for state changes

**Styling:**
- Border: 1px solid #ccc
- Padding: 10px
- Background: #fafafa
- Min-height: 80px

---

### 3.5 AlignmentGrid

**Purpose:** Container for all alignment columns in interleaved layout.

**Interface:**
```python
class AlignmentGrid(QWidget):
    """Interleaved grid of alignment columns.

    Each column represents one source word with vertically
    stacked target words.

    Signals:
        grid_changed(): Emitted when any column changes
        validation_needed(): Emitted after user interaction
    """

    def __init__(self):
        """Initialize empty grid."""

    def build_grid(self, source_words: list[str], alignments: dict[int, list[str]]) -> None:
        """Build grid from source words and alignments."""

    def add_column(self, source_word: str, target_words: list[str]) -> None:
        """Add single column to grid."""

    def get_column(self, index: int) -> AlignmentColumn:
        """Get column by index."""

    def clear_grid(self) -> None:
        """Remove all columns."""

    def get_alignments(self) -> dict[int, list[str]]:
        """Extract current alignments as dict[position, words]."""
```

**Clean Code Requirements:**
- Horizontal layout for columns (QHBoxLayout)
- All methods ≤20 LOC
- Delegates word management to AlignmentColumn

**Styling:**
- Display: Horizontal scroll if >10 columns
- Column spacing: 0px (columns have borders)
- Min-width per column: 80px
- Max-width per column: 200px

---

### 3.6 AlignmentEditorViewModel

**Purpose:** Manage state and business logic for word alignment editing.

**State:**
```python
@dataclass
class AlignmentState:
    """Current state of alignment editor."""
    source_words: list[str]
    assigned_words: dict[int, list[str]]  # column_index -> words
    unassigned_words: list[str]
    is_valid: bool
    validation_errors: list[str]
    is_dirty: bool  # Has unsaved changes
```

**Interface:**
```python
class AlignmentEditorViewModel(BaseViewModel):
    """ViewModel for word alignment editor.

    Manages state for mapping target words to source words.
    Follows MVVM pattern with Qt signals for view updates.

    Signals (inherited from BaseViewModel):
        error_occurred(str)
        loading_changed(bool)

    New Signals:
        alignment_changed()
        validation_changed(bool, list[str])
        state_changed(AlignmentState)
    """

    def load_sentence(self, sentence: Sentence) -> None:
        """Load sentence and initialize alignment state."""

    def assign_word(self, word: str, column_index: int) -> None:
        """Assign target word to source word column."""

    def unassign_word(self, word: str, column_index: int) -> None:
        """Remove target word from column."""

    def validate(self) -> tuple[bool, list[str]]:
        """Validate current alignment state."""

    def to_word_alignments(self) -> list[WordAlignment]:
        """Convert current state to WordAlignment domain models."""

    def reset(self) -> None:
        """Reset to original alignment from sentence."""
```

**Validation Rules:**
1. All source words must have at least one target word
2. All target words must be assigned to a column
3. Unassigned pool must be empty
4. No duplicate target words across columns

**Clean Code Requirements:**
- All methods ≤20 LOC
- No UI logic (delegates to view via signals)
- Follows Single Responsibility Principle

---

### 3.7 InterleavedAlignmentEditor (Main View)

**Purpose:** Top-level widget composing all components.

**Interface:**
```python
class InterleavedAlignmentEditor(QWidget):
    """Complete word alignment editor with interleaved grid.

    Composes AlignmentGrid, UnassignedWordsPool, toolbar,
    and validation panel into single widget.

    Signals:
        save_requested(list[WordAlignment])
        cancel_requested()
        regenerate_requested()
    """

    def __init__(self, viewmodel: AlignmentEditorViewModel):
        """Initialize editor with viewmodel.

        Args:
            viewmodel: ViewModel managing state
        """

    def setup_ui(self) -> None:
        """Build UI layout and widgets."""

    def bind_viewmodel(self) -> None:
        """Connect ViewModel signals to view slots."""

    def load_sentence(self, sentence: Sentence) -> None:
        """Load sentence into editor."""

    def on_save_clicked(self) -> None:
        """Handle save button click."""

    def on_reset_clicked(self) -> None:
        """Handle reset button click."""

    def on_regenerate_clicked(self) -> None:
        """Handle regenerate button click."""
```

**Layout:**
```
┌──────────────────────────────────────────┐
│  Toolbar: [Save] [Reset] [Regenerate AI] │
├──────────────────────────────────────────┤
│  AlignmentGrid (scrollable horizontal)    │
│  ┌────┬────┬────┬────┐                   │
│  │The │cat │sat │... │                   │
│  ├────┼────┼────┼────┤                   │
│  │Die │Kat-│saß │    │                   │
│  │    │ze  │    │    │                   │
│  └────┴────┴────┴────┘                   │
├──────────────────────────────────────────┤
│  Unassigned Words (2):                    │
│  [und] [aber]                             │
├──────────────────────────────────────────┤
│  Validation:                              │
│  ⚠️ 2 words not assigned                 │
│  🔴 Column 'sat' has no translation       │
└──────────────────────────────────────────┘
```

**Clean Code Requirements:**
- All methods ≤20 LOC
- Delegation to child widgets
- Clear separation of concerns

---

## 4. Data Flow

### 4.1 Loading Sentence

```
Sentence (domain model)
    ↓
AlignmentEditorViewModel.load_sentence()
    ↓ tokenize source_text and natural_translation
    ↓ build assigned_words dict from WordAlignment list
    ↓ emit state_changed signal
    ↓
InterleavedAlignmentEditor receives signal
    ↓
AlignmentGrid.build_grid(source_words, alignments)
    ↓ creates AlignmentColumn for each source word
    ↓ populates columns with DraggableWordTag widgets
    ↓
UnassignedWordsPool.set_words(unassigned)
    ↓ displays remaining unassigned words
```

### 4.2 Drag-and-Drop Word

```
User drags word from column A to column B
    ↓
DraggableWordTag.start_drag() emits drag_started
    ↓
AlignmentGrid shows all drop zones
    ↓
User drops word on AlignmentDropZone(column_index=B)
    ↓
AlignmentDropZone.accept_drop() emits word_dropped(word, B)
    ↓
AlignmentColumn(B) handles signal:
    ↓ calls AlignmentColumn(A).remove_word()
    ↓ calls AlignmentColumn(B).add_word()
    ↓ emits word_added/word_removed signals
    ↓
InterleavedAlignmentEditor propagates to ViewModel
    ↓
AlignmentEditorViewModel.unassign_word(word, A)
AlignmentEditorViewModel.assign_word(word, B)
    ↓ updates internal state
    ↓ validates new state
    ↓ emits alignment_changed + validation_changed
    ↓
View updates validation panel
```

### 4.3 Saving Alignment

```
User clicks Save button
    ↓
InterleavedAlignmentEditor.on_save_clicked()
    ↓ calls viewmodel.validate()
    ↓ if valid:
        ↓ alignments = viewmodel.to_word_alignments()
        ↓ emit save_requested(alignments)
    ↓ else:
        ↓ show validation errors in panel
        ↓ highlight error columns
```

---

## 5. Validation Rules

### 5.1 Column Validation

Each column must have **at least one target word**.

**Error Message:**
`"Source word '{source_word}' has no translation"`

**Visual Feedback:**
- Column header text turns red
- Drop zone has red border
- Error icon in validation panel

### 5.2 Unassigned Words

All target words must be assigned to a column.

**Warning Message:**
`"{count} words not assigned: {word_list}"`

**Visual Feedback:**
- Unassigned pool highlighted with yellow border
- Warning icon in validation panel
- Save button disabled

### 5.3 Complete Validation

**Valid State:**
- ✅ All source words have ≥1 target word
- ✅ Unassigned pool is empty
- ✅ No duplicate words across columns
- ✅ Save button enabled

**Invalid State:**
- 🔴 At least one source word has no target words → **Error**
- ⚠️ Unassigned pool not empty → **Warning**
- 🔴 Duplicate target words → **Error**
- ❌ Save button disabled

---

## 6. User Workflows

### 6.1 Edit AI-Generated Alignment

1. User clicks "Translate" in main window
2. AI generates natural translation + word alignments
3. Alignment editor opens with pre-populated grid
4. User reviews alignment
5. User drags incorrect word from column A to column B
6. Grid updates, validation recomputes
7. User clicks Save
8. Alignment persisted to database

### 6.2 Manual Alignment Creation

1. User inputs source text and target text manually
2. System tokenizes both texts
3. Alignment editor opens with empty columns
4. All target words in unassigned pool
5. User drags each word to appropriate column
6. Validation shows progress (e.g., "5 of 10 columns filled")
7. User fills all columns
8. Save button enables
9. User clicks Save

### 6.3 Regenerate Alignment with AI

1. User edits natural translation in text field
2. Clicks "Regenerate Alignment" button
3. AI receives:
   - source_text
   - updated natural_translation
   - source_words list
   - target_words list
4. AI generates new word alignments
5. Grid refreshes with new alignment
6. User can further edit or save

---

## 7. Testing Strategy

### 7.1 Unit Tests

**DraggableWordTag:**
- Test drag initiation
- Test state changes (normal → hover → dragging)
- Test signal emissions

**AlignmentColumn:**
- Test add_word() stacks vertically
- Test remove_word() updates list
- Test is_empty() validation
- Test error state highlighting

**AlignmentEditorViewModel:**
- Test load_sentence() parses correctly
- Test assign_word() updates state
- Test validate() catches all error types
- Test to_word_alignments() creates correct models

### 7.2 Integration Tests

**Drag-and-Drop Workflow:**
- Drag word from column A to column B → updates both columns
- Drag word from column to unassigned pool → removes from column
- Drag word from pool to column → adds to column

**Validation:**
- Empty column → shows error
- Fill column → error clears
- Empty unassigned pool → save enabled
- Non-empty pool → save disabled

**Save Workflow:**
- Valid alignment → emits save_requested with correct WordAlignment list
- Invalid alignment → shows errors, prevents save

---

## 8. Implementation Phases

### Phase 2.1: Architecture & Design ✅ (Current Phase)
- Define UI requirements
- Create widget hierarchy
- Define MVVM data flow
- Document specifications

### Phase 2.2: Base Widgets (4-5 hours)
- Implement DraggableWordTag
- Implement AlignmentDropZone
- Implement UnassignedWordsPool
- Add unit tests
- **Commit:** "feat(gui): Add base widgets for word alignment"

### Phase 2.3: Alignment Grid (3-4 hours)
- Implement AlignmentColumn
- Implement AlignmentGrid
- Add keyboard navigation
- Add unit tests
- **Commit:** "feat(gui): Add AlignmentGrid with interleaved layout"

### Phase 2.4: ViewModel (2-3 hours)
- Implement AlignmentEditorViewModel
- Add state management
- Add validation logic
- Add unit tests
- **Commit:** "feat(gui): Add AlignmentEditorViewModel with state management"

### Phase 2.5: Main Editor View (3-4 hours)
- Implement InterleavedAlignmentEditor
- Connect all components
- Add toolbar actions
- Add integration tests
- **Commit:** "feat(gui): Add InterleavedAlignmentEditor view"

### Phase 2.6: Service Integration (2 hours)
- Add TranslationService.update_sentence_alignment()
- Connect editor to service
- Persist changes to storage
- **Commit:** "feat(gui): Integrate AlignmentEditor with TranslationService"

---

## 9. Success Criteria

### Functional Requirements
- ✅ Users can drag target words between columns
- ✅ Words stack vertically in columns
- ✅ Visual feedback during drag operations
- ✅ Validation prevents invalid alignments
- ✅ Save button only enabled when valid
- ✅ Alignments persist to database

### Non-Functional Requirements
- ✅ All functions ≤20 LOC (Clean Code compliance)
- ✅ All parameters ≤2 per function
- ✅ MVVM pattern followed strictly
- ✅ Type hints on all methods
- ✅ Unit test coverage ≥80%
- ✅ Pyright + Ruff validation passes

### User Experience
- ✅ Intuitive drag-and-drop interaction
- ✅ Clear visual feedback for all states
- ✅ Helpful error messages
- ✅ Responsive to user actions (<100ms)
- ✅ Works with long words and sentences

---

## 10. References

- **UI Concept (German):** `specs/UI Konzept/wortzuordnung_konzept.md`
- **Quick Reference (German):** `specs/UI Konzept/interleaved_quick_reference.md`
- **MVVM Pattern:** `src/birkenbihl/gui/viewmodels/base.py`
- **Widget Protocol:** `src/birkenbihl/gui/widgets/base.py`
- **Domain Models:** `src/birkenbihl/models/translation.py`

---

**Next Step:** Phase 2.2 - Implement Base Widgets
