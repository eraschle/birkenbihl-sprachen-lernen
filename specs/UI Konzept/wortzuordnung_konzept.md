# Birkenbihl Wort-Zuordnung: Visuelles Konzept

## Das Grundprinzip

Die Birkenbihl-Methode verbindet jedes Wort der Originalsprache mit seiner Übersetzung in einer **Interleaved (verschachtelten) Darstellung**.

```
 Originaltext (Englisch)          Übersetzung (Deutsch)
┌──────────────────────┐         ┌──────────────────────┐
│ The cat sat on the   │   →→→   │ Die Katze saß auf    │
│ mat.                 │   →→→   │ der Matte.           │
└──────────────────────┘         └──────────────────────┘

         ↓ Tokenisierung                ↓ Tokenisierung

  ┌───┬───┬───┬──┬───┬───┐      ┌───┬─────┬───┬───┬──┬──────┐
  │The│cat│sat│on│the│mat│      │Die│Katze│saß│auf│der│Matte│
  └───┴───┴───┴──┴───┴───┘      └───┴─────┴───┴───┴──┴──────┘

         ↓ Wort-für-Wort Zuordnung (Interleaved) ↓

  ┌────────────────────────────────────────────────────┐
  │  The   cat    sat    on     the   mat              │
  │   │     │     │      │      │     │                │
  │  Die   Katze  saß   auf     ∅    Matte             │
  │                     der                             │
  └────────────────────────────────────────────────────┘
```

---

## Die Darstellungsformen

### 1. Natürliche Übersetzung
```
┌─────────────────────────────────────┐
│ Die Katze saß auf der Matte.        │
└─────────────────────────────────────┘
```
**Zweck**: Zeigt wie der Satz korrekt auf Deutsch klingt.

### 2. Wort-für-Wort Zuordnung (Interleaved) ⭐ HAUPTDARSTELLUNG
```
┌─────────────────────────────────────┐
│  The   cat    sat    on     mat     │  ← Originalwörter
│   │     │     │      │      │       │  ← Verbindungen
│  Die   Katze  saß   auf    Matte    │  ← Übersetzungen
│                     der              │
└─────────────────────────────────────┘
```
**Zweck**: Direkter visueller Vergleich Wort für Wort. Die Übersetzungswörter stehen direkt unter dem zugehörigen Originalwort.

**Vorteile:**
- Intuitiv: Räumliche Nähe zeigt Zuordnung
- Kompakt: Gesamter Satz auf einen Blick
- Lernfreundlich: Gehirn kann Muster leichter erkennen

---

## Zuordnungs-Regeln (visuell)

### ✅ Erlaubt: 1:1 Zuordnung
```
Original:     cat
              │
Übersetzung:  Katze
```

### ✅ Erlaubt: 1:n Zuordnung (Ein Original → Mehrere Übersetzungen)
```
Original:     on
              │
Übersetzung:  auf
              der
```
**Mehrere Übersetzungswörter stapeln sich vertikal unter dem Originalwort.**

### ❌ Nicht erlaubt: n:1 Zuordnung (Mehrere Originale → Eine Übersetzung)
```
Original:     on    the
              │      │
Übersetzung:  auf ← FEHLER! Beide zeigen auf dasselbe Wort
```
**Lösung**: Entscheide zu welchem Wort "auf" gehört, oder dupliziere es.

### ❌ Nicht erlaubt: Keine Zuordnung
```
Original:     the
              
Übersetzung:  ∅         ← FEHLER! Leere Spalte
```
**Lösung**: Ordne mindestens ein Wort zu oder füge Platzhalter hinzu.

---

## Drag & Drop Workflow (Schritt für Schritt)

### Schritt 1: Ausgangssituation
```
┌──────────────────────────────────────────┐
│   on      the     mat                    │
│   │       │       │                       │
│  auf      der    Matte                   │
└──────────────────────────────────────────┘
```
User erkennt: "auf der" gehört zusammen zu "on"

### Schritt 2: User greift "der"
```
┌──────────────────────────────────────────┐
│   on      the     mat                    │
│  ░░░░    ░░░░    ░░░░                    │  ← Drop-Zonen werden sichtbar
│  auf      ∅      Matte      ╔═════╗      │
│                              ║ der ║      │  ← Drag in Progress
└────────────────────────────────╚═════╝────┘
```

### Schritt 3: User zieht "der" zu "on"
```
┌──────────────────────────────────────────┐
│   on      the     mat                    │
│  ▓▓▓▓    ░░░░    ░░░░                    │  ← Hover über Spalte "on"
│  auf      ∅      Matte      ╔═════╗      │
│                              ║ der ║      │  
└────────────────────────────────╚═════╝────┘
```

### Schritt 4: User lässt "der" los
```
┌──────────────────────────────────────────┐
│   on      the     mat                    │
│   │      (rot)     │                      │
│  auf      ∅       Matte     ✓            │  ← Erfolgreich bei "on"
│  der                                      │
├──────────────────────────────────────────┤
│ Status: ⚠️ Nicht speicherbar             │
│ "the" hat keine Zuordnung                │
└──────────────────────────────────────────┘
```

