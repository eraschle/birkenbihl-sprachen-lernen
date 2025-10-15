# Alignment System - Dokumentation & Erkenntnisse

**Datum:** 2025-10-16
**Status:** Vor Neuentwicklung - System wird gelöscht und neu aufgebaut

## Zweck dieses Dokuments

Dieses Dokument sichert das Wissen über das alte Alignment-System, bevor es gelöscht wird.
Es dokumentiert die Funktionsweise, Architektur, bekannte Bugs und wichtige Design-Entscheidungen.

---

## System-Übersicht

Das Alignment-System ermöglicht die manuelle Bearbeitung von Wort-für-Wort-Zuordnungen
zwischen Quellsprache und Zielsprache nach der Birkenbihl-Methode.

### Hauptkomponenten

1. **AlignmentEditor** - Hauptwidget mit Validierung und Controller-Integration
2. **TagWidget** - Einzelne Wort-Tags mit Löschen-Button
3. **TagContainer** - Container für Tags + ComboBox pro Quellwort
4. **AlignmentController** - Zentrale Zustandsverwaltung
5. **AlignmentHooks** - Transformation von UI-Daten zu Speicher-Format
6. **EditorView** - Oberste View mit 3 Modi (View/Edit Natural/Edit Alignment)
7. **TranslationEditorViewModel** - State Management und Business Logic

---

## Architektur-Muster

### MVVM (Model-View-ViewModel)
- **Model:** `Translation`, `Sentence`, `WordAlignment`
- **View:** `EditorView`, `AlignmentEditor`, `TagWidget`, `TagContainer`
- **ViewModel:** `TranslationEditorViewModel`

### Observer Pattern
- **Controller** ist Subject, **TagContainers** sind Observer
- Signal: `mappings_changed` triggert automatische UI-Synchronisation

### Single Source of Truth
- `AlignmentController` speichert kompletten Zustand
- UI-Widgets sind zustandslos und rendern aus Controller-Daten

---

## Datenfluss

### Format-Konvertierung

**Storage Format (WordAlignment):**
```python
WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2)
```

**Controller Format (dict):**
```python
{"extrañaré": ["werde", "vermissen"]}
```

**Transformation:**
1. **Storage → Controller:** `_build_mappings_from_alignments()` splittet Bindestriche
2. **Controller → Storage:** `HyphenateMultiWordsHook` joined mit Bindestrichen

### User Workflow: Wort zuweisen

```
1. User wählt Wort aus ComboBox
   ↓
2. TagContainer.activated signal → _on_word_selected_by_user()
   ↓
3. controller.add_word(source, target)
   ↓
4. Controller emittiert mappings_changed
   ↓
5. ALLE TagContainers empfangen Signal → _refresh_ui()
   ↓
6. Tags neu rendern, ComboBoxen aktualisieren
```

### User Workflow: Übernehmen

```
1. User klickt "Übernehmen"
   ↓
2. AlignmentEditor._on_apply()
   ↓
3. _build_alignments() → AlignmentHookManager
   ↓
4. Hook joined Multi-Wörter mit Bindestrichen
   ↓
5. Validierung via validate_alignment_complete()
   ↓
6. Bei Erfolg: alignment_changed.emit(alignments)
   ↓
7. EditorView empfängt Signal → viewmodel.update_alignment()
   ↓
8. ViewModel markiert has_unsaved_changes=True
   ↓
9. Auto-Wechsel zu "view" Mode
```

---

## Kritische Bugs & Probleme

### ❌ BUG 1: Punktuation in target_words

**Datei:** `alignment_editor.py:89`

**Problem:**
```python
target_words = self._sentence.natural_translation.split()
# Ergebnis: ["Ich", "werde", "dich", "vermissen."]  ← MIT PUNKT!
```

**Auswirkung:**
- Controller denkt "vermissen." (mit Punkt) ist verfügbar
- Aber Alignments haben "vermissen" (ohne Punkt)
- User sieht beide als verfügbar → Duplikate in ComboBox

**Lösung:**
```python
import re
text_no_punct = re.sub(r"[^\w\s'\-]", "", self._sentence.natural_translation)
target_words = text_no_punct.split()
```

---

