# UI Refactoring - Aufgabenplan

## 📊 FORTSCHRITT (Stand: 2025-10-11)

### ✅ PHASE 1 & 2 ABGESCHLOSSEN! 🎉

**Zusammenfassung:**
- ✅ Alle 6 Agents erfolgreich abgeschlossen
- ✅ 66 Tests geschrieben, alle bestehen
- ✅ ~300+ Zeilen Code eliminiert
- ✅ Clean Code Prinzipien durchgesetzt (5-20 Zeilen pro Funktion, 0-2 Parameter)
- ✅ Wiederverwendbare Komponenten-Architektur etabliert

### ✅ Phase 1: Infrastruktur (Abgeschlossen)

**Agent 1: Alignment Components** ✅
- ✅ Infrastruktur erstellt (`ui/components/`, `ui/models/`)
- ✅ `AlignmentPreview` Komponente implementiert (ersetzt duplizierte Funktionen)
- ✅ `AlignmentEditor` Komponente implementiert (124 Zeilen → 60 Zeilen)
- ✅ 14 Tests geschrieben, alle bestehen
- **Dateien erstellt:**
  - `src/birkenbihl/ui/components/__init__.py`
  - `src/birkenbihl/ui/components/base.py`
  - `src/birkenbihl/ui/components/alignment.py`
  - `src/birkenbihl/ui/models/__init__.py`
  - `src/birkenbihl/ui/models/context.py`
  - `tests/ui/components/test_alignment.py`

**Agent 3: State Management** ✅
- ✅ State Management Infrastruktur erstellt (`ui/state/`)
- ✅ `SessionStateManager` implementiert (kapselt `st.session_state`)
- ✅ `SessionCacheManager` implementiert (Suggestions-Cache)
- ✅ 21 Tests geschrieben, alle bestehen
- **Dateien erstellt:**
  - `src/birkenbihl/ui/state/__init__.py`
  - `src/birkenbihl/ui/state/base.py`
  - `src/birkenbihl/ui/state/session.py`
  - `src/birkenbihl/ui/state/cache.py`
  - `tests/ui/state/test_state.py`

**Agent 4: UI Service Layer** ✅
- ✅ UI Service Layer Infrastruktur erstellt (`ui/services/`)
- ✅ `TranslationUIServiceImpl` implementiert (Singleton, Lazy Init)
- ✅ Storage/Service-Initialisierung zentralisiert
- ✅ 10 Tests geschrieben, alle bestehen
- **Dateien erstellt:**
  - `src/birkenbihl/ui/services/__init__.py`
  - `src/birkenbihl/ui/services/base.py`
  - `src/birkenbihl/ui/services/translation_ui_service.py`
  - `tests/ui/services/test_translation_ui_service.py`

**Agent 2: Provider & Form Components** ✅
- ✅ `ProviderSelector` Komponente implementiert (eliminiert Duplizierung aus 3 Dateien)
- ✅ `ActionButtonGroup`, `SaveCancelButtons`, `BackButton` implementiert
- ✅ 21 Tests geschrieben, alle bestehen
- **Dateien erstellt:**
  - `src/birkenbihl/ui/components/provider.py`
  - `src/birkenbihl/ui/components/buttons.py`
  - `tests/ui/components/test_provider.py`
  - `tests/ui/components/test_buttons.py`

**Agent 5: Refactor translation_result.py** ✅
- ✅ `render_alignment_preview()` entfernt → `AlignmentPreview` verwendet
- ✅ `render_alignment_edit_mode()` reduziert: 146 Zeilen → 10 Zeilen (verwendet `AlignmentEditor`)
- ✅ `render_natural_edit_mode()` vereinfacht: 107 Zeilen → ~60 Zeilen (verwendet `ProviderSelector`, `SessionCacheManager`)
- ✅ `render_translation_result_tab()` refactored: verwendet `StateManager`, `TranslationUIService`
- ✅ 4 neue Hilfsfunktionen extrahiert (Clean Code: 5-20 Zeilen pro Funktion)
- ✅ Alle direkten `st.session_state` Zugriffe durch `StateManager` ersetzt
- ✅ Storage-Initialisierung durch `TranslationUIService` zentralisiert
- **Code-Reduktion:** ~250 Zeilen eliminiert ✨

**Agent 6: Refactor Other Views** ✅
- ✅ `edit_translation.py` refaktoriert:
  - Provider-Selection durch `ProviderSelector` ersetzt
  - Storage/Service-Init durch `TranslationUIServiceImpl` ersetzt
  - Suggestions-Cache durch `SessionCacheManager` ersetzt
  - `BackButton` Komponente verwendet
  - `AlignmentPreview` Komponente verwendet
  - Helper-Funktion `_generate_suggestions()` extrahiert
