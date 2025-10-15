# UI-Spezifikation: Birkenbihl-Übersetzungs-App

## Übersicht

Die App verwaltet Übersetzungen nach der Birkenbihl-Methode mit drei Modi:
- **VIEW** (Standardmodus): Anzeige bestehender Übersetzungen
- **CREATE**: Erstellen einer neuen Übersetzung
- **EDIT**: Bearbeiten einer bestehenden Übersetzung

---

## Hauptbildschirm Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Bestehende Übersetzungen                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Combobox: Titel auswählen]        [Edit] [New]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─ Übersetzungsbereich ────────────────────────────────────┐ │
│ │                                                           │ │
│ │   [Inhalt abhängig vom Modus: VIEW/CREATE/EDIT]          │ │
│ │                                                           │ │
│ └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Komponenten: Kopfzeile

### Label
- **Text**: "Bestehende Übersetzungen"
- **Position**: Links oben

### Combobox: Titel auswählen
- **Breite**: Wide (füllt verfügbaren Platz)
- **Inhalt**: Liste aller gespeicherten Übersetzungstitel
- **Enabled**: `mode != EDIT AND mode != CREATE`
- **Event**: `on_selection_changed` → Lädt gewählte Übersetzung in VIEW-Modus

### Button: Edit
- **Label**: "Edit"
- **Enabled**: `mode == VIEW AND selected_translation != None`
- **Command**: `switch_to_edit_mode()`
- **Tooltip**: "Übersetzung bearbeiten"

### Button: New
- **Label**: "New"
- **Enabled**: Immer aktiv
- **Command**: `create_new()`
- **Tooltip**: "Neue Übersetzung erstellen"

---

## Modus: CREATE

```
┌─ Neue Übersetzung erstellen ────────────────────────────────┐
│                                                               │
│  Titel                                                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ [Entry: Titel eingeben]                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Originaltext                                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ [Text Widget: Mehrzeiliger Text]                        │ │
│  │                                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐ │
│  │[CB: Source Lang] │ │[CB: Target Lang] │ │[CB: Translator]│ │
│  └──────────────────┘ └──────────────────┘ └──────────────┘ │
│                                                               │
│                              [Abbrechen]  [Erstellen]         │
└───────────────────────────────────────────────────────────────┘
```

### Komponenten

**Entry: Titel**
- Einzeilige Texteingabe
- Required field

**Text Widget: Originaltext**
- Mehrzeilige Texteingabe
- Automatisches Zeilenumbruch
- Scrollbar bei Bedarf
- Required field

**Combobox: Source Language**
- Dropdown mit verfügbaren Sprachen
- Default: Letzte verwendete oder "Englisch"

**Combobox: Target Language**
- Dropdown mit verfügbaren Sprachen
- Default: Letzte verwendete oder "Deutsch"

**Combobox: Translator**
- Optionen: "Manual", "AI-Provider1", "AI-Provider2", etc.
- Default: "Manual"

**Button: Abbrechen**
- Command: `cancel_create()` → Zurück zu VIEW

**Button: Erstellen**
- Enabled: `title.is_valid AND original_text.is_valid`
- Command: `save_new_translation()` → Wechselt zu EDIT-Modus

---

## Modus: VIEW

