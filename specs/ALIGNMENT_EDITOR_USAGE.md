# Word Alignment Editor - Usage Guide

## Overview

The Word Alignment Editor allows users to manually edit word-by-word alignments for translated sentences using an intuitive drag-and-drop interface.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Parent View / Window                     │
│  ┌────────────────────────────────────────────────────┐  │
│  │         InterleavedAlignmentEditor                  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │        AlignmentEditorViewModel              │  │  │
│  │  │  (Manages state, validation, conversions)    │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │           AlignmentGrid                      │  │  │
│  │  │  (Interleaved columns with drag-drop)        │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │       UnassignedWordsPool                    │  │  │
│  │  │  (Words not yet assigned to columns)         │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                      ↓ save_requested signal              │
│  ┌────────────────────────────────────────────────────┐  │
│  │           TranslationService                       │  │
│  │  update_sentence_alignment(translation_id,         │  │
│  │                            sentence_uuid,          │  │
│  │                            alignments)             │  │
│  └────────────────────────────────────────────────────┘  │
│                      ↓                                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │           StorageProvider                          │  │
│  │  (Persists updated alignment to database/file)    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Basic Usage

### 1. Create the Editor

```python
from birkenbihl.gui.viewmodels import AlignmentEditorViewModel
from birkenbihl.gui.views.alignment_editor_view import InterleavedAlignmentEditor
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.models.translation import Sentence, WordAlignment

# Create ViewModel
viewmodel = AlignmentEditorViewModel()

# Create Editor View
editor = InterleavedAlignmentEditor(viewmodel)

# Connect signals
editor.save_requested.connect(on_save_alignment)
editor.cancel_requested.connect(on_cancel)
editor.regenerate_requested.connect(on_regenerate_ai)
```

### 2. Load a Sentence

```python
# Get sentence from translation
translation = translation_service.get_translation(translation_id)
sentence = translation.sentences[0]  # First sentence

# Load into editor
editor.load_sentence(sentence)
```

The editor will automatically:
- Tokenize source_text and natural_translation
- Build grid with existing alignments
- Show unassigned words in pool
- Validate current state

### 3. Handle Save

```python
def on_save_alignment(alignments: list[WordAlignment]) -> None:
    """Handle save button clicked.

    Args:
        alignments: List of WordAlignment objects from editor
    """
    try:
        # Update sentence alignment in service
        updated_translation = translation_service.update_sentence_alignment(
            translation_id=current_translation_id,
            sentence_uuid=current_sentence_uuid,
            alignments=alignments
        )

        # Show success message
        show_success("Alignment saved successfully!")

        # Optionally reload editor with updated translation
        sentence = next(s for s in updated_translation.sentences if s.uuid == current_sentence_uuid)
        editor.load_sentence(sentence)

    except ValueError as e:
        # Validation failed
        show_error(f"Invalid alignment: {e}")
    except NotFoundError as e:
        # Translation or sentence not found
        show_error(f"Not found: {e}")
```

### 4. Handle Regenerate

```python
def on_regenerate_ai(sentence: Sentence) -> None:
    """Handle regenerate button clicked.

    Args:
        sentence: Sentence to regenerate alignment for
    """
    try:
        # Call service to regenerate alignment with AI
        updated_translation = translation_service.update_sentence_natural(
            translation_id=current_translation_id,
            sentence_uuid=sentence.uuid,
            new_natural=sentence.natural_translation,
            provider=current_provider_config
        )

        # Reload editor with AI-generated alignment
        sentence = next(s for s in updated_translation.sentences if s.uuid == sentence.uuid)
        editor.load_sentence(sentence)

    except Exception as e:
        show_error(f"Regeneration failed: {e}")
```

## Complete Example

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from birkenbihl.gui.viewmodels import AlignmentEditorViewModel
from birkenbihl.gui.views.alignment_editor_view import InterleavedAlignmentEditor
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.sqlite_storage import SqliteStorageProvider
from uuid import UUID

class AlignmentEditorWindow(QMainWindow):
    """Window for editing word alignments."""

    def __init__(self, translation_service: TranslationService):
        super().__init__()
        self.translation_service = translation_service
        self.current_translation_id: UUID | None = None
        self.current_sentence_uuid: UUID | None = None

        # Create ViewModel and View
        self.viewmodel = AlignmentEditorViewModel()
        self.editor = InterleavedAlignmentEditor(self.viewmodel)

        # Connect signals
        self.editor.save_requested.connect(self.on_save)
        self.editor.cancel_requested.connect(self.close)

        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.editor)
        self.setCentralWidget(central_widget)

        self.setWindowTitle("Word Alignment Editor")
        self.resize(1200, 600)

    def load_translation_sentence(self, translation_id: UUID, sentence_uuid: UUID):
        """Load sentence for editing.

        Args:
            translation_id: Translation UUID
            sentence_uuid: Sentence UUID within translation
        """
        self.current_translation_id = translation_id
        self.current_sentence_uuid = sentence_uuid

        # Load from service
        translation = self.translation_service.get_translation(translation_id)
        if not translation:
            return

        sentence = next((s for s in translation.sentences if s.uuid == sentence_uuid), None)
        if not sentence:
            return

        # Load into editor
        self.editor.load_sentence(sentence)

    def on_save(self, alignments: list):
        """Handle save."""
        if not self.current_translation_id or not self.current_sentence_uuid:
            return

        try:
            updated = self.translation_service.update_sentence_alignment(
                translation_id=self.current_translation_id,
                sentence_uuid=self.current_sentence_uuid,
                alignments=alignments
            )
            print(f"Saved alignment for sentence {self.current_sentence_uuid}")
            self.close()

        except Exception as e:
            print(f"Save failed: {e}")