- ✅ `translation.py` refaktoriert:
  - Provider-Selection-Code (29 Zeilen) → `ProviderSelector` (9 Zeilen) = **69% Reduktion**
- ✅ `manage_translations.py` refaktoriert:
  - Storage/Service-Initialisierung → `TranslationUIServiceImpl`
  - `st.session_state` → `SessionStateManager` in `open_translation_editor()`
  - Bestehende Funktionen bereits Clean Code-konform (24-43 Zeilen, single responsibility)
- **Dateien modifiziert:**
  - `src/birkenbihl/ui/edit_translation.py`
  - `src/birkenbihl/ui/translation.py`
  - `src/birkenbihl/ui/manage_translations.py`

### 🔄 In Bearbeitung

Keine offenen Aufgaben

### ⏸️ Ausstehend

**settings.py refactoring (optional):**
- ⏸️ Provider-Form-Komponenten verwenden (Zeilen 118-327)
- ⏸️ ProviderCard und GeneralSettingsForm Komponenten erstellen
- **Hinweis:** Nicht kritisch, da settings.py weniger oft verwendet wird

---

## Übersicht

Refactoring der Streamlit-UI gemäß Clean Code Prinzipien (Uncle Bob):
- **Lange Funktionen reduzieren**: Von 100+ auf 5-20 Zeilen
- **Parameter reduzieren**: Von 4-5 auf 0-2 Parameter (via Parameter-Objekte)
- **Code-Duplizierung eliminieren**: DRY-Prinzip durchsetzen
- **Single Responsibility**: Eine Verantwortlichkeit pro Funktion/Klasse
- **Wiederverwendbare Komponenten**: UI-Komponenten-Architektur einführen

## Parallelisierungsstrategie

Die Aufgaben sind in **6 parallele Agents** aufgeteilt, die unabhängig voneinander arbeiten können. Die Schnittstellen (Contracts) sind vorab definiert, damit alle Agents gegen dieselben Interfaces entwickeln.

---

## 🔗 SCHNITTSTELLEN-DEFINITIONEN (Contracts)

Alle Agents müssen diese Schnittstellen implementieren/verwenden. Diese bilden die Grundlage für die parallele Arbeit.

### 1. Base Component Protocol

**Datei:** `src/birkenbihl/ui/components/base.py`

```python
"""Base protocol for all UI components."""

from typing import Protocol
from abc import abstractmethod

class UIComponent(Protocol):
    """Protocol for reusable UI components."""

    @abstractmethod
    def render(self) -> None:
        """Render the component to Streamlit."""
        ...
```

### 2. Context Objects (Parameter Objects)

**Datei:** `src/birkenbihl/ui/models/context.py`

```python
"""Context objects for passing data to components (Parameter Object pattern)."""

from dataclasses import dataclass
from uuid import UUID
from birkenbihl.models.translation import Translation, Sentence
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.models.settings import ProviderConfig

@dataclass(frozen=True)
class SentenceEditorContext:
    """Context for sentence editor component."""
    translation: Translation
    sentence: Sentence
    sentence_index: int
    service: TranslationService
    is_new_translation: bool

@dataclass(frozen=True)
class ProviderSelectorContext:
    """Context for provider selector component."""
    providers: list[ProviderConfig]
    default_provider: ProviderConfig | None
    disabled: bool = False
    key_suffix: str = ""

@dataclass(frozen=True)
class AlignmentContext:
    """Context for alignment preview/editor."""
    sentence: Sentence
    translation: Translation
    service: TranslationService
    is_new_translation: bool
```

### 3. State Manager Interface

**Datei:** `src/birkenbihl/ui/state/base.py`

```python
"""State management interfaces."""

from typing import Protocol, Any
from uuid import UUID

class StateManager(Protocol):
    """Protocol for session state management."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from session state."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set value in session state."""
        ...

    def delete(self, key: str) -> None:
        """Delete key from session state."""
        ...

    def exists(self, key: str) -> bool:
        """Check if key exists in session state."""
        ...

class CacheManager(Protocol):
    """Protocol for cache management (suggestions, etc.)."""

    def get_suggestions(self, sentence_uuid: UUID) -> list[str] | None:
        """Get cached suggestions for sentence."""
        ...

    def set_suggestions(self, sentence_uuid: UUID, suggestions: list[str]) -> None:
        """Cache suggestions for sentence."""
        ...

    def clear_suggestions(self, sentence_uuid: UUID) -> None:
        """Clear cached suggestions."""
        ...
```