```
┌─ Übersetzung anzeigen ───────────────────────────────────────┐
│                                                               │
│  ┌─ Originalsätze ──────────┐  ┌─ Übersetzungen ───────────┐ │
│  │ 1. The cat sat on...     │  │ ┌─ Natürlich ────────────┐ │ │
│  │ 2. It was a warm day.    │  │ │ Die Katze saß auf der  │ │ │
│  │ 3. Birds were singing.   │  │ │ Matte.                 │ │ │
│  │                          │  │ └────────────────────────┘ │ │
│  │                          │  │                            │ │
│  │                          │  │ ┌─ Wort-für-Wort ────────┐ │ │
│  │                          │  │ │ The  cat  sat  on  mat │ │ │
│  │                          │  │ │  │    │    │    │   │   │ │ │
│  │                          │  │ │ Die Katze saß auf  Matte│ │ │
│  │                          │  │ │           der           │ │ │
│  │                          │  │ └────────────────────────┘ │ │
│  └──────────────────────────┘  └────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### Komponenten

**Listbox: Originalsätze (Links)**
- Zeigt alle Sätze der Quellsprache
- Single Selection
- Event: `on_sentence_selected` → Zeigt entsprechende Übersetzung rechts
- Nummerierung vor jedem Satz

**Panel: Übersetzungsanzeige (Rechts)**
- Zeigt Übersetzung des ausgewählten Satzes

**Text Display: Natürliche Übersetzung**
- Read-only Text
- Zeigt fließende Übersetzung

**Panel: Wort-für-Wort Übersetzung**
- Interleaved (verschachtelte) Darstellung
- Obere Zeile: Originalwörter horizontal angeordnet
- Mittlere Zeile: Vertikale Verbindungslinien (│)
- Untere Zeile(n): Zugeordnete Übersetzungswörter direkt unter dem Originalwort
- Mehrere Übersetzungswörter pro Originalwort werden untereinander angezeigt
- Layout: Grid mit fester Spaltenbreite pro Originalwort
- Read-only Darstellung

---

## Modus: EDIT

```
┌─ Übersetzung bearbeiten ─────────────────────────────────────┐
│                                                               │
│  ┌─ Originalsätze ──────────┐  ┌─ Übersetzungen ───────────┐ │
│  │ 1. The cat sat on...     │  │ ┌─ Natürlich ────────────┐ │ │
│  │ 2. It was a warm day.    │  │ │ [Text Area]            │ │ │
│  │ 3. Birds were singing.   │  │ │ Die Katze saß auf...   │ │ │
│  │                          │  │ └────────────────────────┘ │ │
│  │                          │  │   [Edit] [Generate (AI)]   │ │
│  │                          │  │                            │ │
│  │                          │  │ ┌─ Wort-für-Wort ────────┐ │ │
│  │                          │  │ │ The  cat  sat  on  mat │ │ │
│  │                          │  │ │ ░░░  ░░░  ░░░  ░░░ ░░░ │ │ │
│  │                          │  │ │ [Die][Katze][saß][auf][Matte]│ │
│  │                          │  │ │              [der]     │ │ │
│  │                          │  │ │ (Drag & Drop aktiv)    │ │ │
│  │                          │  │ └────────────────────────┘ │ │
│  └──────────────────────────┘  └────────────────────────────┘ │
│                                               [Speichern]      │
└───────────────────────────────────────────────────────────────┘
```

### Komponenten

**Listbox: Originalsätze** (wie VIEW)
- Identisch zum VIEW-Modus

**Text Area: Natürliche Übersetzung**
- Editierbar
- Mehrere Zeilen möglich
- Auto-save bei Fokusverlust oder nach Timeout

**Button: Edit (Manuell)**
- Enabled: Immer
- Command: `edit_natural_translation()` 
- Fokussiert das Text Area

**Button: Generate (AI)**
- Enabled: `translator_service.is_available`
- Command: `generate_translation_ai()`
- Ersetzt Text Area Inhalt mit AI-Übersetzung
- Zeigt Loading-Indikator während Generation

**Panel: Wort-für-Wort Übersetzung (Editierbar)**
- Interleaved (verschachtelte) Grid-Darstellung
- **Zeile 1**: Originalwörter (fixed, nicht verschiebbar)
- **Zeile 2**: Drop-Zonen (visueller Indikator)
- **Zeile 3+**: Übersetzungs-Tags (verschiebbar)
- Layout: Grid mit Spalten, eine Spalte pro Originalwort
- Spaltenbreite passt sich längstem Wort an

**Drag & Drop Verhalten:**
- Tags können horizontal zwischen Spalten verschoben werden
- Jede Spalte = Drop-Zone für ein Originalwort
- Mehrere Tags können in einer Spalte übereinander gestapelt werden
- Visual Feedback:
  - Drop-Zonen werden beim Drag sichtbar (░░░)
  - Aktive Drop-Zone beim Hover hervorgehoben (▓▓▓)
  - Tag während Drag hat Schatten/Transparenz

**Validierung:**
- Leere Spalten (kein Tag unter Originalwort) werden rot markiert
- Spaltenüberschrift wechselt Farbe: Grau (leer) → Grün (zugeordnet)

**Pool nicht zugeordneter Wörter:**
- Unterhalb des Grids
- Zeile: `[Nicht zugeordnet] → [Tag1] [Tag2] ...`
- Wenn natürliche Übersetzung geändert wird, neue Wörter hier

**Wort-Tag Struktur:**
```
┌──────────┐
│ Katze    │  
└──────────┘
```
- Gerundete Ecken, Padding
- Schatten beim Hover
- Cursor: grab (✋) / grabbing (✊)

**Button: Speichern**
- Position: Unten rechts
- Enabled: `has_unsaved_changes`
- Command: `save_translation()` → Zurück zu VIEW

---

## State Management

### Global State
```python
app_state = {
    'mode': 'VIEW',  # VIEW, CREATE, EDIT
    'translations': [],  # Liste aller Übersetzungen
    'selected_translation': None,  # Aktuell gewählte Übersetzung
    'selected_sentence_index': 0,  # Index des gewählten Satzes
    'has_unsaved_changes': False
}
```

### Transitions

```
VIEW → CREATE: Button "New" geklickt
VIEW → EDIT:   Button "Edit" geklickt (nur wenn Übersetzung ausgewählt)
CREATE → VIEW: "Abbrechen" oder "Erstellen" geklickt
EDIT → VIEW:   "Speichern" geklickt oder Übersetzung in Combobox gewechselt
```

---

## Datenmodell

### Translation
```python
{
    'id': str,
    'title': str,
    'source_language': str,
    'target_language': str,
    'translator': str,
    'sentences': [Sentence],
    'created_at': datetime,
    'updated_at': datetime
}
```

### Sentence
```python
{
    'id': str,
    'original_text': str,
    'original_words': [str],  # Tokenisierte Originalwörter
    'natural_translation': str,
    'translation_words': [str],  # Tokenisierte Übersetzungswörter
    'word_mappings': [WordMapping]  # Zuordnung Original → Übersetzung
}
```

### WordMapping
```python
{
    'original_word_index': int,  # Index im original_words Array
    'translation_word_indices': [int]  # Indices im translation_words Array
}

