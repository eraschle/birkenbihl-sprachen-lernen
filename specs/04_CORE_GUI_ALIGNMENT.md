# Core ↔ GUI Alignment & Integration

**Datum:** 15. Oktober 2025  
**Zweck:** Konsistenz zwischen Core (Services) und GUI herstellen  
**Basis:** Core-Analyse + GUI-Analyse

---

## 🎯 Executive Summary

Dieses Dokument definiert **wie Core und GUI harmonisch zusammenarbeiten** sollen, um konsistente Code-Qualität über alle Schichten zu erreichen. Beide Schichten sind gut implementiert, aber es gibt **Inkonsistenzen** bei Parameter Objects, Error Handling und Code-Duplikation.

### Hauptziele

1. ✅ **Parameter Objects**: Überall verwenden (Core + GUI)
2. ✅ **Error Handling**: Konsistente Strategie
3. ✅ **Presenter Layer**: Eliminiert CLI/GUI-Duplikation
4. ✅ **Clean Code**: 100% Compliance in allen Schichten

---

## 📊 Status Quo Vergleich

### Core vs. GUI

| Aspekt | Core | GUI | Status | Ziel |
|--------|------|-----|--------|------|
| Funktionslänge | 87% <20 LOC | 91% <20 LOC | ✅ Gut | 100% |
| Parameter Count | 88% ≤2 | 87% ≤2 | ⚠️ Fast | 100% |
| Parameter Objects | ❌ Fehlen | ❌ Fehlen | ❌ Inkonsistent | ✅ Überall |
| Protocol-Based | ✅ 100% | ✅ 100% | ✅ Perfekt | ✅ Beib ehalten |
| Error Handling | Exceptions | Signals | ⚠️ Unterschiedlich | ✅ Konsistent |
| Test Coverage | 80%+ | 61+ Tests | ⚠️ OK | 80%+ |

---

## 🔧 Kritische Anpassungen

### 1. Parameter Objects: Core & GUI harmonisieren ❌🔴

#### Problem: Beide Schichten haben >2 Parameter

**Core (TranslationService):**
```python
# ❌ VORHER: 4 Parameter
def translate(self, text: str, source_lang: Language, 
              target_lang: Language, title: str) -> Translation:
    pass
```

**GUI (CreateTranslationViewModel):**
```python
# ❌ VORHER: 5 Parameter
def create_translation(self, text: str, source_lang: Language | None,
                      target_lang: Language, title: str, 
                      provider: ProviderConfig) -> None:
    pass
```

#### Lösung: Gemeinsame Parameter Objects

**Schritt 1: Core Parameter Object**

```python
# src/birkenbihl/models/requests.py (NEU!)

@dataclass
class TranslationRequest:
    """Request for translating text (Core Layer)."""
    text: str
    source_lang: Language
    target_lang: Language
    title: str = ""

@dataclass
class SentenceUpdateRequest:
    """Request for updating sentence (Core Layer)."""
    translation_id: UUID
    sentence_idx: int
    new_text: str
    provider: ProviderConfig
```

**Schritt 2: Core Service API Update**

```python
# src/birkenbihl/services/translation_service.py

class TranslationService:
    # ✅ NACHHER: 1 Parameter
    def translate(self, request: TranslationRequest) -> Translation:
        """Translate text using Birkenbihl method.
        
        Args:
            request: Translation request with all parameters
            
        Returns:
            Translation object with natural and word-by-word translations
        """
        if not self._translator:
            raise ValueError("Translator not configured")
        
        return self._translator.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            title=request.title
        )
    
    # ✅ NACHHER: 1 Parameter
    def update_sentence_natural(self, 
                               request: SentenceUpdateRequest) -> Translation:
        """Update natural translation for sentence.
        
        Args:
            request: Update request with all parameters
            
        Returns:
            Updated translation with regenerated alignments
        """
        translation = self._load_translation(request.translation_id)
        sentence = self._get_sentence(translation, request.sentence_idx)
        self._update_natural_translation(sentence, request.new_text)
        self._regenerate_alignments(sentence, request.provider)
        return self._save_translation(translation)
```