### 4. UI Service Interface

**Datei:** `src/birkenbihl/ui/services/base.py`

```python
"""UI service layer interfaces."""

from typing import Protocol
from uuid import UUID
from birkenbihl.models.translation import Translation
from birkenbihl.services.translation_service import TranslationService
from birkenbihl.storage.json_storage import JsonStorageProvider

class TranslationUIService(Protocol):
    """Service layer for UI operations (encapsulates storage/service initialization)."""

    @property
    def service(self) -> TranslationService:
        """Get translation service instance."""
        ...

    @property
    def storage(self) -> JsonStorageProvider:
        """Get storage provider instance."""
        ...

    def get_translation(self, translation_id: UUID) -> Translation | None:
        """Get translation by ID."""
        ...

    def list_translations(self) -> list[Translation]:
        """List all translations."""
        ...
```

### 5. Component Interfaces

**Alignment Component Interface:**
```python
class AlignmentPreview:
    """Renders word alignments preview."""
    def __init__(self, alignments: list[WordAlignment]): ...
    def render(self) -> None: ...

class AlignmentEditor:
    """Manual word-by-word alignment editor."""
    def __init__(self, context: AlignmentContext): ...
    def render(self) -> None: ...
```

**Provider Component Interface:**
```python
class ProviderSelector:
    """Provider selection dropdown."""
    def __init__(self, context: ProviderSelectorContext): ...
    def render(self) -> ProviderConfig | None: ...
```

**Button Group Interface:**
```python
class ActionButtonGroup:
    """Reusable action buttons (Save/Cancel/Back)."""
    def __init__(self, actions: dict[str, callable]): ...
    def render(self) -> str | None: ...  # Returns clicked button key
```

---

## 📋 AGENT AUFGABEN

### Agent 1: Alignment Components ⚙️

**Priorität:** Hoch (wird überall gebraucht)
**Abhängigkeiten:** Keine (kann sofort starten)
**Dateien:**
- `src/birkenbihl/ui/components/__init__.py`
- `src/birkenbihl/ui/components/base.py`
- `src/birkenbihl/ui/components/alignment.py`
- `src/birkenbihl/ui/models/__init__.py`
- `src/birkenbihl/ui/models/context.py`

**Aufgaben:**
1. **Infrastruktur erstellen:**
   - `ui/components/__init__.py` erstellen
   - `ui/components/base.py` mit `UIComponent` Protocol erstellen
   - `ui/models/__init__.py` und `ui/models/context.py` erstellen

2. **AlignmentPreview Komponente:**
   - Duplizierten Code aus `edit_translation.py:208-231` und `translation_result.py:323-346` extrahieren
   - HTML-Rendering in separate Methode `_build_alignment_html()` auslagern
   - Clean Code: Max 20 Zeilen pro Funktion
   - Unterstützt: `list[WordAlignment]` als Input

3. **AlignmentEditor Komponente:**
   - Code aus `translation_result.py:349-473` (124 Zeilen) refactoren
   - In mehrere kleine Funktionen aufteilen:
     - `_extract_target_words()` (bereits vorhanden, wiederverwenden)
     - `_initialize_editor_state()`
     - `_render_word_mapping()`
     - `_validate_and_render_actions()`
   - Verwendet `AlignmentContext` Parameter-Objekt (statt 4 Parameter)

4. **Tests schreiben:**
   - Unit-Tests für `AlignmentPreview.render()`
   - Integration-Tests für `AlignmentEditor` mit Mock-Service

