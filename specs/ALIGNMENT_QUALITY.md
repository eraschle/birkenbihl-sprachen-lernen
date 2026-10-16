# Qualität der Wort-für-Wort-Übersetzung

**Stand:** 2026-10-16
**Status:** Datenmodell (Schritt 3) und Selbstkorrektur (Schritt 4) umgesetzt; Prüfdatensatz und Jev offen

Die Wort-für-Wort-Übersetzung („Dekodieren“) ist der Kern der Birkenbihl-Methode und muss stimmen.
Sprachmodelle sind dafür nicht trainiert und machen Fehler. Deshalb vertraut die App keinem einzelnen
Modell, sondern kombiniert harte Regeln, unabhängige Zweitmeinungen und den Menschen als letzte Instanz.

## Aufgabenteilung

| Schritt | Wer | Warum |
|---|---|---|
| Natürliche Übersetzung | Sprachmodell (LLM) | Braucht freien Text |
| Zerlegung in Wörter | Code (deterministisch) | Nie der KI überlassen |
| Wortzuordnung (Vorschlag) | LLM oder Jev | Siehe unten |
| Regelprüfung | Code | Jedes Wort der natürlichen Übersetzung genau einmal, jedes Quellwort mindestens ein Zielwort |
| Unsicherheit erkennen | Jev und/oder Zweitlauf | Markiert Wörter zur Prüfung |
| Endgültige Entscheidung | Nutzer im Editor | Geprüfte Sätze werden nie von der KI überschrieben |

## Datenmodell (umgesetzt in Schritt 3)

Zuordnungen werden über **Positionen** gespeichert, nicht über Wort-Texte (`models/translation.py`):

- `Sentence.source_tokens` / `Sentence.target_tokens`: Zerlegung per `tokenize_clean`, aus dem Text abgeleitet
  (nicht gespeichert, damit Text und Zerlegung nie auseinanderlaufen; der Tokenizer gehört damit zum Datenformat)
- `WordAlignment`: `source_index`, `target_indices` (Anzeige-Reihenfolge), `status`
  (`suggested` | `flagged` | `confirmed`)
- `models/alignment.py`: `align_word_pairs()` übersetzt KI-Wortpaare in Positionen. Wiederholte Wörter werden der
  Reihe nach zugeordnet. Was nicht passt, wird nicht geraten: Die Spalte wird `flagged`, übrig gebliebene Wörter
  landen im Pool des Editors.
- `models/validation.py`: Positionsgenaue Prüfung. Jedes Quellwort genau eine Zuordnung mit mindestens einem
  Zielwort, jedes Wort der natürlichen Übersetzung genau einmal. Die frühere Mengen-Prüfung hat doppelte Wörter
  („der … der“) nicht erkannt.
- Editor (`GridState`): Dieselbe Validierung wie beim Speichern; vom Nutzer veränderte Spalten werden `confirmed`,
  `flagged` Spalten sind orange markiert, leere rot.

- „✓ Stimmt“-Knopf auf markierten Spalten mit Wort: bestätigt einen korrekten KI-Vorschlag ohne Verschieben.
  Bewusst nur pro Spalte, kein „alle bestätigen“: jede unsichere Zuordnung soll einzeln angesehen werden.

Noch nicht umgesetzt: `confidence` pro Zuordnung. Das Feld kommt mit dem ersten Erzeuger (Jev oder Zweitlauf),
damit kein ungenutztes Feld im Modell steht.

## Jev (TypeSafe AI)

Fakten aus `pydantic_ai/models/typesafe.py` (pydantic-ai-slim 2.49.0):

- Unterstützt ab **pydantic-ai 2.45** (Extra `typesafe`, Paket `typesafe-sdk`), Modell `typesafe:jev-latest`.
  Für reproduzierbare Schwellwerte eine feste Version verwenden (z. B. `jev-1.13.0`).
- Erzeugt **keinen Text**. Beantwortet typisierte Fragen: `bool`, `Literal`/`Enum` (max. 255 Optionen),
  `list[Literal]` (ein Ja/Nein pro Option), `float` mit `ge=0, le=1` (Wahrscheinlichkeit), Skala 0–10.
