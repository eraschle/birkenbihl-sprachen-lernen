# Birkenbihl Refactoring Plan

**Erstellt:** 16. Oktober 2025
**Basis:** Code-Analyse vom 15. Oktober 2025
**Status:** 🚧 IN PROGRESS

---

## 🎯 Ziele

Code-Qualität auf 100% Clean Code Compliance bringen:

- ✅ Alle Funktionen <20 LOC
- ✅ Alle Parameter ≤2-3 (mit Parameter Objects)
- ✅ Typ-Hints überall (Code + Tests)
- ✅ Test Coverage >80%
- ✅ Keine Code-Duplikation
- ✅ Presenter Layer für CLI (GUI später)

## 📊 Kontext

- **Breaking Changes:** Erlaubt - Pre-Release Projekt
- **UI-Code:** Settings + Widgets bleiben, Rest wurde gelöscht
- **Parameter-Limit:** Max 2-3 (Ausnahmen bei 3 OK)
- **Test-Strategie:** Tests MÜSSEN vor jedem Commit laufen
- **Commits:** Keine Verweise auf Claude Code

---

## 📋 Phase 1: Kritische Refactorings (5-7 Tage)

### 1.1 SqliteStorage Refactoring 🔴

**Status:** ✅ DONE

**Problem:**
- `_to_dao()`: 42 LOC (KRITISCH)
- `_from_dao()`: 38 LOC (KRITISCH)

**Lösung:**

Aufteilung in jeweils 5 kleinere Funktionen:

```python
# _to_dao() Gruppe (42 LOC → 5 Funktionen)
def _to_dao(translation: Translation) -> TranslationDAO:
    # 4 LOC - orchestriert nur
    pass

def _create_translation_dao_base(translation: Translation) -> TranslationDAO:
    # 8 LOC - erstellt base DAO ohne sentences
    pass

def _create_sentence_daos(translation: Translation) -> list[SentenceDAO]:
    # 3 LOC - list comprehension
    pass

def _create_sentence_dao(sentence: Sentence, translation_id: UUID) -> SentenceDAO:
    # 12 LOC - erstellt einzelnes SentenceDAO
    pass

def _create_alignment_daos(sentence_id: UUID, alignments: list[WordAlignment]) -> list[WordAlignmentDAO]:
    # 10 LOC - erstellt alignment DAOs
    pass
```

**Schritte:**
- [ ] `_to_dao()` refactoren
- [ ] `_from_dao()` refactoren (analog)
- [ ] Tests in `tests/storage/test_sqlite_storage.py` anpassen
- [ ] Typ-Hints in Tests hinzufügen
- [ ] Tests ausführen: `pytest tests/storage/test_sqlite_storage.py -v`
- [ ] Alle Tests müssen bestehen

**Erfolgskriterien:**
- ✅ Alle Funktionen <20 LOC
- ✅ Tests laufen (100% pass)
- ✅ Typ-Hints vorhanden

**Commit Message:**
```
refactor(storage): break down SqliteStorage DAO conversion methods

- Split _to_dao() from 42 LOC into 5 functions (~10 LOC each)
- Split _from_dao() from 38 LOC into 5 functions (~10 LOC each)
- Add type hints to all storage tests
- All tests passing
```

**Abgeschlossen:** ✅ JA
**Commit Hash:** 8393907
**Datum:** 16. Oktober 2025

---

### 1.2 CLI Refactoring 🔴

**Status:** ✅ DONE

**Problem:**
- `translate()` Command: 50 LOC (KRITISCH)

**Lösung:**

Aufteilung in 1 Command + 4 Helper-Funktionen:

```python
@cli.command()
def translate(text, source, target, title, provider, storage):
    # ~15 LOC - orchestriert nur
    pass

def _setup_translation_config(provider: str | None, storage: str | None) -> CLIConfig:
    # ~12 LOC - Setup Services
    pass

def _resolve_source_language(config: CLIConfig, text: str, source: str | None) -> Language:
    # ~15 LOC - Auto-detect oder validate
    pass

def _perform_translation(config: CLIConfig, text: str, source_lang: Language,
                        target: str, title: str) -> Translation:
    # ~8 LOC - Execute translation
    pass

def _display_translation(translation: Translation) -> None:
    # ~15 LOC - Rich Console Display (später Presenter)
    pass
```

**Schritte:**
- [ ] Helper-Funktionen extrahieren
- [ ] Command vereinfachen
- [ ] Tests in `tests/cli/` anpassen
- [ ] Typ-Hints in CLI-Tests hinzufügen
- [ ] Tests ausführen: `pytest tests/cli/ -v`