**Schritt 3: GUI Parameter Object** (erweitert Core Request)

```python
# src/birkenbihl/gui/models/requests.py (NEU!)

from birkenbihl.models.requests import TranslationRequest as CoreTranslationRequest

@dataclass
class GUITranslationRequest(CoreTranslationRequest):
    """GUI-specific translation request.
    
    Extends core request with GUI-specific fields like provider
    (Core doesn't need provider, it's injected via constructor).
    """
    provider: ProviderConfig
    source_lang_override: Language | None = None  # For auto-detection

    def to_core_request(self, detected_lang: Language | None = None) -> CoreTranslationRequest:
        """Convert to core request."""
        return CoreTranslationRequest(
            text=self.text,
            source_lang=self.source_lang_override or detected_lang or self.source_lang,
            target_lang=self.target_lang,
            title=self.title
        )
```

**Schritt 4: GUI ViewModel Update**

```python
# src/birkenbihl/gui/viewmodels/create_vm.py

class CreateTranslationViewModel:
    # ✅ NACHHER: 1 Parameter
    def create_translation(self, request: GUITranslationRequest) -> None:
        """Create translation from request.
        
        Args:
            request: GUI translation request
        """
        # Auto-detect if needed
        if request.source_lang_override is None:
            self._detect_language_async(request)
            return
        
        # Create translation
        worker = TranslationWorker(
            callback=self._on_translation_complete,
            error_callback=self._on_translation_error,
            request=request  # Nur 1 Parameter an Worker!
        )
        QThreadPool.globalInstance().start(worker)
```

**Schritt 5: CLI Update** (nutzt Core Request)

```python
# src/birkenbihl/cli.py

def _perform_translation(config: CLIConfig, text: str, 
                        source_lang: Language, target_lang: Language,
                        title: str) -> Translation:
    """Execute translation (5-10 LOC)."""
    request = TranslationRequest(
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
        title=title
    )
    return config.service.translate(request)  # Core Request!
```

**Ergebnis:**
- ✅ Core: `translate()` hat 1 Parameter (TranslationRequest)
- ✅ GUI: `create_translation()` hat 1 Parameter (GUITranslationRequest)
- ✅ CLI: Nutzt Core Request direkt
- ✅ Konsistenz über alle Schichten

**Aufwand:** 3-4 Stunden

**Priorität:** 🔴 **KRITISCH**

---

### 2. Error Handling: Konsistente Strategie 🔧🟠

#### Problem: Inkonsistente Error Handling

**Core (Exceptions):**
```python
class TranslationService:
    def translate(self, request: TranslationRequest) -> Translation:
        if not self._translator:
            raise ValueError("Translator not configured")  # Exception
        
        try:
            return self._translator.translate(...)
        except Exception as e:
            raise TranslationError(f"Translation failed: {e}") from e
```

**GUI (Mix aus Exceptions und Signals):**
```python
class CreateTranslationViewModel(QObject):
    error_occurred = Signal(str)  # Signal
    
    def create_translation(self, request: GUITranslationRequest) -> None:
        try:
            result = self._service.translate(...)  # Kann Exception werfen
            self.translation_complete.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))  # Signal + keine Rückgabe
```

#### Lösung: Layered Error Handling Strategy

**Prinzip:**
- **Core Layer**: Wirft Exceptions (Business Logic Fehler)
- **ViewModel Layer**: Fängt Exceptions, mapped zu Signals (für UI)
- **Command Layer**: Optional - wrapped ViewModel Calls in CommandResult
- **View Layer**: Reagiert auf Signals, zeigt Dialogs

**Implementation:**

**Core (unverändert):**
```python
# Core wirft Exceptions
class TranslationService:
    def translate(self, request: TranslationRequest) -> Translation:
        if not self._translator:
            raise ValueError("Translator not configured")
        # ...
        return translation  # Immer Translation oder Exception
```

