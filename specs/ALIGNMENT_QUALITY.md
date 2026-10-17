# Qualität der Wort-für-Wort-Übersetzung

**Stand:** 2026-10-17
**Status:** Datenmodell (Schritt 3), Selbstkorrektur (Schritt 4) und Jev als Zuordner (Rolle A) umgesetzt;
Jev als Kontrolleur (Rolle B) und fester Benchmark offen

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

### Rolle A: Jev als Wort-für-Wort-Zuordner (umgesetzt)

Einstellung `word_aligner: jev` in `settings.yaml`, Key in `jev_api_key` oder `TYPESAFE_API_KEY`.

1. LLM liefert die natürliche Übersetzung, Code zerlegt beide Sätze.
2. `JevAligner` (`providers/jev_aligner.py`): **eine** Anfrage pro Satz mit einer Frage pro Wortpaar,
   als `float` mit `ge=0, le=1` („Wahrscheinlichkeit, dass 'dich' (Wort 3) 'te' (Wort 2) übersetzt“)
   → Wahrscheinlichkeitsmatrix `P[quelle][ziel]`. Die Positionen stehen in jeder Frage, damit doppelte
   Wörter („der … der“) unterscheidbar sind. `float` statt `dict[Literal, bool]`, weil pydantic-ai eine
   Auswahl aus nur einer Option ablehnt (einwortige Übersetzung).
3. `align_by_probability()` (`models/alignment.py`) gibt jedes Ziel-Token der Quell-Spalte mit der höchsten
   Wahrscheinlichkeit. Damit ist „jedes Wort genau einmal“ **durch Konstruktion** erfüllt.
4. `flagged` wird eine Spalte, wenn eines ihrer Wörter unter `MIN_PROBABILITY` (0,5) liegt oder weniger als
   `MIN_MARGIN` (0,15) vor der zweitbesten Spalte. Quellwörter ohne Zielwort bleiben **leer** und `flagged`.
   Ein Versuch, ihnen Wörter aus vollen Spalten zu geben, hat im Test meist falsch geraten („city → sind“)
   und dabei richtige Spalten zerstört („went → sind-gegangen“); deshalb wird nicht geraten.

Erste Messung (2026-10-17, 40 Sätze aus `birkenbihl_unit1_1.json`, einmaliges Skript, noch nicht im Repo):

| Zuordner | Sätze exakt | Spalten richtig | Falsch, markiert | Falsch, **nicht** markiert | Richtig, aber markiert | Zeit/Satz | Kosten/1000 Sätze |
|---|---|---|---|---|---|---|---|
| LLM (claude-sonnet-5-5) | 40/40 | 242/242 | 0 | 0 | 0 | 1,9 s | 7,95 $ |
| LLM (claude-haiku-5-5) | 40/40 | 242/242 | 0 | 0 | 0 | 2,0 s | 0,46 $ |
| Jev (jev-latest) | 39/40 | 240/242 | 2 | 0 | 8 | 0,3 s | 0,19 $ |

Kosten nur für den Zuordnungs-Schritt, berechnet von pydantic-ai/genai-prices aus den Tokens (10 Sätze).

**Schwere Sätze** (2026-10-17, `tests/fixtures/alignment_hard_cases.json`: 13 Sätze mit echter natürlicher
Übersetzung, Umstellungen, trennbaren Verben, Klitika, Pro-drop, Wortwiederholungen; erzeugt von
claude-fable-5-1, von Hand geprüft und korrigiert). Skript: `scripts/benchmark_alignment.py`, ein Lauf:

| Zuordner | Sätze exakt | Spalten richtig | Falsch, markiert | Falsch, **nicht** markiert | Richtig, aber markiert | Zeit/Satz | Kosten/Satz |
|---|---|---|---|---|---|---|---|
| LLM (claude-sonnet-5-5) | 11/13 | 218/226 | 0 | 8 | 0 | 4,0 s | 0,0120 $ |
| LLM (claude-haiku-5-5) | 11/13 | 222/226 | 0 | 4 | 0 | 5,6 s | 0,0010 $ |
| Jev (jev-latest) | 3/13 | 179/226 | 33 | 14 | 27 | 0,6 s | 0,0012 $ |

Befund:

- Bei schweren Sätzen ist Jev als Zuordner deutlich schlechter: 14 unmarkierte Fehler. Typisch sind
  Pro-drop-Subjekte (spanisch „llegué“ → „kam-ich“: Jev gibt „ich“ nicht dem Verb) und Wortwiederholungen
  („whom → den-den“, „las → die-die“): Die Position in der Frage reicht Jev nicht zur Unterscheidung.
  Jev ist nur schneller; die Kosten steigen mit Quellwörter × Zielwörter und liegen bei langen Sätzen
  auf Haiku-Niveau.
- Haiku ist so gut wie Sonnet (hier sogar besser) bei einem Zwölftel der Kosten. Sonnets Fehler betreffen
  spanische Klitika und Pro-drop („me encontré“), Haikus zwei davon sind strittig („could have“ →
  „hätten können“ kreuzweise).
- Die LLMs markieren ihre Fehler nie, weil die Selbstkorrektur nur Regelverstöße erkennt, nicht falsche
  Zuordnungen innerhalb der Regeln. Hier könnte Jev als Kontrolleur (Rolle B) helfen, muss aber erst
  gemessen werden.
- Ein Lauf mit 13 Sätzen: Abweichungen von ±2 Fehlern zwischen Läufen sind zu erwarten.

Vorbehalt: Der Datensatz hat nur die erwartete Wort-für-Wort-Übersetzung. Als „natürliche Übersetzung“
bekamen beide Zuordner deren Wörter **in Quell-Reihenfolge**. Das ist leichter als echte natürliche
Übersetzungen mit umgestellter Wortstellung. Für eine aussagekräftige Messung braucht der Datensatz die
natürliche Übersetzung je Satz.

Grenzen:

- Reihenfolge innerhalb einer Spalte ist die der natürlichen Übersetzung („werde-vermissen“ statt
  „vermissen-werde“). Jev beantwortet keine Reihenfolge-Fragen ohne weitere Anfrage.
- Anzahl Fragen = Quellwörter × Zielwörter. Ein Satz mit 20 × 21 Wörtern lief in 0,6 s.
- Schwellwerte sind gegen `jev-latest` gesetzt; für stabile Ergebnisse auf eine feste Version wechseln
  (`JEV_MODEL` in `providers/catalog.py`).

### Rolle B: Jev als Kontrolleur eines LLM-Vorschlags

Noch nicht umgesetzt. Das LLM schlägt die Zuordnung vor (wie heute). Jev bekommt pro Zuordnung eine Frage
`float (0–1)`: „Ist 'dich' im Kontext eine Übersetzung von 'te'?“. Zuordnungen unter einer Schwelle
werden `flagged`. Widersprechen sich LLM und Rolle-A-Matrix, ebenfalls `flagged`.

### Welche Rolle?

Wird mit dem Prüfdatensatz gemessen, nicht vorab entschieden. Zuordner implementieren `IWordAligner`
(`protocols/alignment.py`), damit LLM, Jev oder ein klassischer Aligner (z. B. SimAlign) austauschbar sind.

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
3. ~~Jev Rolle A (Zuordner) mit `IWordAligner`-Schnittstelle.~~ Erledigt.
4. Benchmark als festes Skript, Jev Rolle B (Kontrolleur eines LLM-Vorschlags) messen.