# Beispiel:
# original_words = ["The", "cat", "sat", "on", "the", "mat"]
# translation_words = ["Die", "Katze", "saß", "auf", "der", "Matte"]
# word_mappings = [
#     {'original_word_index': 0, 'translation_word_indices': [0]},      # The → Die
#     {'original_word_index': 1, 'translation_word_indices': [1]},      # cat → Katze
#     {'original_word_index': 2, 'translation_word_indices': [2]},      # sat → saß
#     {'original_word_index': 3, 'translation_word_indices': [3, 4]},   # on → auf der
#     {'original_word_index': 4, 'translation_word_indices': []},       # the → (bereits bei "on" zugeordnet)
#     {'original_word_index': 5, 'translation_word_indices': [5]}       # mat → Matte
# ]
```

---

## Interaktionslogik

### Satz auswählen (VIEW/EDIT)
1. User klickt auf Satz in Listbox
2. `selected_sentence_index` wird aktualisiert
3. Rechte Seite zeigt Übersetzung des gewählten Satzes

### Wort-für-Wort bearbeiten (EDIT)
1. **Initialisierung**: Wenn natürliche Übersetzung geändert wird:
   - Text wird tokenisiert (in Wörter aufgeteilt)
   - Neue Wörter werden zum "Nicht zugeordnet"-Pool hinzugefügt
   - Bestehende Zuordnungen bleiben erhalten

2. **Drag & Drop Ablauf (Interleaved)**:
   - User startet Drag auf einem Übersetzungs-Tag
   - Alle Spalten (Drop-Zonen unter jedem Originalwort) werden sichtbar gemacht (░░░)
   - User bewegt Tag horizontal über Spalten
   - Spalte unter Mauszeiger zeigt Hover-Effekt (▓▓▓)
   - User lässt Tag in einer Spalte los:
     - Tag wird aus alter Spalte entfernt
     - Tag wird in neue Spalte eingefügt (unterhalb vorhandener Tags)
     - `word_mappings` wird aktualisiert
     - Grid rendert neu
     - `has_unsaved_changes = True`

3. **Vertikale Anordnung innerhalb Spalte**:
   - Wenn mehrere Tags in einer Spalte: untereinander stapeln
   - Beispiel: "on" kann "auf" und "der" haben
   ```
   on
   │
   auf
   der
   ```

4. **Validierung**:
   - Spalten ohne Tags werden rot markiert (Originalwort in roter Farbe)
   - "Speichern"-Button deaktiviert wenn Validierung fehlschlägt
   - Fehlermeldung: "Alle Originalwörter müssen eine Übersetzung haben"
   - Tooltip bei leerer Spalte: "Ziehen Sie ein Wort hierher"

5. **Auto-Zuordnung (Optional)**:
   - Button "Auto-Zuordnen" führt intelligentes Mapping durch
   - Nutzt Wort-Reihenfolge oder AI für Vorschlag
   - Füllt Tags automatisch in Spalten
   - User kann Zuordnung manuell korrigieren

### AI-Übersetzung generieren (EDIT)
1. User klickt "Generate (AI)"
2. Loading-Spinner erscheint
3. API-Call an AI-Service mit:
   - Originaltext
   - Source/Target Language
   - Anforderung: Natürliche Übersetzung + Wort-Zuordnungen
4. Bei Erfolg: 
   - Text Area wird mit natürlicher Übersetzung befüllt
   - `translation_words` wird tokenisiert
   - `word_mappings` wird mit AI-Vorschlag gefüllt
   - UI rendert Wort-für-Wort Zuordnung
5. Bei Fehler: Error-Message anzeigen
6. User kann AI-Zuordnung manuell korrigieren
7. `has_unsaved_changes = True`

---

## Wort-Zuordnungs-Logik im Detail

### Konzept
Die Birkenbihl-Methode basiert darauf, jedes Wort der Originalsprache mit seiner Übersetzung zu verknüpfen. Dies erfolgt durch:
1. **Natürliche Übersetzung**: Fließender, grammatikalisch korrekter Zieltext
2. **Wort-für-Wort Zuordnung**: Mapping von Originalwörtern zu Übersetzungswörtern

### Regeln
1. Jedes **Originalwort** MUSS mindestens einem Übersetzungswort zugeordnet sein
2. Jedes **Übersetzungswort** MUSS genau einem Originalwort zugeordnet sein
3. Ein Originalwort KANN mehreren Übersetzungswörtern zugeordnet sein
4. Ein Übersetzungswort KANN NICHT mehreren Originalwörtern zugeordnet sein

### Beispiel-Szenarien

**Szenario 1: Einfache 1:1 Zuordnung**
```
Original:     "The cat sleeps"
Übersetzung:  "Die Katze schläft"