### ❌ BUG 2: Unnötige Sortierung

**Datei:** `alignment_editor.py:118-119`

**Problem:**
```python
sorted_alignments = sorted(self._sentence.word_alignments, key=lambda a: a.position)
```

**Grund:**
Wurde hinzugefügt gegen Benutzer-Anweisung "NICHT SORTIEREN"

**Auswirkung:**
- Maskiert fehlerhafte Daten (falsche Position-Werte)
- Performance-Overhead
- Position-Werte werden bei jedem Speichern neu nummeriert (0,1,2...)

**Lösung:**
Einfach entfernen! Daten sollten bereits korrekt sortiert sein.

---

### ❌ BUG 3: ComboBox Signal

**Datei:** `tag_container.py:49`

**Problem:**
```python
self._combobox.activated.connect(self._on_word_selected_by_user)
```

`activated` feuert nicht bei erneuter Auswahl des gleichen Items.

**Lösung:**
War eigentlich richtig gewählt, aber könnte zu `currentIndexChanged` geändert werden
mit zusätzlicher Prüfung gegen programmatische Änderungen.

---

### ❌ BUG 4: Inkonsistente Normalisierung

**Dateien:**
- `validation.py:87` - `_extract_words()`
- `validation.py:152` - `_extract_alignment_words()`

**Problem:**
Unterschiedliche Regex-Patterns für gleiche Aufgabe.

**Lösung:**
Zentrale Normalisierungs-Funktion erstellen, die beide verwenden.

---

## Was funktioniert GUT