### Schritt 5: User ordnet verbleibendes Wort zu
```
┌──────────────────────────────────────────┐
│   on      the     mat                    │
│   │       │       │                       │
│  auf     die*    Matte                   │  
│  der                                      │
├──────────────────────────────────────────┤
│ Status: ✅ Alle Wörter zugeordnet        │
│ Speichern möglich                        │
└──────────────────────────────────────────┘

* aus "Nicht zugeordnet"-Pool gezogen
```

---

## Edge Cases und Lösungen

### Problem 1: Artikel-Verschmelzung im Deutschen
```
Englisch:  "in the house"
Deutsch:   "im Haus"

Lösung A (Empfohlen):
in     the    house
│      │      │
im     ∅      Haus

Lösung B (Alternative):
in     the    house
│             │
i             Haus
m
```

### Problem 2: Unterschiedliche Wortanzahl
```
Englisch:  "I am going to eat"    (5 Wörter)
Deutsch:   "Ich werde essen"      (3 Wörter)

Zuordnung (Interleaved):
I      am      going   to     eat
│      │                      │
Ich    werde                  essen
       (umfasst "am going to")
```

### Problem 3: Zusätzliche Wörter im Deutschen
```
Englisch:  "I enjoy"      (2 Wörter)
Deutsch:   "Ich freue mich" (3 Wörter)

Zuordnung (Interleaved):
I       enjoy
│       │
Ich     freue
        mich
```

### Problem 4: Trennbare Verben
```
Englisch:  "I give up"
Deutsch:   "Ich gebe auf"

Zuordnung (Interleaved):
I      give    up
│      │       │
Ich    gebe    auf
```

---

## UI States Übersicht

```
┌─ LEGENDE ─────────────────────────────────┐
│ Wort       = Normaler Text                │
│ [Wort]     = Tag/Chip (verschiebbar)      │
│ ░░░░       = Drop-Zone (inaktiv)          │
│ ▓▓▓▓       = Drop-Zone (hover)            │
│ ╔═══╗      = Tag während Drag             │
│ │          = Verbindungslinie              │
│ ✓          = Validierung OK               │
│ ⚠️         = Warnung                      │
│ 🔴         = Fehler                       │
│ ∅          = Leer                         │
│ (rot)      = Rot eingefärbter Text        │
└───────────────────────────────────────────┘
```

### State 1: Vollständig und korrekt
```
┌──────────────────────────────────────────┐
│  The   cat    sat                        │
│   │     │     │                           │
│  Die   Katze  saß                        │
├──────────────────────────────────────────┤
│ Status: ✅ Vollständig                   │
└──────────────────────────────────────────┘
[Speichern] ← Aktiv
```

### State 2: Unvollständig
```
┌──────────────────────────────────────────┐
│  The   cat    sat                        │
│   │   (rot)    │                          │
│  Die    ∅     saß                        │
├──────────────────────────────────────────┤
│ ⚠️ "cat" hat keine Übersetzung           │
└──────────────────────────────────────────┘
[Nicht zugeordnet] → [Katze]

[Speichern] ← Deaktiviert
```

### State 3: Während Bearbeitung
```
┌──────────────────────────────────────────┐
│  The   cat    sat                        │
│  ░░░░  ▓▓▓▓  ░░░░                        │  ← Drop-Zonen
│  Die    ∅     saß         ╔═════╗       │
│                            ║Katze║       │  ← Drag
└──────────────────────────────╚═════╝─────┘
```

### State 4: Mehrere Wörter pro Spalte
```
┌──────────────────────────────────────────┐
│   on     the    mat                      │
│   │      │      │                         │
│  auf     der   Matte                     │
│  dem                                      │  ← Mehrfachzuordnung
└──────────────────────────────────────────┘
```

---

## Interleaved-Layout: Implementierungsdetails

### Grid-Struktur

Das Interleaved-Layout basiert auf einem **Grid (Tabellen-Layout)** mit dynamischen Spalten:

```
┌─────────────────────────────────────────────────┐
│  Spalte 1  │  Spalte 2  │  Spalte 3  │ ...     │
├────────────┼────────────┼────────────┼─────────┤
│ Zeile 1: Originalwörter                         │
│   The      │   cat      │   sat      │         │
├────────────┼────────────┼────────────┼─────────┤
│ Zeile 2: Verbindungslinien (optional)           │
│    │       │    │       │    │       │         │
├────────────┼────────────┼────────────┼─────────┤
│ Zeile 3+: Übersetzungswörter (dynamisch)       │
│   Die      │  Katze     │   saß      │         │
│            │            │            │         │
└────────────┴────────────┴────────────┴─────────┘
```

### Spaltenbreite
- **Dynamisch**: Jede Spalte passt sich dem breitesten Element an
- Mindestbreite: 60px
- Padding: 10px horizontal, 5px vertikal

### Drag & Drop Zonen
Jede Spalte ist eine Drop-Zone:
```python
# Pseudocode
for column in grid.columns:
    column.set_droppable(True)
    column.on_drop(lambda word, col: assign_word_to_column(word, col))
    column.on_drag_over(lambda col: highlight_column(col))
```