**ViewModel (fängt + mapped):**
```python
class CreateTranslationViewModel(QObject):
    translation_complete = Signal(Translation)
    error_occurred = Signal(str)
    
    def create_translation(self, request: GUITranslationRequest) -> None:
        """Create translation (no return value, uses signals).
        
        Args:
            request: Translation request
            
        Signals:
            translation_complete: On success with translation
            error_occurred: On error with error message
        """
        worker = TranslationWorker(
            success_callback=lambda t: self.translation_complete.emit(t),
            error_callback=lambda e: self.error_occurred.emit(e),
            request=request
        )
        QThreadPool.globalInstance().start(worker)

# Worker fängt Exceptions im Thread
class TranslationWorker(QRunnable):
    def run(self) -> None:
        try:
            translation = self._service.translate(...)
            self._success_callback(translation)  # Signal via Callback
        except Exception as e:
            self._error_callback(str(e))  # Signal via Callback
```

**Command Layer (optional, für Undo/Redo):**
```python
class CreateTranslationCommand:
    def execute(self) -> CommandResult:
        """Execute command with result wrapping.
        
        Returns:
            CommandResult with success/failure and optional data
        """
        try:
            # Trigger ViewModel (async via signals)
            self._viewmodel.create_translation(self._request)
            return CommandResult(success=True, message="Translation started")
        except Exception as e:
            return CommandResult(success=False, message=str(e))
```

**View Layer (reagiert auf Signals):**
```python
class CreateTranslationView(QWidget):
    def _connect_signals(self) -> None:
        """Connect ViewModel signals to View slots."""
        self._viewmodel.translation_complete.connect(self._on_translation_complete)
        self._viewmodel.error_occurred.connect(self._on_error)
    
    def _on_translation_complete(self, translation: Translation) -> None:
        """Handle successful translation (10-15 LOC)."""
        QMessageBox.information(self, "Success", 
                               f"Translation '{translation.title}' created!")
        self._clear_form()
    
    def _on_error(self, error_message: str) -> None:
        """Handle translation error (5 LOC)."""
        QMessageBox.critical(self, "Error", error_message)
```

**Vorteil:**
- ✅ Core bleibt clean (nur Exceptions)
- ✅ GUI nutzt Qt-Pattern (Signals/Slots)
- ✅ Klare Responsibilities pro Layer
- ✅ Testbar (Mock Signals)

**Aufwand:** 2-3 Stunden

**Priorität:** 🟠 **HOCH**

---

### 3. Presenter Layer: Eliminiert CLI/GUI Duplikation 🎨🟡

#### Problem: CLI und GUI berechnen gleiche Daten unterschiedlich

**CLI Display:**
```python
def display_translation(translation: Translation) -> None:
    # Title berechnen (CLI)
    title = translation.title or f"Translation {str(translation.uuid)[:8]}"
    console.print(Panel(f"[bold]{title}[/bold]", ...))
    
    # Sentences iterieren (CLI)
    for idx, sentence in enumerate(translation.sentences, 1):
        console.print(f"[yellow]Sentence {idx}:[/yellow]")
        # ... Rich Console Formatting
```

**GUI Display:**
```python
class TranslationView(QWidget):
    def display_translation(self, translation: Translation) -> None:
        # Title berechnen (GUI - gleiche Logik!)
        title = translation.title or f"Translation {str(translation.uuid)[:8]}"
        self.title_label.setText(title)
        
        # Sentences iterieren (GUI - gleiche Logik!)
        for idx, sentence in enumerate(translation.sentences, 1):
            card = SentenceCard()
            card.set_index(idx)
            # ... Qt Widget Darstellung
```

**Duplikation:** Beide berechnen Title, Index, Alignment Count, etc.

#### Lösung: Gemeinsamer Presenter

**Schritt 1: Presentation Models**