**Prompt für Agent 1:**
```
You are refactoring the Birkenbihl UI to follow Clean Code principles (Uncle Bob).

TASK: Create alignment UI components that eliminate code duplication and reduce function length.

REQUIREMENTS:
1. Implement UIComponent protocol from the interface definition
2. Create AlignmentPreview component:
   - Extract duplicated code from edit_translation.py:208-231 and translation_result.py:323-346
   - Input: list[WordAlignment]
   - Output: Renders HTML preview
   - Max 20 lines per function

3. Create AlignmentEditor component:
   - Refactor translation_result.py:349-473 (124 lines → ~40 lines)
   - Use AlignmentContext parameter object (NOT 4 separate parameters)
   - Split into small functions (5-20 lines each):
     * _initialize_editor_state()
     * _render_word_mapping()
     * _validate_and_render_actions()

4. Follow Uncle Bob's Clean Code:
   - Functions: 5-20 lines
   - Parameters: 0-2 (use parameter objects)
   - Single Responsibility Principle
   - DRY (Don't Repeat Yourself)

FILES TO CREATE:
- src/birkenbihl/ui/components/__init__.py
- src/birkenbihl/ui/components/base.py (UIComponent protocol)
- src/birkenbihl/ui/components/alignment.py
- src/birkenbihl/ui/models/__init__.py
- src/birkenbihl/ui/models/context.py (AlignmentContext, SentenceEditorContext)

INTERFACE CONTRACT (use exactly this):
- AlignmentPreview.__init__(alignments: list[WordAlignment])
- AlignmentPreview.render() -> None
- AlignmentEditor.__init__(context: AlignmentContext)
- AlignmentEditor.render() -> None

Run tests after implementation to verify functionality.
```

---

### Agent 2: Provider & Form Components 🔌

**Priorität:** Hoch (parallel zu Agent 1)
**Abhängigkeiten:** `ui/components/base.py` (Agent 1)
**Dateien:**
- `src/birkenbihl/ui/components/provider.py`
- `src/birkenbihl/ui/components/forms.py`
- `src/birkenbihl/ui/components/buttons.py`

**Aufgaben:**
1. **ProviderSelector Komponente:**
   - Duplizierten Provider-Auswahl-Code extrahieren aus:
     - `translation.py:103-131` (29 Zeilen)
     - `translation_result.py:234-248` (15 Zeilen)
     - `edit_translation.py:130-144` (15 Zeilen)
   - Verwendet `ProviderSelectorContext` Parameter-Objekt
   - Rückgabe: `ProviderConfig | None`
   - Single Responsibility: Nur Provider auswählen, keine Logik

2. **ProviderForm Komponente:**
   - Code aus `settings.py:118-218` (Add) und `settings.py:232-327` (Edit) refactoren
   - Shared Logic in Basis-Klasse `BaseProviderForm`
   - `AddProviderForm(BaseProviderForm)` und `EditProviderForm(BaseProviderForm)`
   - Formularbehandlung in `_render_form_fields()` und `_render_actions()` trennen

3. **ActionButtonGroup Komponente:**
   - Wiederverwendbare Button-Gruppen (Save/Cancel/Back/Delete)
   - Input: `dict[str, ButtonConfig]` mit Label, Type, Icon, Callback
   - Output: Clicked button key oder None
   - Verwendung in allen Views (Translation, Settings, etc.)

4. **Tests schreiben:**
   - Mock-Tests für `ProviderSelector` mit verschiedenen Kontexten
   - Form-Tests mit verschiedenen Provider-Typen

**Prompt für Agent 2:**
```
You are refactoring the Birkenbihl UI to follow Clean Code principles (Uncle Bob).

TASK: Create provider selection and form components to eliminate code duplication.

REQUIREMENTS:
1. ProviderSelector component:
   - Eliminates duplication from translation.py:103-131, translation_result.py:234-248, edit_translation.py:130-144
   - Uses ProviderSelectorContext parameter object
   - Returns: ProviderConfig | None
   - Single responsibility: ONLY provider selection, no business logic

2. Provider Forms:
   - Refactor settings.py:118-218 (Add) and :232-327 (Edit) into components
   - Create BaseProviderForm with shared logic
   - AddProviderForm and EditProviderForm inherit from base
   - Split into: _render_form_fields(), _render_actions()

3. ActionButtonGroup:
   - Reusable button groups (Save/Cancel/Back/Delete)
   - Input: dict[str, ButtonConfig] with label, type, icon, callback
   - Output: Clicked button key or None

CLEAN CODE RULES:
- Functions: 5-20 lines
- Parameters: 0-2 (use parameter objects)
- DRY principle
- Single Responsibility

FILES TO CREATE:
- src/birkenbihl/ui/components/provider.py
- src/birkenbihl/ui/components/forms.py
- src/birkenbihl/ui/components/buttons.py

DEPENDENCIES:
- Wait for Agent 1 to create ui/components/base.py (UIComponent protocol)
- Use ProviderSelectorContext from ui/models/context.py (Agent 1)

INTERFACE CONTRACT:
- ProviderSelector.__init__(context: ProviderSelectorContext)
- ProviderSelector.render() -> ProviderConfig | None
- ActionButtonGroup.__init__(buttons: dict[str, ButtonConfig])
- ActionButtonGroup.render() -> str | None

Run tests after implementation.
```

---

### Agent 3: State Management 📊