Interleaved-Ansicht:
The   cat     sleeps
│     │       │
Die   Katze   schläft
```

**Szenario 2: Artikel-Verschmelzung (1:n)**
```
Original:     "on the table"
Übersetzung:  "auf dem Tisch"

Interleaved-Ansicht (Option A):
on    the   table
│     │     │
auf   dem   Tisch

Interleaved-Ansicht (Option B):
on    the   table
│           │
auf         Tisch
dem

(Beide Optionen sind valide, Option B zeigt dass "dem" zu "on" gehört)
```

**Szenario 3: Zusammengesetzte Verben**
```
Original:     "I give up"
Übersetzung:  "Ich gebe auf"

Interleaved-Ansicht:
I     give  up
│     │     │
Ich   gebe  auf
      auf
```

**Szenario 4: Fehlende direkte Übersetzung**
```
Original:     "It is raining"
Übersetzung:  "Es regnet"

Interleaved-Ansicht:
It    is    raining
│     │     │
Es    ∅     regnet

(oder "is" kann mit "regnet" kombiniert werden)
```

### UI-Verhalten bei Zuordnung

**Visualisierung der Zuordnung (Interleaved):**
```
┌─────────────────────────────────────────────┐
│    on      the     table                    │  ← Originalwörter
│    │       │       │                         │  ← Verbindungslinien
│   auf      ∅      Tisch                     │  ← Übersetzungen
│   dem                                        │
└─────────────────────────────────────────────┘
     ↑       ↑ (rot)  ↑
   1:2 OK   Fehler!  1:1 OK

