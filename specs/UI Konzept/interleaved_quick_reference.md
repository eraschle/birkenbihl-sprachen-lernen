# Birkenbihl Interleaved UI - Quick Reference

## Grundprinzip in 3 Zeilen

```
Zeile 1:  Originalwörter (horizontal, fixed)
Zeile 2:  Verbindungslinien (optional)
Zeile 3+: Übersetzungswörter (vertikal stapelbar, per Drag & Drop)
```

---

## Basis-Beispiel

```
┌────────────────────────────────────┐
│  The   cat    sat                  │  ← Original (Englisch)
│   │     │     │                     │  ← Verbindungen
│  Die   Katze  saß                  │  ← Übersetzung (Deutsch)
└────────────────────────────────────┘
```

---

## Die 3 wichtigsten Regeln

### 1️⃣ Ein Originalwort = Eine Spalte
```
│  cat  │  ← Eine Spalte für "cat"
│   │   │
│ Katze │  ← Alle Übersetzungen von "cat" in dieser Spalte
```

### 2️⃣ Mehrere Übersetzungen = Vertikal stapeln
```
│   on   │  ← Eine Spalte
│   │    │
│  auf   │  ← Erste Übersetzung
│  der   │  ← Zweite Übersetzung
```

### 3️⃣ Leere Spalte = Fehler
```
│  the   │  ← Leere Spalte
│  (rot) │  ← Rot markiert
│   ∅    │  ← FEHLER! Muss gefüllt werden
```

---

## Drag & Drop: Die 4 Phasen

### Phase 1: Normal
```
│   on      the     mat   │
│   │       │       │     │
│  auf      der    Matte  │
```

### Phase 2: Grab (User greift "der")
```
│   on      the     mat       │
│  ░░░░    ░░░░    ░░░░      │  ← Alle Spalten = Drop-Zonen
│  auf      ∅      Matte  ╔═════╗
│                          ║ der ║
```

### Phase 3: Hover (über Spalte "on")
```
│   on      the     mat       │
│  ▓▓▓▓    ░░░░    ░░░░      │  ← "on" highlighted
│  auf      ∅      Matte  ╔═════╗
│                          ║ der ║
```

### Phase 4: Drop (in Spalte "on")
```
│   on      the     mat   │
│   │       │       │     │
│  auf      ∅      Matte  │  ✓ Erfolgreich!
│  der                    │
```

---

## Häufige Szenarien

### Szenario: Artikel-Verschmelzung
**Problem**: "auf dem" = "on the"

**Lösung A**: Beide zu "on"
```
│   on      the   │
│   │       │     │
│  auf      ∅     │
│  dem            │
```

**Lösung B**: Verteilen
```
│   on      the   │
│   │       │     │
│  auf      dem   │
```

### Szenario: Kein direktes Äquivalent
**Problem**: "It is raining" → "Es regnet"

**Lösung**:
```
│  It     is      raining  │
│  │      │       │        │
│  Es     ∅       regnet   │
```
oder mit Platzhalter für "is"

### Szenario: Trennbare Verben
**Problem**: "give up" → "gebe auf"

**Lösung**:
```
│  give    up    │
│   │      │     │
│  gebe    auf   │
```

---

## UI-Komponenten Cheatsheet

### Spalte (Column)
```python
class Column:
    - header: Originalwort (Text, fixed)
    - dropzone: Unsichtbar → Sichtbar beim Drag
    - tags: Liste von Übersetzungswörtern
    - is_empty: Bool für Validierung
    - on_drop(tag): Callback
```

### Tag (Draggable Word)
```python
class Tag:
    - text: Übersetzungswort
    - draggable: True
    - on_drag_start(): Alle Spalten zeigen Drop-Zones
    - on_drag_end(): Drop-Zones ausblenden
```

### Grid
```python
class InterlevedGrid:
    - columns: List[Column]
    - unassigned_pool: List[Tag]
    - validate(): Alle Spalten haben min. 1 Tag?
```

---

## CSS/Styling Hinweise

### Spalte
- Width: `auto` oder `minmax(60px, auto)`
- Border: `1px solid #ddd` (zwischen Spalten)
- Padding: `10px`

### Drop-Zone (aktiv)
- Background: `rgba(0, 150, 255, 0.1)`
- Border: `2px dashed #0096ff`

### Drop-Zone (hover)
- Background: `rgba(0, 150, 255, 0.2)`
- Border: `2px solid #0096ff`

### Tag
- Border-radius: `4px`
- Padding: `5px 10px`
- Background: `#f0f0f0`
- Box-shadow: `0 2px 4px rgba(0,0,0,0.1)`
- Cursor: `grab` → `grabbing`