**Erfolgskriterien:**
- ✅ translate() Command <20 LOC
- ✅ Helper-Funktionen <20 LOC
- ✅ Tests laufen
- ✅ Typ-Hints vorhanden

**Commit Message:**
```
refactor(cli): break down translate command into helper functions

- Extract helper functions from 50 LOC translate command
- _load_settings_service: settings initialization (6 LOC)
- _select_provider: provider selection logic (16 LOC)
- _create_translation_service: service setup (6 LOC)
- _execute_translation: translation execution (8 LOC)
- translate command reduced to 14 LOC
- Add complete type hints (ProviderConfig, TranslationService)
- Pyright clean (0 errors)
```

**Abgeschlossen:** ✅ JA
**Commit Hash:** (wird eingefügt)
**Datum:** 16. Oktober 2025

---

### 1.3 Core Parameter Objects 🔴

**Status:** ⬜ TODO

**Neu:** `src/birkenbihl/models/requests.py`

**Lösung:**

```python
from dataclasses import dataclass
from uuid import UUID
from birkenbihl.models.language import Language
from birkenbihl.models.settings import ProviderConfig

@dataclass
class TranslationRequest:
    """Request for translating text using Birkenbihl method.

    Args:
        text: Text to translate
        source_lang: Source language
        target_lang: Target language
        title: Optional title for the translation
    """
    text: str
    source_lang: Language
    target_lang: Language
    title: str = ""

@dataclass
class SentenceUpdateRequest:
    """Request for updating sentence translation.

    Args:
        translation_id: UUID of the translation
        sentence_idx: Index of sentence to update (0-based)
        new_text: New natural translation text
        provider: Provider config for regenerating alignments
    """
    translation_id: UUID
    sentence_idx: int
    new_text: str
    provider: ProviderConfig
```

**Schritte:**
- [ ] Datei `src/birkenbihl/models/requests.py` erstellen
- [ ] Parameter Objects definieren
- [ ] Imports hinzufügen
- [ ] Docstrings schreiben

**Erfolgskriterien:**
- ✅ Datei existiert
- ✅ Typ-Hints vollständig
- ✅ Docstrings vorhanden

**Commit Message:**
```
feat(models): add parameter objects for translation requests

- Add TranslationRequest for translate operations
- Add SentenceUpdateRequest for sentence editing
- Reduce parameter count from 4-5 to 1 per method
- Full type hints and docstrings
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

### 1.4 TranslationService API Anpassung 🔴

**Status:** ⬜ TODO

**Änderungen:**

```python
# Vorher: 4 Parameter
def translate(self, text: str, source_lang: Language,
              target_lang: Language, title: str) -> Translation:
    pass

# Nachher: 1 Parameter
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
```

```python
# Vorher: 4 Parameter
def update_sentence_natural(self, translation_id: UUID, sentence_idx: int,
                           new_text: str, provider: ProviderConfig) -> Translation:
    pass

# Nachher: 1 Parameter + Hilfsfunktionen
def update_sentence_natural(self, request: SentenceUpdateRequest) -> Translation:
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

def _load_translation(self, translation_id: UUID) -> Translation:
    """Load translation or raise error."""
    translation = self.get_translation(translation_id)
    if not translation:
        raise NotFoundError(f"Translation {translation_id} not found")
    return translation

def _get_sentence(self, translation: Translation, index: int) -> Sentence:
    """Get sentence by index or raise error."""
    if index < 0 or index >= len(translation.sentences):
        raise ValueError(f"Sentence index {index} out of range")
    return translation.sentences[index]
```

**Schritte:**
- [ ] `TranslationService.translate()` API ändern
- [ ] `TranslationService.update_sentence_natural()` refactoren
- [ ] Hilfsfunktionen extrahieren
- [ ] Tests in `tests/services/test_translation_service.py` anpassen
- [ ] Typ-Hints in Tests hinzufügen
- [ ] Tests ausführen: `pytest tests/services/test_translation_service.py -v`

**Erfolgskriterien:**
- ✅ Alle Methoden ≤2 Parameter
- ✅ Hilfsfunktionen <20 LOC
- ✅ Tests laufen
- ✅ Typ-Hints vorhanden

**Commit Message:**
```
refactor(services): use parameter objects in TranslationService

- Change translate() to accept TranslationRequest
- Change update_sentence_natural() to accept SentenceUpdateRequest
- Extract helper functions: _load_translation, _get_sentence
- Add type hints to service tests
- All tests passing
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