```python
# src/birkenbihl/presenters/models.py (NEU!)

@dataclass(frozen=True)
class TranslationPresentation:
    """Presentation data for Translation (View-agnostic)."""
    uuid: UUID
    title: str  # Bereits bereinigt (mit Fallback)
    source_language_name: str
    target_language_name: str
    sentence_count: int
    created_at: str  # Formatiert
    updated_at: str  # Formatiert
    sentences: list['SentencePresentation']

@dataclass(frozen=True)
class SentencePresentation:
    """Presentation data for Sentence."""
    uuid: UUID
    index: int  # 1-based für Display
    source_text: str
    natural_translation: str
    alignment_count: int
    has_alignments: bool
    alignments: list[tuple[str, str]]  # (source, target) pairs
```

**Schritt 2: Presenter**

```python
# src/birkenbihl/presenters/translation_presenter.py (NEU!)

class TranslationPresenter:
    """Prepares Translation data for display (CLI/GUI agnostic).
    
    Converts domain models to presentation models with:
    - Computed fields (title with fallback, formatted dates)
    - Display indices (1-based)
    - Structured data (ready for rendering)
    """
    
    def present(self, translation: Translation) -> TranslationPresentation:
        """Convert Translation to presentation model (max 15 LOC)."""
        return TranslationPresentation(
            uuid=translation.uuid,
            title=self._format_title(translation),
            source_language_name=translation.source_language.name,
            target_language_name=translation.target_language.name,
            sentence_count=len(translation.sentences),
            created_at=self._format_datetime(translation.created_at),
            updated_at=self._format_datetime(translation.updated_at),
            sentences=[
                self._present_sentence(sentence, idx)
                for idx, sentence in enumerate(translation.sentences, 1)
            ],
        )
    
    def _format_title(self, translation: Translation) -> str:
        """Format title with fallback (3 LOC)."""
        return translation.title or f"Translation {str(translation.uuid)[:8]}"
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display (2 LOC)."""
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def _present_sentence(self, sentence: Sentence, index: int) -> SentencePresentation:
        """Convert Sentence to presentation model (10-15 LOC)."""
        alignments = [
            (wa.source_word, wa.target_word)
            for wa in sentence.word_alignments
        ]
        
        return SentencePresentation(
            uuid=sentence.uuid,
            index=index,
            source_text=sentence.source_text,
            natural_translation=sentence.natural_translation,
            alignment_count=len(alignments),
            has_alignments=bool(alignments),
            alignments=alignments,
        )
```

**Schritt 3: CLI verwendet Presenter**

```python
# src/birkenbihl/cli.py

def display_translation(translation: Translation) -> None:
    """Display translation with rich formatting (max 15 LOC)."""
    presenter = TranslationPresenter()
    data = presenter.present(translation)  # Presentation Model!
    
    # CLI-spezifische Darstellung (Rich)
    _display_header(data)
    for sentence_data in data.sentences:
        _display_sentence(sentence_data)

def _display_header(data: TranslationPresentation) -> None:
    """Display translation header (5-10 LOC)."""
    header = f"[bold cyan]{data.title}[/bold cyan]"
    lang_info = f"[dim]{data.source_language_name} → {data.target_language_name}[/dim]"
    console.print(Panel(f"{header}\n{lang_info}", border_style="cyan"))

def _display_sentence(data: SentencePresentation) -> None:
    """Display single sentence (10-15 LOC)."""
    console.print(f"\n[bold yellow]Sentence {data.index}:[/bold yellow]")
    console.print(f"  [dim]Original:[/dim]  {data.source_text}")
    console.print(f"  [dim]Natural:[/dim]   {data.natural_translation}")
    
    if data.has_alignments:
        _display_alignments(data.alignments)
```

**Schritt 4: GUI verwendet Presenter**