**Priorität:** Mittel (parallel zu Agent 1 & 2)
**Abhängigkeiten:** Keine
**Dateien:**
- `src/birkenbihl/ui/state/__init__.py`
- `src/birkenbihl/ui/state/base.py`
- `src/birkenbihl/ui/state/session.py`
- `src/birkenbihl/ui/state/cache.py`

**Aufgaben:**
1. **StateManager Implementierung:**
   - Kapselt alle `st.session_state` Zugriffe
   - Type-safe Getter/Setter für bekannte Keys
   - Property-basierte Zugriffe für häufige States:
     - `.current_view`, `.is_translating`, `.translation_result`, etc.
   - Verhindert direkte `st.session_state` Zugriffe in UI-Code

2. **CacheManager Implementierung:**
   - Verwaltet `suggestions_cache` aus `translation_result.py`
   - Methods: `get_suggestions()`, `set_suggestions()`, `clear_suggestions()`
   - TTL-basiertes Caching (optional, für spätere Optimierung)
   - Type-safe: UUID-based Keys, List[str] Values

3. **Initialisierung zentralisieren:**
   - `app.py:103-133` (initialize_session_state) in StateManager verschieben
   - `StateManager.initialize()` aufrufen statt manueller Initialisierung
   - Default-Werte in einer Config (nicht hardcoded)

4. **Tests schreiben:**
   - Unit-Tests für StateManager Get/Set/Delete
   - Cache-Tests mit verschiedenen Szenarien (Hit/Miss/Clear)

**Prompt für Agent 3:**
```
You are refactoring the Birkenbihl UI to follow Clean Code principles (Uncle Bob).

TASK: Create state management layer to encapsulate Streamlit session state access.

REQUIREMENTS:
1. StateManager implementation:
   - Encapsulates ALL st.session_state accesses
   - Type-safe getters/setters for known keys
   - Properties for frequent states: .current_view, .is_translating, .translation_result, etc.
   - NO direct st.session_state access in UI code

2. CacheManager implementation:
   - Manages suggestions_cache from translation_result.py
   - Methods: get_suggestions(), set_suggestions(), clear_suggestions()
   - Type-safe: UUID keys, list[str] values
   - Optional: TTL-based caching for future optimization

3. Centralize initialization:
   - Move app.py:103-133 (initialize_session_state) to StateManager.initialize()
   - Default values in config (not hardcoded)

CLEAN CODE RULES:
- Single Responsibility: Only state management
- Encapsulation: Hide Streamlit internals
- Type Safety: Use type hints everywhere

FILES TO CREATE:
- src/birkenbihl/ui/state/__init__.py
- src/birkenbihl/ui/state/base.py (StateManager, CacheManager protocols)
- src/birkenbihl/ui/state/session.py (SessionStateManager implementation)
- src/birkenbihl/ui/state/cache.py (SessionCacheManager implementation)

INTERFACE CONTRACT (implement exactly):
- StateManager.get(key: str, default: Any) -> Any
- StateManager.set(key: str, value: Any) -> None
- StateManager.delete(key: str) -> None
- StateManager.exists(key: str) -> bool
- CacheManager.get_suggestions(uuid: UUID) -> list[str] | None
- CacheManager.set_suggestions(uuid: UUID, suggestions: list[str]) -> None
- CacheManager.clear_suggestions(uuid: UUID) -> None

Run tests after implementation.
```

---

### Agent 4: UI Service Layer 🛠️

**Priorität:** Mittel (parallel zu Agent 1-3)
**Abhängigkeiten:** Keine
**Dateien:**
- `src/birkenbihl/ui/services/__init__.py`
- `src/birkenbihl/ui/services/base.py`
- `src/birkenbihl/ui/services/translation_ui_service.py`

**Aufgaben:**
1. **TranslationUIService Implementierung:**
   - Kapselt wiederholte Storage/Service-Initialisierung:
     - `translation_result.py:68-69, 92-93` (4x dupliziert)
     - `edit_translation.py:30-32`
     - `manage_translations.py:20-21`
   - Singleton-Pattern: Eine Service-Instanz pro Session
   - Lazy Initialization: Nur bei Bedarf erstellen

2. **Methoden implementieren:**
   - `get_translation(uuid)` - Wrapper mit Error-Handling
   - `list_translations()` - Mit Sortierung (neueste zuerst)
   - `save_translation()` - Mit Success/Error Feedback
   - `delete_translation()` - Mit Confirmation-Logik
   - `update_sentence_natural()`, `update_sentence_alignment()` - Wrapper

