# Qualität der Wort-für-Wort-Übersetzung

**Stand:** 2026-10-16
**Status:** Entwurf, Grundlage für Schritt 3 (Positionen) und Schritt 4 (Provider/pydantic-ai 2.x)

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

## Datenmodell (Voraussetzung, Schritt 3)

Zuordnungen werden über **Positionen** gespeichert, nicht über Wort-Texte:

- `source_tokens`: Zerlegung des Originalsatzes (Code)
- `target_tokens`: Zerlegung der natürlichen Übersetzung (Code)
- Zuordnung: pro Quell-Position eine Liste von Ziel-Positionen
- Pro Zuordnung: `confidence` (0–1, optional) und `status` (`suggested` | `flagged` | `confirmed`)

Die Birkenbihl-Regel wird damit zu einer Mengenprüfung: Die Ziel-Positionen aller Spalten bilden genau
`{0 … len(target_tokens)-1}`, ohne Doppelte. Der Bindestrich-Text („vermissen-werde“) wird nur für die Anzeige
erzeugt. Wiederholte Wörter („der Hund und der Mann“) sind eindeutig.

Bekannter Fehler im heutigen Editor (`GridState` ordnet über Text zu): siehe
`tests/integration/test_grid_editing_workflow.py::test_repeated_source_word_keeps_its_own_target` (xfail).

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

## Selbstkorrektur des LLM

Verletzt ein LLM-Vorschlag die Regeln, wird die konkrete Fehlermeldung über einen pydantic-ai
Output-Validator (`ModelRetry`) zurückgegeben („'dich' fehlt“). Begrenzte Anzahl Versuche, danach
geht der Satz `flagged` an den Nutzer.

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

1. Schritt 3: Positionen + `confidence`/`status` im Modell, Editor hebt `flagged` hervor.
2. Schritt 4: Provider-Schicht vereinfachen, pydantic-ai ≥ 2.45 (Voraussetzung für Jev), Selbstkorrektur.
3. Prüfdatensatz-Benchmark, dann Jev Rolle A und B messen.