### 1.5 Provider API Anpassung 🟠

**Status:** ⬜ TODO

**Prüfung:**
- PydanticAITranslator auf Kompatibilität mit neuen Request Objects prüfen
- Laut Analyse: Bereits gut implementiert (⭐⭐⭐⭐⭐)
- Evtl. minimale Anpassungen

**Schritte:**
- [ ] Provider-Code prüfen
- [ ] API an TranslationRequest anpassen (falls nötig)
- [ ] Tests in `tests/providers/` anpassen
- [ ] Typ-Hints hinzufügen
- [ ] Tests ausführen: `pytest tests/providers/ -v`

**Erfolgskriterien:**
- ✅ Provider nutzen Request Objects (oder bleiben unverändert)
- ✅ Tests laufen
- ✅ Typ-Hints vorhanden

**Commit Message:**
```
refactor(providers): align with new parameter objects

- Update provider interfaces for TranslationRequest
- Add type hints to provider tests
- All tests passing
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

### 1.6 Alle Core Tests anpassen 🔴

**Status:** ⬜ TODO

**Fokus:**
- Typ-Hints in ALLEN Test-Funktionen
- Fixtures mit Typ-Hints
- Tests an neue API anpassen

**Beispiel:**

```python
# Vorher
def test_translate(translation_service, mock_translator):
    result = translation_service.translate("text", en, de, "title")
    assert result.title == "title"

# Nachher
def test_translate(
    translation_service: TranslationService,
    mock_translator: ITranslationProvider
) -> None:
    request = TranslationRequest(
        text="text",
        source_lang=en,
        target_lang=de,
        title="title"
    )
    result = translation_service.translate(request)
    assert result.title == "title"
```

**Betroffene Test-Dateien:**
- `tests/models/test_translation.py`
- `tests/models/test_settings.py`
- `tests/services/test_translation_service.py`
- `tests/services/test_settings_service.py`
- `tests/storage/test_json_storage.py`
- `tests/storage/test_sqlite_storage.py`
- `tests/storage/test_settings_storage*.py`
- `tests/providers/test_*.py`
- `tests/integration/test_*.py`

**Schritte:**
- [ ] Alle Test-Dateien durchgehen
- [ ] Typ-Hints für Funktionen hinzufügen
- [ ] Typ-Hints für Fixtures hinzufügen
- [ ] An neue API anpassen (Request Objects)
- [ ] Tests ausführen: `pytest -v`
- [ ] Coverage prüfen: `pytest --cov`

**Erfolgskriterien:**
- ✅ Alle Tests haben Typ-Hints
- ✅ Alle Fixtures haben Typ-Hints
- ✅ Coverage >80%
- ✅ Alle Tests bestehen

**Commit Message:**
```
test: add type hints and adapt to new API

- Add type hints to all test functions
- Add type hints to all fixtures
- Adapt tests to use parameter objects
- Coverage remains >80%
- All tests passing
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

## 🎨 Phase 2: Presenter & Test-Qualität (3-5 Tage)

### 2.1 TranslationPresenter implementieren 🟡

**Status:** ⬜ TODO

**Neue Dateien:**
- `src/birkenbihl/presenters/__init__.py`
- `src/birkenbihl/presenters/models.py`
- `src/birkenbihl/presenters/translation_presenter.py`

**Inhalt `presenters/models.py`:**

```python
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class SentencePresentation:
    """Presentation data for a single sentence."""
    uuid: UUID
    index: int  # 1-based für Display
    source_text: str
    natural_translation: str
    alignment_count: int
    has_alignments: bool
    alignments: list[tuple[str, str]]  # (source, target) pairs

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
    sentences: list[SentencePresentation]
```

**Inhalt `presenters/translation_presenter.py`:**

```python
from datetime import datetime
from birkenbihl.models.translation import Translation, Sentence
from birkenbihl.presenters.models import TranslationPresentation, SentencePresentation

class TranslationPresenter:
    """Prepares Translation data for display (CLI/GUI agnostic).

    Converts domain models to presentation models with:
    - Computed fields (title with fallback, formatted dates)
    - Display indices (1-based)
    - Structured data (ready for rendering)
    """

    def present(self, translation: Translation) -> TranslationPresentation:
        """Convert Translation to presentation model."""
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
        """Format title with fallback."""
        return translation.title or f"Translation {str(translation.uuid)[:8]}"

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display."""
        return dt.strftime("%Y-%m-%d %H:%M")

    def _present_sentence(self, sentence: Sentence, index: int) -> SentencePresentation:
        """Convert Sentence to presentation model."""
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

**Schritte:**
- [ ] Presenter Package erstellen
- [ ] Presentation Models definieren
- [ ] TranslationPresenter implementieren
- [ ] Tests schreiben: `tests/presenters/test_translation_presenter.py`
- [ ] Tests ausführen: `pytest tests/presenters/ -v`

**Erfolgskriterien:**
- ✅ Alle Funktionen <20 LOC
- ✅ Typ-Hints vollständig
- ✅ Tests vorhanden und bestehen
- ✅ Docstrings vorhanden

**Commit Message:**
```
feat(presenters): add TranslationPresenter layer