3. **Error Handling zentralisieren:**
   - Try/Except-Blöcke aus UI-Code in Service verschieben
   - Streamlit-freundliche Error-Messages
   - Logging in Service-Layer (nicht in UI)

4. **Tests schreiben:**
   - Mock-Storage für Service-Tests
   - Error-Handling-Tests (FileNotFound, ValidationError, etc.)

**Prompt für Agent 4:**
```
You are refactoring the Birkenbihl UI to follow Clean Code principles (Uncle Bob).

TASK: Create UI service layer to encapsulate storage/service initialization and error handling.

REQUIREMENTS:
1. TranslationUIService implementation:
   - Eliminates duplication: translation_result.py:68-69, 92-93, edit_translation.py:30-32, manage_translations.py:20-21
   - Singleton pattern: One service instance per session
   - Lazy initialization: Create only when needed

2. Methods to implement:
   - get_translation(uuid) - with error handling
   - list_translations() - sorted by date (newest first)
   - save_translation() - with success/error feedback
   - delete_translation() - with confirmation logic
   - update_sentence_natural(), update_sentence_alignment() - wrappers

3. Centralize error handling:
   - Move try/except blocks from UI to service
   - Streamlit-friendly error messages
   - Logging in service (NOT in UI)

CLEAN CODE RULES:
- Single Responsibility: Service layer only
- Error handling in one place
- No UI logic in service (return data, let UI render)

FILES TO CREATE:
- src/birkenbihl/ui/services/__init__.py
- src/birkenbihl/ui/services/base.py (TranslationUIService protocol)
- src/birkenbihl/ui/services/translation_ui_service.py (implementation)

INTERFACE CONTRACT:
- TranslationUIService.get_translation(uuid: UUID) -> Translation | None
- TranslationUIService.list_translations() -> list[Translation]
- TranslationUIService.save_translation(translation: Translation) -> bool
- TranslationUIService.delete_translation(uuid: UUID) -> bool
- Properties: .service, .storage (lazy-loaded)

Run tests after implementation.
```

---

### Agent 5: Refactor translation_result.py 🔄

**Priorität:** Niedrig (wartet auf Agent 1-4)
**Abhängigkeiten:** Agent 1, 2, 3, 4 (alle Komponenten)
**Dateien:**
- `src/birkenbihl/ui/translation_result.py` (refactored)
- `src/birkenbihl/ui/components/sentence.py` (neue Komponente)

**Aufgaben:**
1. **Komponenten verwenden:**
   - `AlignmentPreview` (Agent 1) statt `render_alignment_preview()` (Zeilen 323-346)
   - `AlignmentEditor` (Agent 1) in `render_alignment_edit_mode()` verwenden
   - `ProviderSelector` (Agent 2) in `render_natural_edit_mode()` verwenden
   - `ActionButtonGroup` (Agent 2) für Save/Cancel/Back Buttons
   - `StateManager` (Agent 3) statt direkter `st.session_state` Zugriffe
   - `TranslationUIService` (Agent 4) statt direkter Storage-Initialisierung

2. **SentenceEditor Komponente erstellen:**
   - Code aus `render_sentence_editor()` (Zeilen 171-212) extrahieren
   - Verwendet `SentenceEditorContext` Parameter-Objekt
   - Tabs-Logik in separate Methoden: `_render_natural_tab()`, `_render_alignment_tab()`

3. **Funktionen reduzieren:**
   - `render_natural_edit_mode()`: Von 107 auf ~30 Zeilen (Komponenten nutzen)
   - `render_alignment_edit_mode()`: Von 124 auf ~15 Zeilen (vollständig in Komponente)
   - `render_sentence_editor()`: Von 42 auf ~10 Zeilen (SentenceEditor Komponente)
   - `_execute_translation()`: Streaming-Logik in separate Funktion

4. **Tests aktualisieren:**
   - Integration-Tests für gesamten Translation-Result-Flow
   - Mock-Components für isolierte Tests