### Vertikales Stapeln
Wenn mehrere Wörter einer Spalte zugeordnet sind:
```
│  on   │
│   │   │
│  auf  │  ← Erstes Wort
│  der  │  ← Zweites Wort (darunter)
│  dem  │  ← Drittes Wort (darunter)
```

**Implementierung:**
- Spalte = Container mit vertikalem Layout
- Tags werden einfach hinzugefügt: `column.add_child(tag)`
- Automatisches Stapeln durch Layout-Engine

---

## Implementierungs-Checkliste

- [ ] Tokenisierung für beide Sprachen
- [ ] Grid-Layout mit dynamischen Spalten implementieren
- [ ] Drag & Drop Logik für horizontale Bewegung
- [ ] Drop-Zone Visualisierung (░░░ und ▓▓▓)
- [ ] Vertikales Stapeln innerhalb Spalten
- [ ] Validierung (alle Spalten haben min. 1 Tag)
- [ ] "Nicht zugeordnet"-Pool unterhalb Grid
- [ ] Fehlermarkierungen (rote Spaltenüberschrift bei leer)
- [ ] Verbindungslinien zwischen Original und Übersetzung (optional)
- [ ] Spaltenbreite dynamisch anpassen
- [ ] Speichern nur bei vollständiger Zuordnung
- [ ] Optional: Auto-Zuordnung per AI
- [ ] Optional: Undo/Redo für Zuordnungen
- [ ] Optional: Zoom für lange Sätze
- [ ] Optional: Horizontales Scrollen bei vielen Wörtern

---

## Typische User-Flows

### Flow 1: Neue Übersetzung mit AI
1. User gibt Titel und Originaltext ein
2. Wählt Sprachen
3. Klickt "Generate (AI)"
4. AI erstellt natürliche Übersetzung + Wort-Zuordnung (Interleaved)
5. User sieht Interleaved-Grid mit vorgeschlagenen Zuordnungen
6. User prüft und korrigiert Zuordnung per Drag & Drop zwischen Spalten
7. Speichert Übersetzung

### Flow 2: Manuelle Übersetzung
1. User gibt Titel und Originaltext ein
2. Gibt natürliche Übersetzung manuell ein
3. System tokenisiert beide Texte und erstellt Interleaved-Grid
4. Originalwörter stehen in Spalten, alle Übersetzungswörter im "Nicht zugeordnet"-Pool
5. User zieht jedes Übersetzungswort in die passende Spalte
6. Grid zeigt die Zuordnungen vertikal untereinander
7. Speichert wenn alle Spalten gefüllt

### Flow 3: Bestehende Übersetzung korrigieren
1. User wählt Übersetzung aus Combobox
2. Sieht Übersetzung im VIEW-Modus (Interleaved-Grid, read-only)
3. Klickt "Edit"
4. Ändert natürliche Übersetzung
5. Neue Wörter erscheinen in "Nicht zugeordnet"
6. User ordnet neue Wörter in Spalten zu
7. Kann bestehende Tags zwischen Spalten verschieben
8. Speichert Änderungen

### Flow 4: Wort zwischen Spalten verschieben
1. User ist im EDIT-Modus mit Interleaved-Grid
2. Sieht: "the → der" aber möchte "on → auf der"
3. Greift Tag "der" in Spalte "the"
4. Alle Spalten zeigen Drop-Zonen
5. Zieht "der" horizontal zur Spalte "on"
6. Lässt los → "der" erscheint unter "auf" in Spalte "on"
7. Grid aktualisiert Ansicht
```
Vorher:              Nachher:
on    the           on      the
│     │             │       │
auf   der           auf     ∅
                    der
```

---

## Visuelle Vergleiche: Verschiedene Zuordnungsoptionen

Die Interleaved-Darstellung zeigt deutlich verschiedene Interpretationen:

### Beispiel: "I want to go"

**Option 1: "to" bei "want"**
```
I      want    to     go
│      │       │      │
Ich    will    ∅      gehen
       zu
```

**Option 2: "to" bei "go"**
```
I      want    to     go
│      │       │      │
Ich    will    ∅      gehen
                      zu
```

**Option 3: "to" leer lassen**
```
I      want    to     go
│      │       │      │
Ich    will    ∅      gehen
```

### Beispiel: "the old man"

**Option 1: "the" → "der"**
```
the    old     man
│      │       │
der    alte    Mann
```

**Option 2: "the" bei "man" integriert**
```
the    old     man
│      │       │
∅      alte    Mann
              der
```

**Option 3: "the" verteilt**
```
the    old     man
│      │       │
der    alte    ∅
```

### Vorteil der Interleaved-Darstellung
- **Verschiedene Ansätze sichtbar**: User kann experimentieren
- **Schneller Vergleich**: Alle Optionen auf einen Blick
- **Lerneffekt**: User versteht Sprachstrukturen besser
- **Flexibilität**: Keine "richtige" Zuordnung erzwungen