### Leere Spalte (Fehler)
- Header-Color: `#ff0000`
- Background: `rgba(255, 0, 0, 0.05)`

---

## Layout-Optionen

### Option 1: CSS Grid
```css
.interleaved-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
    gap: 0;
}

.column {
    border-right: 1px solid #ddd;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
}
```

### Option 2: Flexbox
```css
.interleaved-grid {
    display: flex;
    flex-direction: row;
}

.column {
    flex: 1;
    min-width: 60px;
    display: flex;
    flex-direction: column;
}
```

### Option 3: Table (klassisch)
```html
<table class="interleaved-grid">
  <tr class="original-words">
    <td>The</td>
    <td>cat</td>
    <td>sat</td>
  </tr>
  <tr class="translations">
    <td>
      <div class="tag">Die</div>
    </td>
    <td>
      <div class="tag">Katze</div>
    </td>
    <td>
      <div class="tag">saß</div>
    </td>
  </tr>
</table>
```

---

## Validierungs-Checkliste

Vor dem Speichern prüfen:

- [ ] Alle Spalten haben min. 1 Tag
- [ ] "Nicht zugeordnet"-Pool ist leer
- [ ] Keine Tags sind außerhalb von Spalten
- [ ] Jedes Tag ist genau einer Spalte zugeordnet
- [ ] Spalten-Count = Anzahl Originalwörter

---

## Interaktions-Matrix

| Aktion | Spalte leer | Spalte gefüllt | Während Drag |
|--------|------------|---------------|--------------|
| Click auf Tag | - | Start Drag | - |
| Hover über Spalte | Highlight | Highlight | Highlight + Indicator |
| Drop in Spalte | Tag hinzufügen | Tag anhängen (stapeln) | Tag verschieben |
| Spalte leer lassen | ❌ Fehler | ✓ OK | - |

---

## Fehlermeldungen

```
┌──────────────────────────────────────────┐
│ ⚠️ 3 Wörter nicht zugeordnet             │  ← Warnung
│ 🔴 "the" und "on" haben keine Übersetzung│  ← Fehler
│ ℹ️ Ziehen Sie Wörter in die Spalten      │  ← Hinweis
└──────────────────────────────────────────┘
```

---

## Performance-Tipps

- **Virtualisierung**: Bei >50 Wörtern nur sichtbare Spalten rendern
- **Debouncing**: Drag-Events nicht bei jedem Pixel neu berechnen
- **Caching**: Grid-Layout cachen und nur bei Änderungen neu berechnen
- **Lazy Loading**: Übersetzungen on-demand laden

---

## Accessibility

```html
<!-- Spalte -->
<div role="region" aria-label="Übersetzung für: cat">
  <div class="header" aria-hidden="false">cat</div>
  <div role="list" class="tags">
    <div role="listitem" draggable="true" 
         aria-label="Übersetzung: Katze">
      Katze
    </div>
  </div>
</div>

<!-- Leere Spalte -->
<div role="alert" aria-live="polite">
  Spalte "the" hat keine Übersetzung
</div>
```

---

## Testing-Szenarien

1. **Basis-Drag**: Ein Tag von A nach B
2. **Mehrfach-Drop**: Mehrere Tags in eine Spalte
3. **Leere-Spalte**: Validierung bei leerer Spalte
4. **Lange-Wörter**: Spaltenbreite bei "Donaudampfschifffahrtsgesellschaft"
5. **Viele-Wörter**: Grid mit 50+ Spalten
6. **Edge-Case**: Alle Tags in einer Spalte
7. **Undo**: Drag rückgängig machen (ESC-Taste)
8. **Mobile**: Touch-Drag auf Tablet/Phone

---

## Keyboard-Shortcuts (optional)

- `Tab`: Nächste Spalte
- `Shift+Tab`: Vorherige Spalte
- `Space`: Tag aufheben (Drag-Modus)
- `Pfeiltasten`: Tag in Spalte bewegen
- `Enter`: Tag in Spalte ablegen
- `Esc`: Drag abbrechen
- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo

---

## Zusammenfassung

✅ **Tun:**
- Grid-Layout mit Spalten verwenden
- Tags vertikal in Spalten stapeln
- Drop-Zonen beim Drag anzeigen
- Leere Spalten rot markieren
- Pool für nicht zugeordnete Wörter

❌ **Nicht tun:**
- Tags horizontal innerhalb einer Spalte
- Mehrere Tags mit gleichem Text
- Spalten ohne Originalwort
- Drag & Drop ohne visuelles Feedback
- Speichern bei unvollständiger Zuordnung