[Nicht zugeordnet] →  [der] [und]              ← Übrige Wörter
```

**Drag & Drop Interaktion (Interleaved):**
1. User greift Tag "dem" und zieht es
2. Alle Spalten zeigen Drop-Zone Indicator
3. User lässt "dem" in Spalte "the" los
4. "dem" erscheint jetzt unter "the"
5. Validation prüft ob alle Spalten mindestens ein Tag haben

### Visuelles Drag & Drop Interface

**Normal State (Interleaved):**
```
┌─────────────────────────────────────────────┐
│   on      the     table                     │
│   │       │       │                          │
│  [auf]   [der]  [Tisch]                     │
└─────────────────────────────────────────────┘
```

**Während Drag (Tag "der" wird bewegt):**
```
┌─────────────────────────────────────────────┐
│   on      the     table                     │
│  ░░░░    ░░░░    ░░░░                       │  ← Drop-Zonen sichtbar
│  [auf]    ∅      [Tisch]      ╔═════╗       │
│                                ║ der ║       │  ← Tag schwebt
└────────────────────────────────╚═════╝───────┘
                                   └─ Mauszeiger
```

**Hover über Spalte "on":**
```
┌─────────────────────────────────────────────┐
│   on      the     table                     │
│  ▓▓▓▓    ░░░░    ░░░░                       │  ← "on" hervorgehoben
│  [auf]    ∅      [Tisch]      ╔═════╗       │
│                                ║ der ║       │
└────────────────────────────────╚═════╝───────┘
```

**Nach Drop bei "on":**
```
┌─────────────────────────────────────────────┐
│   on      the     table                     │
│   │       │       │                          │
│  [auf]    ∅      [Tisch]                    │  ← "der" neu zugeordnet
│  [der]                                       │
└─────────────────────────────────────────────┘
```

**Mit Validierungs-Fehler:**
```
┌─────────────────────────────────────────────┐
│   on      the     table                     │  
│   │      (rot)     │                         │
│  [auf]    ∅      [Tisch]                    │
│  [der]                                       │
├─────────────────────────────────────────────┤
│ ⚠️ Fehler: "the" hat keine Übersetzung      │
└─────────────────────────────────────────────┘

[Nicht zugeordnet] →  [auf] [dem]  ← Noch verfügbar
```

### Tokenisierung

**Wichtig**: Text muss in Wörter aufgeteilt werden
- Einfache Methode: Split bei Leerzeichen und Satzzeichen
- Erweiterte Methode: Nutzung von NLP-Bibliotheken (z.B. spaCy, NLTK)
- Satzzeichen: Können ignoriert oder als separate Tokens behandelt werden

**Beispiel:**
```python
text = "The cat's name is Fluffy."
# Einfach:
words = text.split()  # ["The", "cat's", "name", "is", "Fluffy."]

# Besser:
import re
words = re.findall(r'\b\w+\b', text)  # ["The", "cat", "s", "name", "is", "Fluffy"]
```

---

## UI-Framework Hinweise

### Empfohlene Widgets (Python/Tkinter)
- **Combobox**: `ttk.Combobox`
- **Listbox**: `tk.Listbox` mit Scrollbar
- **Text Area**: `tk.Text` (mehrzeilig) oder `ttk.Entry` (einzeilig)
- **Buttons**: `ttk.Button`
- **Labels**: `ttk.Label`
- **LabelFrame**: `ttk.LabelFrame` für gruppierte Bereiche
- **Drag & Drop**: Eigene Implementierung mit `bind('<Button-1>')`, `bind('<B1-Motion>')`, `bind('<ButtonRelease-1>')`

### Alternative (Python/PyQt)
- **Combobox**: `QComboBox`
- **Listbox**: `QListWidget`
- **Text Area**: `QTextEdit` (mehrzeilig) oder `QLineEdit` (einzeilig)
- **Buttons**: `QPushButton`
- **Drag & Drop**: Qt's eingebautes Drag & Drop System

---

## Styling-Richtlinien

### Farben
- **Wort-Tags**: Leicht gerundete Ecken, Schatten beim Hover
- **Drop-Zonen**: Gestrichelte Linie oder farbige Markierung
- **Aktiver Satz**: Highlight-Farbe in Listbox

### Abstände
- **Padding**: 10px zwischen Hauptelementen
- **Margin**: 5px zwischen Wort-Tags
- **Gap**: 15px zwischen Listbox und Übersetzungspanel

### Responsive
- Mindestbreite: 800px
- Mindesthöhe: 600px
- Linke Listbox: 40% Breite
- Rechtes Panel: 60% Breite