```python
# src/birkenbihl/gui/views/translation_view.py

class TranslationView(QWidget):
    def display_translation(self, translation: Translation) -> None:
        """Display translation with Qt widgets (max 15 LOC)."""
        presenter = TranslationPresenter()
        data = presenter.present(translation)  # Gleicher Presenter!
        
        # GUI-spezifische Darstellung (Qt)
        self._display_header(data)
        self._display_sentences(data.sentences)
    
    def _display_header(self, data: TranslationPresentation) -> None:
        """Display header widgets (5-10 LOC)."""
        self.title_label.setText(data.title)
        self.languages_label.setText(
            f"{data.source_language_name} → {data.target_language_name}"
        )
        self.date_label.setText(f"Updated: {data.updated_at}")
    
    def _display_sentences(self, sentences: list[SentencePresentation]) -> None:
        """Display sentence cards (5-10 LOC)."""
        self._clear_sentences()
        for sentence_data in sentences:
            card = self._create_sentence_card(sentence_data)
            self.sentences_layout.addWidget(card)
    
    def _create_sentence_card(self, data: SentencePresentation) -> SentenceCard:
        """Create sentence card from presentation data (10 LOC)."""
        card = SentenceCard()
        card.set_index(data.index)
        card.set_source_text(data.source_text)
        card.set_natural_translation(data.natural_translation)
        card.set_alignment_count(data.alignment_count)
        return card
```

**Vorteile:**
- ✅ Keine Duplikation (DRY)
- ✅ Konsistente Daten in CLI und GUI
- ✅ Presenter testbar ohne UI-Framework
- ✅ Einmal ändern → beide UIs profitieren

**Aufwand:** 3-4 Stunden

**Priorität:** 🟡 **MITTEL** (hoher Wert, aber nicht blockierend)

---

## 📋 Implementierungs-Checkliste

### Phase 1: Kritische Alignments (MUSS) - 1 Woche 🔴

- [ ] **1.1 Core Parameter Objects** (2h)
  - [ ] `TranslationRequest` Dataclass hinzufügen
  - [ ] `SentenceUpdateRequest` Dataclass hinzufügen
  - [ ] `TranslationService` API anpassen
  - [ ] Provider API anpassen
  - [ ] Tests anpassen

- [ ] **1.2 GUI Parameter Objects** (2h)
  - [ ] `GUITranslationRequest` Dataclass hinzufügen
  - [ ] ViewModels anpassen (create_translation, etc.)
  - [ ] Worker anpassen
  - [ ] Tests anpassen

- [ ] **1.3 CLI Parameter Objects** (1h)
  - [ ] CLI nutzt Core Requests
  - [ ] Helper-Funktionen anpassen

- [ ] **1.4 Error Handling Alignment** (3h)
  - [ ] ViewModel: Exceptions → Signals Mapping dokumentieren
  - [ ] Worker: Try/Catch Pattern
  - [ ] View: Signal-Slots für Error Display
  - [ ] Dokumentation updaten

**Erfolgskriterien Phase 1:**
- ✅ Alle Methoden max 2 Parameter (via Parameter Objects)
- ✅ GUI verwendet gleiche Request Types wie Core
- ✅ Error Handling konsistent dokumentiert
- ✅ Alle Tests laufen durch

---

### Phase 2: Qualitäts-Alignments (KANN) - 1 Woche 🟡

- [ ] **2.1 Presenter Layer** (3-4h)
  - [ ] `TranslationPresenter` Klasse erstellen
  - [ ] `TranslationPresentation` Models erstellen
  - [ ] CLI anpassen (verwendet Presenter)
  - [ ] GUI anpassen (verwendet Presenter)
  - [ ] Tests schreiben

- [ ] **2.2 Core Refactoring** (siehe Core Analyse)
  - [ ] SqliteStorage `_to_dao()` aufteilen
  - [ ] CLI `translate()` Command aufteilen

- [ ] **2.3 GUI Refactoring** (siehe GUI Analyse)
  - [ ] View Event-Handler kürzen
  - [ ] Command Pattern durchgängig

**Erfolgskriterien Phase 2:**
- ✅ Keine Code-Duplikation zwischen CLI und GUI
- ✅ Alle Funktionen <20 LOC
- ✅ Test-Coverage stabil

---

## 📊 Vorher/Nachher Vergleich

### Vorher (Aktuell)