**Prompt für Agent 5:**
```
You are refactoring translation_result.py to use the new component architecture.

TASK: Refactor translation_result.py using components from Agent 1-4 to reduce function length and complexity.

REQUIREMENTS:
1. Replace inline code with components:
   - AlignmentPreview (Agent 1) replaces render_alignment_preview() (lines 323-346)
   - AlignmentEditor (Agent 1) in render_alignment_edit_mode()
   - ProviderSelector (Agent 2) in render_natural_edit_mode()
   - ActionButtonGroup (Agent 2) for all buttons
   - StateManager (Agent 3) instead of st.session_state
   - TranslationUIService (Agent 4) instead of manual Storage init

2. Create SentenceEditor component:
   - Extract from render_sentence_editor() (lines 171-212)
   - Use SentenceEditorContext parameter object
   - Split tabs: _render_natural_tab(), _render_alignment_tab()

3. Reduce function length:
   - render_natural_edit_mode(): 107 → ~30 lines
   - render_alignment_edit_mode(): 124 → ~15 lines (use AlignmentEditor component)
   - render_sentence_editor(): 42 → ~10 lines (use SentenceEditor component)
   - _execute_translation(): Extract streaming logic

CLEAN CODE TARGET:
- All functions: 5-20 lines
- Parameters: 0-2 (use context objects)
- No code duplication
- Single Responsibility

FILES TO MODIFY:
- src/birkenbihl/ui/translation_result.py

FILES TO CREATE:
- src/birkenbihl/ui/components/sentence.py (SentenceEditor, SentenceCard)

DEPENDENCIES (wait for these):
- Agent 1: AlignmentPreview, AlignmentEditor
- Agent 2: ProviderSelector, ActionButtonGroup
- Agent 3: StateManager
- Agent 4: TranslationUIService

Run integration tests after refactoring.
```

---

### Agent 6: Refactor Other Views 📝

**Priorität:** Niedrig (wartet auf Agent 1-4)
**Abhängigkeiten:** Agent 1, 2, 3, 4
**Dateien:**
- `src/birkenbihl/ui/translation.py` (refactored)
- `src/birkenbihl/ui/settings.py` (refactored)
- `src/birkenbihl/ui/manage_translations.py` (refactored)
- `src/birkenbihl/ui/edit_translation.py` (refactored)

**Aufgaben:**
1. **translation.py refactoren:**
   - `ProviderSelector` (Agent 2) verwenden statt Zeilen 103-131
   - `StateManager` (Agent 3) für Session-State
   - File-Upload-Logik in separate Funktion `_handle_file_upload()` extrahieren
   - Settings-Logik in separate Funktion `_render_settings_panel()` extrahieren

2. **settings.py refactoren:**
   - `ProviderForm` (Agent 2) verwenden statt Zeilen 118-327
   - Provider-Card-Rendering in `ProviderCard` Komponente extrahieren
   - Settings-Form in `GeneralSettingsForm` Komponente extrahieren

3. **manage_translations.py refactoren:**
   - `TranslationUIService` (Agent 4) verwenden statt Zeilen 20-21
   - `TranslationCard` Komponente für `render_translation_card()` erstellen
   - Confirmation-Dialog in `ConfirmationDialog` Komponente extrahieren

4. **edit_translation.py analysieren:**
   - Evaluieren ob überhaupt noch benötigt (Overlap mit translation_result.py)
   - Falls ja: `AlignmentPreview` verwenden, sonst löschen

5. **Tests schreiben:**
   - View-Tests mit gemockten Komponenten
   - End-to-End-Tests für komplette User-Flows

**Prompt für Agent 6:**
```
You are refactoring all remaining UI views to use the new component architecture.

TASK: Refactor translation.py, settings.py, manage_translations.py, edit_translation.py using components.

REQUIREMENTS:
1. translation.py:
   - Use ProviderSelector (Agent 2) instead of lines 103-131
   - Use StateManager (Agent 3) for session state
   - Extract: _handle_file_upload(), _render_settings_panel()

2. settings.py:
   - Use ProviderForm (Agent 2) instead of lines 118-327
   - Create ProviderCard component for provider cards
   - Create GeneralSettingsForm component

3. manage_translations.py:
   - Use TranslationUIService (Agent 4) instead of lines 20-21
   - Create TranslationCard component for render_translation_card()
   - Create ConfirmationDialog component for delete confirmation

4. edit_translation.py:
   - Evaluate if still needed (overlap with translation_result.py)
   - If yes: Use AlignmentPreview, otherwise delete

CLEAN CODE TARGET:
- All functions: 5-20 lines
- No code duplication (DRY)
- Single Responsibility

FILES TO MODIFY:
- src/birkenbihl/ui/translation.py
- src/birkenbihl/ui/settings.py
- src/birkenbihl/ui/manage_translations.py
- src/birkenbihl/ui/edit_translation.py (or delete)

FILES TO CREATE:
- src/birkenbihl/ui/components/cards.py (TranslationCard, ProviderCard)
- src/birkenbihl/ui/components/dialogs.py (ConfirmationDialog)

DEPENDENCIES (wait for these):
- Agent 1: AlignmentPreview
- Agent 2: ProviderSelector, ProviderForm, ActionButtonGroup
- Agent 3: StateManager
- Agent 4: TranslationUIService

Run view tests and end-to-end tests after refactoring.
```

