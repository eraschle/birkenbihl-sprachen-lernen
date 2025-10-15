# Alignment Editor Redesign - Design Dokument

## Motivation

**Aktuelles Problem:**
- AlignmentEditor erlaubt nur 1:1 Zuordnung (ein Quellwort → ein Zielwort)
- Zeigt alle Zielwörter, auch bereits verwendete
- Keine Möglichkeit, mehrere Zielwörter einem Quellwort zuzuordnen

**Neue Anforderungen:**
1. Mehrfachauswahl: Ein Quellwort kann mehreren Zielwörtern zugeordnet werden
2. Dynamische Filterung: Nur noch nicht verwendete Zielwörter anzeigen
3. Reihenfolge beibehalten: Liste folgt Reihenfolge der natürlichen Übersetzung
4. Post-Processing: Mehrere Wörter werden mit Bindestrich verbunden
5. Optional: Drag & Drop zum Neuanordnen

## Architektur-Entscheidungen

### 1. Internes Datenmodell

**UI-Datenmodell** (während der Bearbeitung):
```python
# Liste von Zuordnungen pro Quellwort
source_mappings: dict[str, list[str]] = {
    "Yo": ["Ich"],
    "te": ["dich"],
    "extrañaré": ["werde", "vermissen"]  # MEHRERE Wörter!
}
```

**Persistenz-Datenmodell** (nach Post-Processing):
```python
# WordAlignment mit verbundenen Wörtern
[
    WordAlignment(source_word="Yo", target_word="Ich", position=0),
    WordAlignment(source_word="te", target_word="dich", position=1),
    WordAlignment(source_word="extrañaré", target_word="werde-vermissen", position=2),  # Mit Bindestrich!
]
```

### 2. Post-Processing Hook-System

**Hook-Architektur:**
```python
class AlignmentHook(Protocol):
    """Protocol for alignment post-processing hooks."""
    def process(self,
                source_mappings: dict[str, list[str]],
                target_words: list[str]) -> list[WordAlignment]:
        """Process source mappings and return final WordAlignments."""
        pass

class HyphenateMultiWordsHook:
    """Verbindet mehrere Zielwörter mit Bindestrich."""
    def process(self, source_mappings, target_words):
        alignments = []
        for position, (source_word, target_word_list) in enumerate(source_mappings.items()):
            if len(target_word_list) == 0:
                continue  # Skip unmapped
            elif len(target_word_list) == 1:
                target_word = target_word_list[0]
            else:
                target_word = "-".join(target_word_list)  # Bindestrich!

            alignments.append(
                WordAlignment(source_word=source_word, target_word=target_word, position=position)
            )
        return alignments
```

**Hook-Manager:**
```python
class AlignmentHookManager:
    def __init__(self):
        self._hooks: list[AlignmentHook] = []
        self._register_default_hooks()

    def _register_default_hooks(self):
        self.register(HyphenateMultiWordsHook())

    def register(self, hook: AlignmentHook):
        self._hooks.append(hook)

    def process(self, source_mappings, target_words) -> list[WordAlignment]:
        # Apply all hooks in sequence
        # For now, we only have one hook that directly produces WordAlignments
        result = None
        for hook in self._hooks:
            result = hook.process(source_mappings, target_words)
        return result or []
```

### 3. UI-Design

**Neue Row-Struktur für jedes Quellwort:**

```
┌─────────────────────────────────────────────┐
│ Yo →                                        │
│   [Dropdown: verfügbare Wörter▼] [+ Hinzufügen] │
│   Ausgewählt:                               │
│   ┌──────────────────────────────────────┐ │
│   │ [1. Ich] [↑] [↓] [X]                 │ │
│   └──────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Komponenten:**
- `QLabel`: Quellwort mit Pfeil
- `QComboBox`: Dropdown mit noch verfügbaren Zielwörtern
- `QPushButton` (+): Fügt ausgewähltes Wort zur Liste hinzu
- `QListWidget` oder `QVBoxLayout`: Zeigt ausgewählte Wörter an
- Für jedes ausgewählte Wort:
  - `QLabel`: Ordnungszahl und Wort
  - `QPushButton` (↑): Nach oben verschieben
  - `QPushButton` (↓): Nach unten verschieben
  - `QPushButton` (X): Entfernen

### 4. Dynamische Filterung

**Algorithmus:**
1. Sammle alle bereits zugeordneten Zielwörter aus `source_mappings`
2. Filtere `target_words` Liste: Zeige nur noch nicht zugeordnete
3. Sortiere nach Reihenfolge in `target_words` (natürliche Übersetzung)

```python
def get_available_target_words(self, for_source_word: str | None = None) -> list[str]:
    """Get list of available (not yet mapped) target words.

    Args:
        for_source_word: If provided, includes words already mapped to this source word

    Returns:
        List of available target words in natural translation order
    """
    # Collect all mapped words (except for current source word)
    mapped = set()
    for source, targets in self._source_mappings.items():
        if source != for_source_word:
            mapped.update(targets)

    # Return words not yet mapped
    return [word for word in self._target_words if word not in mapped]