- Konfidenz und Wahrscheinlichkeitsverteilungen stehen in `ModelResponse.provider_details`
  (`confidence`, `probabilities`). `typesafe_boolean_threshold` steuert die Ja/Nein-Schwelle.

Folgerung: Jev kann die natürliche Übersetzung **nicht** liefern, aber die Wortzuordnung, sobald die
natürliche Übersetzung und ihre Zerlegung feststehen.

### Rolle A: Jev als Wort-für-Wort-Zuordner

1. LLM liefert die natürliche Übersetzung, Code zerlegt beide Sätze.
2. Pro Quellwort eine Frage `list[Literal[<Ziel-Tokens>]]` („Welche Wörter der Übersetzung gehören zu
   'extrañaré'?“) → Wahrscheinlichkeitsmatrix `P[quelle][ziel]`.
3. Code verteilt jedes Ziel-Token auf die Quell-Spalte mit der höchsten Wahrscheinlichkeit.
   Damit ist „jedes Wort genau einmal“ **durch Konstruktion** erfüllt, nicht durch Hoffen auf das Modell.
4. Leere Spalten oder Tokens mit knappem Vorsprung (zweitbeste Spalte fast gleich wahrscheinlich)
   werden `flagged`.

Offene Frage: Doppelte Ziel-Tokens („der … der“) brauchen unterscheidbare Optionen, z. B. `der#1`, `der#4`.

### Rolle B: Jev als Kontrolleur eines LLM-Vorschlags

Das LLM schlägt die Zuordnung vor (wie heute). Jev bekommt pro Zuordnung eine Frage
`float (0–1)`: „Ist 'dich' im Kontext eine Übersetzung von 'te'?“. Zuordnungen unter einer Schwelle
werden `flagged`. Widersprechen sich LLM und Rolle-A-Matrix, ebenfalls `flagged`.

### Welche Rolle?

Wird mit dem Prüfdatensatz gemessen, nicht vorab entschieden. Beide Rollen nutzen dieselbe Schnittstelle
im Code (Zuordnung + Konfidenz pro Paar), damit LLM, Jev oder ein klassischer Aligner (z. B. SimAlign)
austauschbar sind.

## Selbstkorrektur des LLM (umgesetzt in Schritt 4)

`BaseTranslator._align()`: Ein pydantic-ai Output-Validator gleicht jede Antwort mit `align_word_pairs()` ab und
prüft sie mit `validate_alignment_complete()`. Bei Verstößen geht die konkrete Meldung als `ModelRetry` zurück
(„Quellwörter ohne Zielwort: te. Fehlende Wörter: dich …“, oder Zielwörter, die nicht in der Übersetzung
stehen). Nach `ALIGNMENT_RETRIES` (2) Korrekturen wird der letzte Versuch mit `flagged`-Spalten übernommen
statt abzubrechen. Das Modell bekommt dieselben bereinigten Tokens, gegen die geprüft wird.

## Prüfdatensatz

`tests/fixtures/birkenbihl_unit1_1.json` enthält echte Kursdaten mit erwarteter Wort-für-Wort-Übersetzung.
Ein Benchmark (nicht Teil der normalen Testsuite, braucht API-Keys) misst pro Modell/Prompt/Rolle:

- Anteil exakt korrekter Sätze
- Anteil korrekter Zuordnungen
- Trefferquote der Markierung: Wie viele falsche Zuordnungen wurden `flagged`, wie viele richtige
  unnötig?

Die letzte Zahl ist für die Lernmethode die wichtigste: Ein Fehler, der markiert wird, ist harmlos, weil
der Nutzer ihn prüft. Gefährlich ist nur der unmarkierte Fehler.

## Reihenfolge

1. ~~Schritt 3: Positionen + `status` im Modell, Editor hebt `flagged` hervor.~~ Erledigt.
2. ~~Schritt 4: Provider-Schicht vereinfachen, pydantic-ai ≥ 2.45 (Voraussetzung für Jev), Selbstkorrektur.~~ Erledigt.
3. Prüfdatensatz-Benchmark, dann Jev Rolle A und B messen.