### ✅ TagWidget Button-Sichtbarkeit
- Button ist permanent sichtbar (20x20px, grauer Hintergrund)
- Hover-Effekt: Wird rot (#f44336)
- User kann sofort löschen ohne Hover

### ✅ Controller State Management
- Single Source of Truth
- Automatische UI-Synchronisation via Signals
- Verhindert Duplikate korrekt

### ✅ Memory Management
- `setParent(None)` + `deleteLater()` verhindert Leaks
- Rekursives Layout-Clearing

### ✅ Validierung vor Übernehmen
- `_on_apply()` validiert BEVOR es speichert
- Bei Fehler wird NICHT übernommen
- User bekommt klare Fehlermeldung

---

## Design-Entscheidungen

### Warum Bindestriche?

**Problem:** Ein Quellwort kann mehreren Zielwörtern zugeordnet werden.

**Lösung:** Speichern als "werde-vermissen" (Bindestrich-Notation)

**Vorteile:**
- Einfaches Speicher-Format (ein String pro WordAlignment)
- Kompatibel mit Birkenbihl-Methode
- Leicht zu parsen (split auf "-")

**Nachteile:**
- Funktioniert nicht bei Wörtern die selbst Bindestriche haben
- Zwei-Format-System (UI vs. Storage) ist komplexer

### Warum AlignmentController?

**Grund:** Verhindere Race Conditions und Inkonsistenzen.

**Ohne Controller:**
- Jeder TagContainer müsste prüfen, ob Wort schon vergeben ist
- Zwischen Prüfung und Zuweisung könnte anderer Container dasselbe tun
- UI-Komponenten müssten sich gegenseitig benachrichtigen

**Mit Controller:**
- Zentrale Prüfung atomar
- Ein Signal für alle → automatische Synchronisation
- Einfacher zu testen

---

## Test-Erkenntnisse

### Was getestet wurde
- TagWidget Erstellung mit verschiedenen Texten
- Controller add/remove/get_available Operationen
- Hook-Transformation (Listen zu Bindestrichen)
- Validierung mit fehlenden/extra Wörtern

### Was NICHT getestet wurde
- Integration mit echter Datenbank
- Performance bei vielen Wörtern (>100)
- Unicode-Handling (Emojis, asiatische Zeichen)
- Undo/Redo Funktionalität

---

## Lessons Learned

### 🎯 Was beim Neustart BESSER machen

1. **Zentrale Normalisierung:**
   ```python
   def normalize_word(word: str) -> str:
       """Remove punctuation, lowercase, consistent everywhere."""
       return re.sub(r"[^\w'\-]", "", word.lower())
   ```

2. **Keine versteckte Sortierung:**
   - Daten kommen sortiert aus DB
   - Wenn nicht sortiert → Fehler werfen, nicht maskieren!

3. **Ein Format für alle:**
   - Entweder immer Listen ODER immer Bindestriche
   - Nicht hin und her konvertieren

4. **Bessere Fehlermeldungen:**
   - "Wort 'vermissen.' (mit Punkt!) ist nicht in Alignments"
   - Statt nur "Fehlendes Wort: vermissen"

5. **Validierung an EINER Stelle:**
   - Vor Speichern im ViewModel
   - Nicht zusätzlich im Widget

### 🎯 Was BEIBEHALTEN

1. **Controller-Pattern** - Funktioniert sehr gut
2. **Tag-basierte UI** - User-freundlich
3. **Signal-basierte Updates** - Automatische Synchronisation
4. **Memory Management** - Korrekt implementiert
5. **Hook-System** - Gute Erweiterbarkeit

---

## Datei-Liste (zum Löschen)

### Alignment-spezifisch:
- src/birkenbihl/gui/widgets/alignment_editor.py
- src/birkenbihl/gui/widgets/alignment_preview.py
- src/birkenbihl/gui/widgets/tag_widget.py
- src/birkenbihl/gui/widgets/tag_container.py
- src/birkenbihl/gui/controllers/alignment_controller.py
- src/birkenbihl/gui/hooks/alignment_hooks.py
- src/birkenbihl/gui/components/alignment_preview.py
- src/birkenbihl/gui/views/editor_view.py
- src/birkenbihl/gui/models/editor_viewmodel.py
- tests/gui/widgets/test_alignment_editor.py
- tests/gui/widgets/test_alignment_preview.py
- tests/gui/widgets/test_tag_widget.py
- tests/gui/widgets/test_tag_container.py
- tests/gui/controllers/test_alignment_controller.py
- tests/gui/hooks/test_alignment_hooks.py
- tests/gui/models/test_editor_viewmodel.py

### Andere GUI (Nicht-Settings):
- src/birkenbihl/gui/main.py
- src/birkenbihl/gui/views/main_window.py
- src/birkenbihl/gui/views/translation_view.py
- src/birkenbihl/gui/views/create_view.py
- src/birkenbihl/gui/models/translation_viewmodel.py
- src/birkenbihl/gui/models/ui_state.py
- src/birkenbihl/gui/viewmodels/create_vm.py
- src/birkenbihl/gui/widgets/sentence_card.py
- src/birkenbihl/gui/widgets/language_combo.py
- src/birkenbihl/gui/widgets/language_selector.py
- src/birkenbihl/gui/widgets/progress_widget.py
- src/birkenbihl/gui/widgets/provider_selector.py
- src/birkenbihl/gui/commands/editor_commands.py
- src/birkenbihl/gui/commands/translation_commands.py
- src/birkenbihl/gui/services/translation_ui_service.py
- src/birkenbihl/gui/utils/async_helper.py
- src/birkenbihl/gui/components/progress_widget.py
- src/birkenbihl/gui/components/provider_selector.py
- src/birkenbihl/gui/styles/theme.py
- tests/gui/views/test_main_window.py
- tests/gui/models/test_ui_state.py
- tests/gui/models/test_translation_viewmodel.py
- tests/gui/commands/test_editor_commands.py
- tests/gui/commands/test_translation_commands.py
- tests/gui/widgets/test_progress_widget.py
- tests/gui/widgets/test_language_combo.py
- tests/gui/widgets/test_language_selector.py
- tests/gui/widgets/test_provider_selector.py
- tests/gui/utils/test_async_helper.py
- tests/gui/test_protocols.py

---

## Abschließende Gedanken

Das System hatte eine **gute Architektur** (Controller, Signals, MVVM) aber **schlechte Daten-Normalisierung**.

Die Hauptprobleme waren:
1. Inkonsistente Wort-Normalisierung (Punktuation)
2. Unnötige Sortierung die Probleme maskiert
3. Zwei Format-Systeme (Listen vs. Bindestriche) erhöhen Komplexität

**Für Neuentwicklung:** Fokus auf konsistente Daten-Normalisierung von Anfang an!