- Add presentation models (TranslationPresentation, SentencePresentation)
- Add TranslationPresenter for view-agnostic data preparation
- Eliminates display logic duplication between CLI/GUI
- Full type hints and docstrings
- Tests passing
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

### 2.2 CLI nutzt Presenter 🟡

**Status:** ⬜ TODO

**Änderungen in `src/birkenbihl/cli.py`:**

```python
from birkenbihl.presenters.translation_presenter import TranslationPresenter
from birkenbihl.presenters.models import TranslationPresentation, SentencePresentation

def _display_translation(translation: Translation) -> None:
    """Display translation with rich formatting."""
    presenter = TranslationPresenter()
    data = presenter.present(translation)

    _display_header(data)
    for sentence_data in data.sentences:
        _display_sentence(sentence_data)

def _display_header(data: TranslationPresentation) -> None:
    """Display translation header."""
    header = f"[bold cyan]{data.title}[/bold cyan]"
    lang_info = f"[dim]{data.source_language_name} → {data.target_language_name}[/dim]"
    console.print(Panel(f"{header}\n{lang_info}", border_style="cyan"))

def _display_sentence(data: SentencePresentation) -> None:
    """Display single sentence."""
    console.print(f"\n[bold yellow]Sentence {data.index}:[/bold yellow]")
    console.print(f"  [dim]Original:[/dim]  {data.source_text}")
    console.print(f"  [dim]Natural:[/dim]   {data.natural_translation}")

    if data.has_alignments:
        _display_alignments(data.alignments)

def _display_alignments(alignments: list[tuple[str, str]]) -> None:
    """Display word alignments."""
    console.print("  [dim]Alignments:[/dim]")
    for source, target in alignments:
        console.print(f"    {source} → {target}")
```

**Schritte:**
- [ ] CLI `_display_translation()` refactoren
- [ ] Helper-Funktionen für Display hinzufügen
- [ ] Presenter verwenden
- [ ] Tests anpassen
- [ ] Tests ausführen: `pytest tests/cli/ -v`

**Erfolgskriterien:**
- ✅ Keine Display-Logik-Duplikation
- ✅ Presenter wird verwendet
- ✅ Alle Funktionen <20 LOC
- ✅ Tests bestehen

**Commit Message:**
```
refactor(cli): use TranslationPresenter for display logic

- Refactor _display_translation to use presenter
- Extract display helper functions
- Eliminate display logic duplication
- All tests passing
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

### 2.3 Test-Verbesserungen 🟡

**Status:** ⬜ TODO

**Fokus:**
- Test-Duplikation reduzieren
- Parametrized Tests wo sinnvoll
- Mehr negative Tests (Edge Cases)
- Sicherstellen: ALLE Tests mit Typ-Hints

**Beispiele für Verbesserungen:**

```python
# Parametrized Tests für mehrere Szenarien
@pytest.mark.parametrize("text,expected_lang", [
    ("Hello world", Language.ENGLISH),
    ("Hola mundo", Language.SPANISH),
    ("Guten Tag", Language.GERMAN),
])
def test_language_detection(
    translator: ITranslationProvider,
    text: str,
    expected_lang: Language
) -> None:
    detected = translator.detect_language(text)
    assert detected == expected_lang
```

```python
# Negative Tests
def test_translate_empty_string(
    translation_service: TranslationService
) -> None:
    request = TranslationRequest(text="", source_lang=en, target_lang=de)
    with pytest.raises(ValueError, match="Text cannot be empty"):
        translation_service.translate(request)

def test_get_nonexistent_translation(
    translation_service: TranslationService
) -> None:
    result = translation_service.get_translation(uuid4())
    assert result is None