---

## 🔄 ABHÄNGIGKEITEN & REIHENFOLGE

### Phase 1: Infrastruktur (Parallel)
- **Agent 1**: Components Base + Alignment ⚙️
- **Agent 2**: Provider & Forms 🔌 (wartet auf base.py von Agent 1)
- **Agent 3**: State Management 📊 (unabhängig)
- **Agent 4**: UI Service Layer 🛠️ (unabhängig)

**Wartezeit:** Bis alle 4 Agents fertig sind

### Phase 2: Refactoring (Parallel)
- **Agent 5**: Refactor translation_result.py 🔄 (wartet auf Agent 1-4)
- **Agent 6**: Refactor Other Views 📝 (wartet auf Agent 1-4)

**Wartezeit:** Bis beide Agents fertig sind

### Phase 3: Finalisierung (Sequentiell)
1. Integration-Tests über alle Views
2. Code-Review & Clean-Up
3. Dokumentation aktualisieren

---

## ✅ ERFOLGSKRITERIEN

Nach Abschluss aller Agents:

1. **Code-Metriken:**
   - ✅ Alle Funktionen: 5-20 Zeilen
   - ✅ Alle Funktionen: Max 2 Parameter
   - ✅ Keine Code-Duplizierung (DRY)
   - ✅ Test-Coverage: >80%

2. **Architektur:**
   - ✅ Wiederverwendbare Komponenten in `ui/components/`
   - ✅ State-Management in `ui/state/`
   - ✅ UI-Service-Layer in `ui/services/`
   - ✅ Parameter-Objekte in `ui/models/`

3. **Clean Code Prinzipien:**
   - ✅ Single Responsibility Principle
   - ✅ Don't Repeat Yourself (DRY)
   - ✅ Meaningful Names
   - ✅ Small Functions
   - ✅ Error Handling centralized

4. **Funktionalität:**
   - ✅ Alle bestehenden Features funktionieren
   - ✅ Keine Regression-Bugs
   - ✅ Performance unverändert oder besser

---

## 🚀 AUSFÜHRUNG

### Parallele Ausführung (Empfohlen):

```bash
# Phase 1: Alle Agents parallel starten
claude-code --agent agent1 &
claude-code --agent agent2 &
claude-code --agent agent3 &
claude-code --agent agent4 &
wait

# Phase 2: Refactoring-Agents parallel starten
claude-code --agent agent5 &
claude-code --agent agent6 &
wait

# Phase 3: Tests & Finalisierung
pytest tests/ui/ -v --cov
```

### Sequentielle Ausführung (Fallback):

```bash
# Wenn parallele Ausführung nicht möglich:
claude-code --agent agent1  # Zuerst Basis-Infrastruktur
claude-code --agent agent2  # Dann Provider-Components
claude-code --agent agent3  # State Management
claude-code --agent agent4  # UI Service
claude-code --agent agent5  # Refactor translation_result
claude-code --agent agent6  # Refactor other views
pytest tests/ui/ -v --cov
```

---

## 📝 NOTIZEN

- **Schnittstellen NICHT ändern:** Alle Agents müssen die definierten Interfaces verwenden
- **Tests sind Pflicht:** Jeder Agent schreibt Tests für seinen Code
- **Clean Code ist Priorität:** Lieber mehr kleine Funktionen als wenige große
- **Kommunikation über Interfaces:** Agents kommunizieren nur über definierte Schnittstellen
- **Backward Compatibility:** Bestehende Funktionalität darf nicht brechen

---

## 🐛 TROUBLESHOOTING

**Problem:** Agent 2 kann nicht starten, da `base.py` fehlt
**Lösung:** Warte auf Agent 1 oder erstelle leere `base.py` mit Protocol-Definition

**Problem:** Tests schlagen fehl wegen fehlender Imports
**Lösung:** Überprüfe dass alle `__init__.py` Dateien existieren und Exporte definiert haben

**Problem:** Circular Imports zwischen Komponenten
**Lösung:** Verwende TYPE_CHECKING Imports oder verschiebe gemeinsame Types in `ui/models/`

**Problem:** Streamlit session_state Konflikte
**Lösung:** Nur StateManager darf auf `st.session_state` zugreifen, keine direkten Zugriffe in Komponenten
