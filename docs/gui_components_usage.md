# GUI Components Usage Guide

This document demonstrates how to use the reusable PySide6 components in the Birkenbihl GUI application.

## Components Overview

All components follow Clean Code principles:
- Small functions (5-20 lines)
- Single Responsibility Principle
- Type hints (Python 3.13+ syntax)
- Qt Signals for event handling

## ProviderSelector

**File:** `/home/elyo/workspace/elyo/birkenbihl/src/birkenbihl/gui/components/provider_selector.py`

### Purpose
Dropdown widget for selecting AI translation providers. Displays provider name and model in format: "Provider Name (model-name)".

### Interface

```python
class ProviderSelector(QComboBox):
    # Signals
    provider_changed = Signal(ProviderConfig)

    # Constructor
    def __init__(self, context: ProviderSelectorContext)

    # Methods
    def get_selected_provider(self) -> ProviderConfig | None
```

### Usage Example

```python
from birkenbihl.gui.components import ProviderSelector
from birkenbihl.gui.models.context import ProviderSelectorContext
from birkenbihl.models.settings import ProviderConfig

# Create context with providers
providers = [
    ProviderConfig(
        name="OpenAI GPT-4",
        provider_type="openai",
        model="gpt-4",
        api_key="sk-xxx",
    ),
    ProviderConfig(
        name="Claude Sonnet",
        provider_type="anthropic",
        model="claude-3-sonnet",
        api_key="sk-ant-xxx",
    ),
]

context = ProviderSelectorContext(
    providers=providers,
    default_provider=providers[0],
    disabled=False,
)

# Create selector widget
selector = ProviderSelector(context)

# Connect to signal
def on_provider_changed(provider: ProviderConfig):
    print(f"Selected: {provider.name}")

selector.provider_changed.connect(on_provider_changed)

# Get current selection
current = selector.get_selected_provider()
```

## ProgressWidget

**File:** `/home/elyo/workspace/elyo/birkenbihl/src/birkenbihl/gui/components/progress_widget.py`

### Purpose
Progress bar with status message and cancel button for async operations. Supports both indeterminate and determinate progress.

### Interface

```python
class ProgressWidget(QWidget):
    # Signals
    cancelled = Signal()

    # Methods
    def start(self, message: str = "Processing...")
    def update_progress(self, value: int, maximum: int = 100)
    def set_message(self, message: str)
    def finish()
```

### Usage Example

```python
from birkenbihl.gui.components import ProgressWidget

# Create progress widget
progress = ProgressWidget()

# Connect cancel signal
def on_cancelled():
    print("User cancelled operation")

progress.cancelled.connect(on_cancelled)

# Start indeterminate progress
progress.start("Translating text...")

# Update to determinate progress
progress.update_progress(50, 100)  # 50%
progress.set_message("Processing sentence 5/10...")

# Update progress
progress.update_progress(75, 100)  # 75%

# Complete
progress.finish()  # Sets to 100% and hides widget
```

## AlignmentPreview

**File:** `/home/elyo/workspace/elyo/birkenbihl/src/birkenbihl/gui/components/alignment_preview.py`

### Purpose
Read-only preview of word-by-word alignment between source and target language. Displays aligned words in a grid layout.

### Interface

```python
class AlignmentPreview(QWidget):
    # Constructor
    def __init__(self, alignments: list[WordAlignment])

    # Methods
    def update_alignments(self, alignments: list[WordAlignment])
```

### Usage Example

```python
from birkenbihl.gui.components import AlignmentPreview
from birkenbihl.models.translation import WordAlignment

# Create alignments
alignments = [
    WordAlignment(source_word="Yo", target_word="Ich", position=0),
    WordAlignment(source_word="te", target_word="dich", position=1),
    WordAlignment(source_word="extrañaré", target_word="vermissen-werde", position=2),
]

# Create preview widget
preview = AlignmentPreview(alignments)

# Update with new alignments
new_alignments = [
    WordAlignment(source_word="Hello", target_word="Hallo", position=0),
    WordAlignment(source_word="world", target_word="Welt", position=1),
]
preview.update_alignments(new_alignments)
```

## Architecture Notes

### Context Objects (Parameter Object Pattern)

All components use context objects from `/home/elyo/workspace/elyo/birkenbihl/src/birkenbihl/gui/models/context.py`:

- **ProviderSelectorContext**: Encapsulates provider list, default selection, and disabled state
- Reduces parameter count (follows Clean Code: 0-2 parameters ideal)
- Immutable (frozen dataclasses)

### Signal/Slot Pattern

Components use Qt Signals for event communication:
- **ProviderSelector**: `provider_changed(ProviderConfig)` - User selected new provider
- **ProgressWidget**: `cancelled()` - User clicked cancel button

### MVVM Integration

These components are designed to integrate with ViewModels:

```python
class TranslationViewModel(BaseViewModel):
    def __init__(self, translation_service):
        super().__init__()
        self.translation_service = translation_service

    def on_provider_changed(self, provider: ProviderConfig):
        # Update service with new provider
        self.translation_service.set_provider(provider)

    def on_translation_cancelled(self):
        # Cancel ongoing translation
        self.translation_service.cancel_current_translation()
```

## Function Size Compliance

All methods adhere to Clean Code principles:

### ProviderSelector
- `__init__`: 7 lines
- `_populate_providers`: 3 lines
- `_format_provider_display`: 1 line
- `_set_default_provider`: 6 lines
- `_on_selection_changed`: 3 lines
- `get_selected_provider`: 1 line

**Maximum: 7 lines ✓**

### ProgressWidget
- `__init__`: 3 lines
- `_setup_ui`: 12 lines
- `start`: 4 lines
- `update_progress`: 2 lines
- `set_message`: 1 line
- `finish`: 4 lines
- `_on_cancel_clicked`: 1 line

**Maximum: 12 lines ✓**

### AlignmentPreview
- `__init__`: 3 lines
- `_sort_by_position`: 1 line
- `_setup_ui`: 5 lines
- `_add_header_row`: 6 lines
- `_add_alignment_rows`: 7 lines
- `_create_bold_label`: 5 lines
- `update_alignments`: 4 lines
- `_clear_layout`: 4 lines

**Maximum: 7 lines ✓**

## Dependencies

To use these components, add PySide6 to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "PySide6>=6.6.0",
]
```

Install with: `uv sync`