```

**Schritte:**
- [ ] Duplikate in Tests identifizieren
- [ ] Gemeinsame Fixtures extrahieren
- [ ] Parametrized Tests hinzufügen
- [ ] Negative Tests hinzufügen
- [ ] Typ-Hints verifizieren
- [ ] Tests ausführen: `pytest -v`
- [ ] Coverage prüfen: `pytest --cov`

**Erfolgskriterien:**
- ✅ Weniger Test-Duplikation
- ✅ Mehr Edge Cases getestet
- ✅ Coverage >80%
- ✅ Alle Tests bestehen

**Commit Message:**
```
test: reduce duplication and add edge case tests

- Extract common test fixtures
- Add parametrized tests for multiple scenarios
- Add negative tests for edge cases
- Verify type hints in all tests
- Coverage >80%
- All tests passing
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

## ✅ Phase 3: Final Verification (2-3 Tage)

### 3.1 Code Quality Check ✅

**Status:** ⬜ TODO

**Checks:**

```bash
# Ruff Linting
ruff check .

# Ruff Formatting
ruff format .

# Pyright Type Checking
pyright
```

**Schritte:**
- [ ] Ruff check ausführen
- [ ] Alle Warnungen beheben
- [ ] Ruff format ausführen
- [ ] Pyright ausführen
- [ ] Alle Type-Errors beheben

**Erfolgskriterien:**
- ✅ Ruff clean (keine Fehler)
- ✅ Pyright clean (keine Fehler)
- ✅ Code formatiert

---

### 3.2 Test Coverage ✅

**Status:** ⬜ TODO

```bash
pytest --cov --cov-report=term-missing
```

**Schritte:**
- [ ] Coverage-Report generieren
- [ ] Fehlende Coverage identifizieren
- [ ] Tests ergänzen (falls <80%)
- [ ] Final Test-Run

**Erfolgskriterien:**
- ✅ Coverage >80% (gesamt)
- ✅ Alle kritischen Pfade getestet

---

### 3.3 Manual Code Review ✅

**Status:** ⬜ TODO

**Checkliste:**
- [ ] Alle Funktionen <20 LOC?
- [ ] Alle Parameter ≤3?
- [ ] Typ-Hints überall (Code + Tests)?
- [ ] Keine Code-Duplikation?
- [ ] Docstrings für öffentliche APIs?
- [ ] Tests laufen alle?

**Erfolgskriterien:**
- ✅ Alle Checkboxen erfüllt

---

### 3.4 Dokumentation ✅

**Status:** ⬜ TODO

**Zu aktualisieren:**
- [ ] README.md (falls nötig)
- [ ] CLAUDE.md (falls nötig)
- [ ] Dieser Refactoring-Plan (finaler Status)

**Commit Message:**
```
docs: update documentation after refactoring

- Update README with new API changes
- Add notes about parameter objects
- Mark refactoring plan as completed
```

**Abgeschlossen:** ⬜ NEIN
**Commit Hash:** -
**Datum:** -

---

## 📊 Fortschritts-Tracking

### Phase 1 (Kritisch)
- [x] 1.1 SqliteStorage Refactoring
- [x] 1.2 CLI Refactoring
- [ ] 1.3 Core Parameter Objects
- [ ] 1.4 TranslationService API
- [ ] 1.5 Provider API
- [ ] 1.6 Tests anpassen

### Phase 2 (Qualität)
- [ ] 2.1 TranslationPresenter
- [ ] 2.2 CLI Presenter Integration
- [ ] 2.3 Test-Verbesserungen

### Phase 3 (Verification)
- [ ] 3.1 Code Quality Check
- [ ] 3.2 Test Coverage
- [ ] 3.3 Manual Review
- [ ] 3.4 Dokumentation

---

## 🎯 Finale Erfolgskriterien

Nach Abschluss aller Phasen:

- ✅ **100% Funktionen <20 LOC**
- ✅ **100% Parameter ≤2-3**
- ✅ **Typ-Hints überall** (Code + Tests)
- ✅ **Test Coverage >80%**
- ✅ **Keine Code-Duplikation**
- ✅ **Presenter Layer** vorhanden
- ✅ **Alle Tests laufen**
- ✅ **Ruff + Pyright clean**
- ✅ **Basis für UI-Development** bereit

---

## 📝 Notizen

### Entscheidungen
- Parameter-Limit: 2-3 (nicht strikt 2, Ausnahmen bei 3 OK)
- Settings UI bleibt unberührt (API kann angepasst werden)
- Tests MÜSSEN vor jedem Commit laufen
- Keine Claude Code Verweise in Commits

### Lessons Learned
_Wird während der Implementation befüllt_

---

**Letzte Aktualisierung:** 16. Oktober 2025
**Status:** 🚧 IN PROGRESS
**Nächster Schritt:** Phase 1.1 - SqliteStorage Refactoring