```

### 5. Drag & Drop (Optional)

**Implementierung mit Qt Drag & Drop:**
- `QListWidget` mit `setDragDropMode(QAbstractItemView.InternalMove)`
- Oder manuelle Implementierung mit ↑/↓ Buttons

Für MVP: **Nur ↑/↓ Buttons** (einfacher zu implementieren)

## Implementierungsplan

### Phase 1: Post-Processing Hook-System (Agent 1)
**Dateien:**
- `src/birkenbihl/gui/hooks/__init__.py` (neu)
- `src/birkenbihl/gui/hooks/alignment_hooks.py` (neu)
- `tests/gui/hooks/test_alignment_hooks.py` (neu)

**Deliverables:**
- `AlignmentHook` Protocol
- `HyphenateMultiWordsHook` Implementierung
- `AlignmentHookManager` mit Registration
- Unit-Tests für Hook-System

### Phase 2: AlignmentEditor UI Redesign (Agent 2)
**Dateien:**
- `src/birkenbihl/gui/widgets/alignment_editor.py` (umfangreiche Änderungen)

**Deliverables:**
- Neues internes Datenmodell: `_source_mappings: dict[str, list[str]]`
- UI mit Mehrfachauswahl (Dropdown + Liste)
- Dynamische Filterung (nur verfügbare Wörter)
- ↑/↓ Buttons für Reihenfolge
- Integration von Hook-Manager im `_on_apply()`

### Phase 3: Integration & Tests (Agent 3)
**Dateien:**
- `tests/gui/widgets/test_alignment_editor.py`
- Integration mit `editor_view.py` (sollte nahtlos funktionieren, da Signal gleich bleibt)

**Deliverables:**
- Unit-Tests für AlignmentEditor
- Integration-Tests für gesamten Workflow
- Manuelle UI-Tests

### Phase 4: Optional - Drag & Drop
- Falls Zeit und Bedarf: Ersetze ↑/↓ Buttons durch Drag & Drop

## Erfolgs-Kriterien

1. ✅ Benutzer kann mehrere Zielwörter einem Quellwort zuordnen
2. ✅ Dropdown zeigt nur noch nicht verwendete Wörter
3. ✅ Reihenfolge der Wörter kann mit ↑/↓ angepasst werden
4. ✅ Beim Speichern werden mehrere Wörter mit Bindestrich verbunden
5. ✅ Alle Tests bestehen
6. ✅ Keine Breaking Changes (Signal `alignment_changed` bleibt gleich)

## Beispiel-Workflow

**Vorher (aktuell):**
```
Yo → [Dropdown: Ich/werde/dich/vermissen] → wählt "Ich"
te → [Dropdown: Ich/werde/dich/vermissen] → wählt "dich"
extrañaré → [Dropdown: Ich/werde/dich/vermissen] → kann nur 1 Wort wählen ❌
```

**Nachher (neu):**
```
Yo → [Dropdown: Ich/werde/dich/vermissen] [+]
     Ausgewählt: [1. Ich] [↑][↓][X]

te → [Dropdown: werde/dich/vermissen] [+]  # "Ich" nicht mehr verfügbar
     Ausgewählt: [1. dich] [↑][↓][X]

extrañaré → [Dropdown: werde/vermissen] [+]
            Ausgewählt: [1. werde] [↑][↓][X]
                        [2. vermissen] [↑][↓][X]  # Mehrere Wörter! ✅

Speichern → Post-Processing → Ergebnis:
[
  WordAlignment("Yo", "Ich", 0),
  WordAlignment("te", "dich", 1),
  WordAlignment("extrañaré", "werde-vermissen", 2)  # Mit Bindestrich! ✅
]
```

## Technische Notizen

- **Keine Breaking Changes:** Signal `alignment_changed` behält Signatur `list[WordAlignment]`
- **Hook-System extensible:** Weitere Hooks können später hinzugefügt werden (z.B. Validierung, Normalisierung)
- **Clean Architecture:** UI-Logik getrennt von Business-Logik (Hooks)
- **Testbar:** Jede Komponente einzeln testbar