# Usage
if __name__ == "__main__":
    app = QApplication([])

    # Setup service
    storage = SqliteStorageProvider("translations.db")
    service = TranslationService(None, storage)

    # Create window
    window = AlignmentEditorWindow(service)

    # Load specific translation/sentence
    window.load_translation_sentence(
        translation_id=UUID("..."),
        sentence_uuid=UUID("...")
    )

    window.show()
    app.exec()
```

## User Workflow

### Editing Alignment

1. **Load Sentence**: Grid shows source words as column headers, target words stacked below
2. **Review**: User sees current alignment
3. **Drag Words**: User can drag target words between columns
   - From pool → column: Assign unassigned word
   - From column → column: Move word to different source
   - From column → pool: Unassign word
4. **Validation**: Real-time feedback shows:
   - ✅ Green: All columns have words, no unassigned
   - ⚠️ Yellow: Empty columns or unassigned words remain
5. **Save**: Button enabled only when valid

### States

```
Initial Load:
┌─────────────────────────────────────────┐
│  The   cat    sat                       │
│   │     │     │                          │
│  Die   Katze  saß                       │
└─────────────────────────────────────────┘
Unassigned: []
Status: ✅ Ready to save

After Drag (Invalid):
┌─────────────────────────────────────────┐
│  The   cat    sat                       │
│  (red)  │     │                          │
│   ∅    Katze  saß                       │
└─────────────────────────────────────────┘
Unassigned: [Die]
Status: ⚠️ "The" has no translation
        ⚠️ 1 word not assigned

After Fix:
┌─────────────────────────────────────────┐
│  The   cat    sat                       │
│   │     │     │                          │
│  Die   Katze  saß                       │
└─────────────────────────────────────────┘
Unassigned: []
Status: ✅ Ready to save
```

## Integration Points

### With TranslationService

The editor integrates with TranslationService via:

1. **Load**: `translation_service.get_translation()` → Load sentence into editor
2. **Save**: Editor emits `save_requested` → Call `translation_service.update_sentence_alignment()`
3. **Regenerate**: Editor emits `regenerate_requested` → Call `translation_service.update_sentence_natural()`

### With Storage

TranslationService handles all storage operations:
- `update_sentence_alignment()` validates and persists changes
- Automatic timestamp updates (`translation.updated_at`)
- Validation using `validate_alignment_complete()`

## Error Handling

### Validation Errors

```python
# Service validates before saving
try:
    service.update_sentence_alignment(translation_id, sentence_uuid, alignments)
except ValueError as e:
    # e.message contains validation error
    # Example: "Invalid alignment: Word 'Die' from natural translation not used"
```

### Not Found Errors

```python
from birkenbihl.storage.exceptions import NotFoundError

try:
    service.update_sentence_alignment(translation_id, sentence_uuid, alignments)
except NotFoundError as e:
    # Translation or sentence doesn't exist
    print(f"Not found: {e}")
```

## Testing

### Manual Test

```python
# Create test sentence
sentence = Sentence(
    source_text="The cat sat",
    natural_translation="Die Katze saß",
    word_alignments=[
        WordAlignment(source_word="The", target_word="Die", position=0),
        WordAlignment(source_word="cat", target_word="Katze", position=1),
        WordAlignment(source_word="sat", target_word="saß", position=2),
    ]
)

# Load and edit
editor.load_sentence(sentence)

# Editor shows:
# - 3 columns (The, cat, sat)
# - Each column has one word (Die, Katze, saß)
# - No unassigned words
# - Save button enabled
```

## Summary

The Word Alignment Editor provides:
- ✅ Visual drag-and-drop interface
- ✅ Real-time validation
- ✅ MVVM architecture (View ↔ ViewModel ↔ Service)
- ✅ Automatic state management
- ✅ Persistence via TranslationService
- ✅ Error handling and feedback

**Integration is simple:**
1. Create editor with ViewModel
2. Load sentence
3. Connect save_requested signal to TranslationService.update_sentence_alignment()
