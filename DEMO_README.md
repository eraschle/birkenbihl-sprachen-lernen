# Word Alignment Editor Demo

This demo showcases the Birkenbihl Word Alignment Editor implementation.

## Features Demonstrated

✅ **Visual Drag-and-Drop Interface**
- Interleaved grid layout with source words as column headers
- Target words displayed vertically below each source word
- Drag words between columns to change alignments
- Visual feedback during drag operations

✅ **Real-Time Validation**
- Instant validation as you edit
- Clear error messages for empty columns and unassigned words
- Save button enabled only when alignment is valid

✅ **Multiple Word Assignment**
- Assign multiple target words to one source word
- Automatically joined with hyphens (e.g., "werde-vermissen")
- Handle complex word order changes between languages

✅ **Persistence**
- Changes saved through TranslationService
- Verification of persistence by reloading from storage
- Uses JSON file storage for demo

✅ **Three Example Scenarios**

1. **Simple Alignment** (EN→DE)
   - "The cat sat on the mat" → "Die Katze saß auf der Matte"
   - Demonstrates 1:1 word alignment

2. **Word Order Changes** (EN→DE)
   - "I will miss you" → "Ich werde dich vermissen"
   - Shows how word order differs between English and German

3. **Hyphenated Words** (ES→DE)
   - "Yo te extrañaré" → "Ich werde dich vermissen"
   - Demonstrates multi-word alignment (extrañaré → werde-vermissen)

## Running the Demo

### Prerequisites

```bash
# Install dependencies
uv sync
```

### Launch Demo

```bash
# Run with uv
uv run python demo_alignment_editor.py

# Or if birkenbihl is installed
python demo_alignment_editor.py
```

## How to Use

1. **Select an Example**: Click one of the three example buttons at the top
2. **View Current Alignment**: See source words as columns, target words below
3. **Edit Alignment**:
   - Click and drag target words between columns
   - Drop words in different columns to reassign them
   - Drop words in the "Unassigned Pool" to remove from alignment
4. **Validate**: Watch the validation panel at bottom
   - ✅ Green: Valid alignment, ready to save
   - ⚠️ Yellow: Issues detected (empty columns, unassigned words)
5. **Save**: Click "💾 Save" when valid to persist changes
6. **Reset**: Click "↺ Reset" to restore original alignment

## Architecture Highlights

### MVVM Pattern

```
InterleavedAlignmentEditor (View)
         ↕ signals
AlignmentEditorViewModel (ViewModel)
         ↕
TranslationService (Service)
         ↕
JsonStorageProvider (Storage)
```

### Components Used

- **AlignmentEditorViewModel**: State management, validation, business logic
- **InterleavedAlignmentEditor**: Main view composing all widgets
- **AlignmentGrid**: Grid container with columns
- **AlignmentColumn**: Single column for one source word
- **DraggableWordTag**: Draggable word chips
- **UnassignedWordsPool**: Pool for unassigned words
- **TranslationService**: Orchestrates persistence
- **JsonStorageProvider**: File-based storage

### Key Features

**Signal-Based Communication**
- `state_changed` → Update view when state changes
- `validation_changed` → Update validation panel
- `save_requested` → Trigger save through service
- `word_moved` → Update ViewModel when user drags

**Clean Code**
- All functions ≤20 LOC
- Single Responsibility Principle
- Protocol-based dependency injection

**Type Safety**
- Python 3.13+ type hints throughout
- Passes Pyright strict type checking

## Testing

The demo uses temporary storage that is cleaned up on exit.

To test with real storage:

```python
from birkenbihl.storage.json_storage import JsonStorageProvider

storage = JsonStorageProvider("my_translations.json")
service = TranslationService(translator=None, storage=storage)
```

## Integration with Full Application

In production, integrate as follows:

```python
# In your main window/view
from birkenbihl.gui.viewmodels import AlignmentEditorViewModel
from birkenbihl.gui.views.alignment_editor_view import InterleavedAlignmentEditor

# Create ViewModel
viewmodel = AlignmentEditorViewModel()

# Create Editor
editor = InterleavedAlignmentEditor(viewmodel)

# Load sentence from translation
translation = translation_service.get_translation(translation_id)
sentence = translation.sentences[sentence_index]
editor.load_sentence(sentence)

# Connect save signal
editor.save_requested.connect(
    lambda alignments: translation_service.update_sentence_alignment(
        translation_id, sentence.uuid, alignments
    )
)

# Add to your layout
layout.addWidget(editor)
```

## Known Limitations

- **No AI Integration**: Demo uses static examples
  - Regenerate button shows info dialog
  - In production, connect to TranslationService.update_sentence_natural()

- **Single Sentence**: Demo edits one sentence at a time
  - In production, iterate through translation.sentences

- **Temporary Storage**: Uses temp directory
  - In production, use persistent JsonStorageProvider or SqliteStorageProvider

## Next Steps

See `specs/ALIGNMENT_EDITOR_USAGE.md` for complete integration guide.

**Phase 3 - AudioService** (Coming Next)
- Text-to-speech for source language
- Sentence-by-sentence playback
- Active listening phase of Birkenbihl method