| Aspekt | Core | CLI | GUI | Status |
|--------|------|-----|-----|--------|
| Funktionslänge | 87% <20 LOC | 60% <20 LOC | 91% <20 LOC | ⚠️ Inkonsistent |
| Parameter Count | 88% <2 | 70% <2 | 87% <2 | ⚠️ Inkonsistent |
| Parameter Objects | Fehlen | Nein | Fehlen | ❌ Inkonsistent |
| Error Handling | Exceptions | Try/Catch | Signals | ⚠️ Inkonsistent |
| Presenter/Formatter | - | Inline | Inline | ❌ Duplikation |

### Nachher (Ziel)

| Aspekt | Core | CLI | GUI | Status |
|--------|------|-----|-----|--------|
| Funktionslänge | 100% <20 LOC | 100% <20 LOC | 100% <20 LOC | ✅ Konsistent |
| Parameter Count | 100% <2 | 100% <2 | 100% <2 | ✅ Konsistent |
| Parameter Objects | Überall | Überall | Überall | ✅ Konsistent |
| Error Handling | Exceptions | Exceptions | Exceptions+Signals | ✅ Konsistent |
| Presenter/Formatter | - | Presenter | Presenter | ✅ Geteilt |

---

## 🎓 Design Patterns Alignment

### Verwendete Patterns

| Pattern | Core | CLI | GUI | Konsistent? |
|---------|------|-----|-----|-------------|
| **Protocol-based** | ✅ | ✅ | ✅ | ✅ JA |
| **Dependency Injection** | ✅ | ✅ | ✅ | ✅ JA |
| **MVVM** | - | - | ✅ | ✅ N/A |
| **Command** | - | - | ⚠️ Teilweise | ⚠️ NEIN |
| **Observer (Signals)** | - | - | ✅ | ✅ N/A |
| **Presenter** | - | ❌ Fehlt | ❌ Fehlt | ❌ NEIN |
| **Factory** | ✅ | ✅ | ✅ | ✅ JA |

### Empfehlungen

1. **Command Pattern**: Durchgängig in GUI verwenden (Undo/Redo)
2. **Presenter Pattern**: CLI + GUI nutzen gemeinsam
3. **Parameter Object Pattern**: Überall einführen

---

## 🚀 Migrations-Strategie

### Schritt-für-Schritt Migration

**Wichtig:** Pre-Release Projekt → Breaking Changes sind OK!

#### Woche 1: Core Parameter Objects 🔴

```bash
# Tag 1: Core Requests hinzufügen
# - TranslationRequest, SentenceUpdateRequest
# - In models/requests.py

# Tag 2: TranslationService API ändern
# - translate(request)
# - update_sentence_natural(request)

# Tag 3: Provider API anpassen
# - PydanticAITranslator

# Tag 4: Tests anpassen
# - Alle Service Tests
# - Alle Integration Tests

# Tag 5: CLI anpassen
# - Nutzt neue Core API
```

#### Woche 2: GUI Parameter Objects & Error Handling 🟠

```bash
# Tag 1: GUI Requests hinzufügen
# - GUITranslationRequest
# - In gui/models/requests.py

# Tag 2-3: ViewModels anpassen
# - CreateTranslationViewModel
# - UpdateSentenceViewModel

# Tag 4: Error Handling standardisieren
# - Workers: Try/Catch
# - ViewModels: Exception → Signal

# Tag 5: Tests anpassen
# - Alle GUI Tests
```

#### Woche 3: Presenter & Polish 🟡

```bash
# Tag 1-2: Presenter implementieren
# - TranslationPresenter
# - Presentation Models

# Tag 3: CLI nutzt Presenter
# - display_translation() refactored

# Tag 4: GUI nutzt Presenter
# - TranslationView refactored

# Tag 5: Tests & Dokumentation
# - Presenter Tests
# - README aktualisieren
```

**Vorteil:** Schrittweise Migration, jeder Schritt testbar

---

## 💡 Best Practices für zukünftige Features

### 1. Vor dem Schreiben

- [ ] Funktionslänge planen (max 20 LOC)
- [ ] Parameter Objects für >2 Parameter
- [ ] Error Handling Strategie festlegen
- [ ] Presenter nötig? (bei Display-Logik)

### 2. Während des Schreibens

- [ ] Nach jedem Commit: Code Review
- [ ] Ruff + Pyright laufen lassen
- [ ] Tests ZUERST schreiben (TDD)

### 3. Nach dem Schreiben

- [ ] Clean Code Checkliste durchgehen
- [ ] Integration Tests hinzufügen
- [ ] Dokumentation schreiben

---

## 📚 Code Review Checkliste

### Vor dem Merge - Alle PRs müssen erfüllen:

#### Clean Code ✅
- [ ] Alle Funktionen 5-20 LOC
- [ ] Alle Parameter 0-2 (oder Parameter Object)
- [ ] Keine Code-Duplikation (DRY)
- [ ] Klare, aussagekräftige Namen

#### Architektur ✅
- [ ] SOLID-Prinzipien befolgt
- [ ] Protocol-based Abstractions verwendet
- [ ] Dependency Injection verwendet
- [ ] Keine Business Logic in Views/Commands

#### Konsistenz ✅
- [ ] Core, CLI, GUI verwenden gleiche Parameter Objects
- [ ] Error Handling konsistent
- [ ] Presenter/Formatter wiederverwendet (wenn Display-Logik)

#### Tests ✅
- [ ] Unit Tests vorhanden
- [ ] Coverage >80% für neue Code
- [ ] Edge Cases getestet
- [ ] Negative Cases getestet

#### Dokumentation ✅
- [ ] Docstrings für alle öffentlichen Methoden
- [ ] Type Hints überall
- [ ] README updated (wenn neue Features)

---

## 📊 Gesamt-Scores

### Nach Alignment (Ziel)

| Schicht | Funktionslänge | Parameter | Error Handling | Gesamt |
|---------|----------------|-----------|----------------|--------|
| **Core** | ⭐⭐⭐⭐⭐ 100% | ⭐⭐⭐⭐⭐ 100% | ⭐⭐⭐⭐⭐ Exceptions | ⭐⭐⭐⭐⭐ |
| **CLI** | ⭐⭐⭐⭐⭐ 100% | ⭐⭐⭐⭐⭐ 100% | ⭐⭐⭐⭐⭐ Exceptions | ⭐⭐⭐⭐⭐ |
| **GUI** | ⭐⭐⭐⭐⭐ 100% | ⭐⭐⭐⭐⭐ 100% | ⭐⭐⭐⭐⭐ Signals | ⭐⭐⭐⭐⭐ |

---

## 💡 Zusammenfassung

### Kritische Änderungen (MUSS - 1 Woche)

1. ✅ **Parameter Objects**: Core + GUI + CLI
2. ✅ **Error Handling**: Dokumentierte Strategie
3. ✅ **Funktionslängen**: Refactoring (Core SQL, CLI, GUI Views)

### Empfohlene Änderungen (KANN - 1 Woche)

1. 🎨 **Presenter**: CLI + GUI gemeinsam
2. 📊 **Command Pattern**: Durchgängig in GUI
3. 🧪 **Tests**: Mehr Coverage

### Zeitaufwand

- **Phase 1 (MUSS):** 1 Woche
- **Phase 2 (KANN):** 1 Woche
- **Total:** 2 Wochen

### Erfolgskriterien

- ✅ 100% Funktionen unter 20 LOC
- ✅ 100% Parameter unter 2 (via Parameter Objects)
- ✅ Keine Code-Duplikation (DRY)
- ✅ Konsistentes Error Handling
- ✅ Tests >80% Coverage überall

**Nach diesen Änderungen:** Core, CLI und GUI erfüllen alle dieselben Clean Code Standards! 🎉

---

**Stand:** 15. Oktober 2025  
**Autor:** Claude (AI Assistant)  
**Nächster Schritt:** Phase 1 Implementation starten  
**Geschätzte Zeit bis 100% Compliance:** 2 Wochen
