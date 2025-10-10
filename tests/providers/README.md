# Translation Provider Tests

Dieses Verzeichnis enthält Tests für die Translation Provider gemäß den Anforderungen aus `specs/ORIGINAL_REQUIREMENTS.md`.

## Test-Struktur

```
tests/providers/
├── conftest.py                      # Shared fixtures und Test-Daten
├── test_base_translator.py         # Unit tests für BaseTranslator (mit Mocks)
├── test_openai_translator.py       # Integration tests für OpenAITranslator
└── test_anthropic_translator.py    # Integration tests für AnthropicTranslator
```

## Test-Kategorien

### Unit Tests (`@pytest.mark.unit`)
- Verwenden Mocks für AI-Aufrufe
- Schnell und ohne API-Keys ausführbar
- Testen die Kern-Logik isoliert

### Integration Tests (`@pytest.mark.integration`, `@pytest.mark.slow`)
- Machen echte API-Aufrufe zu OpenAI/Anthropic
- Benötigen API-Keys in `.env`
- Testen die komplette Integration

## Tests Ausführen

### Alle Unit Tests (schnell, ohne API-Keys)
```bash
uv run pytest tests/providers/ -m unit -v
```

### Nur Integration Tests (benötigt API-Keys)
```bash
# Sicherstellen dass .env konfiguriert ist
cp .env.example .env
# OPENAI_API_KEY und/oder ANTHROPIC_API_KEY eintragen

uv run pytest tests/providers/ -m integration -v
```

### Alle Tests (Unit + Integration)
```bash
uv run pytest tests/providers/ -v
```

### Bestimmte Test-Datei
```bash
uv run pytest tests/providers/test_base_translator.py -v
```

## Getestete Anforderungen

Die Tests validieren die Birkenbihl-Methode Anforderungen:

### ✅ Phase 1: Übersetzen (Natürliche Übersetzung)
- `test_natural_translation_exists`: Natürliche, flüssige Übersetzung wird generiert
- Alle Provider liefern lesbare deutsche Übersetzungen

### ✅ Phase 1: Dekodieren (Wort-für-Wort)
- `test_word_by_word_translation_exists`: Word-by-Word Alignments vorhanden
- `test_word_alignment_position_ordering`: Sequentielle Positions-Nummerierung für UI-Alignment
- `test_hyphenated_compound_words`: Compound Words mit Bindestrichen (z.B. "vermissen-werde")

### ✅ Formatierung
- `test_all_words_from_natural_used_in_alignments`: Alle Wörter aus natürlicher Übersetzung in Alignments
- Position-basiertes Ordering für vertikales UI-Alignment

### ✅ Sprachen
- Englisch → Deutsch: `test_translate_english_to_german_simple`
- Spanisch → Deutsch: `test_translate_spanish_to_german`
- Language Detection: `test_detect_language_*`

### ✅ Speicherung
- `test_metadata_preserved`: UUIDs, Timestamps, Metadaten werden korrekt gespeichert
- Cross-Storage Kompatibilität (JSON, SQLite, Excel)

## Test-Beispiele aus ORIGINAL_REQUIREMENTS.md

Die Tests verwenden reale Beispiele aus den Anforderungen:

```python
# Beispiel 1: Yo te extrañaré
Source:     "Yo te extrañaré"
Natural:    "Ich werde dich vermissen"
Word-Alignments:
  - "Yo" → "Ich" (position 0)
  - "te" → "dich" (position 1)
  - "extrañaré" → "vermissen-werde" (position 2)

# Beispiel 2: Fueron tantos bellos y malos momentos
Source:     "Fueron tantos bellos y malos momentos"
Natural:    "Waren so viele schöne und schlechte momente"
Word-Alignments:
  - "Fueron" → "Waren" (position 0)
  - "tantos" → "so-viele" (position 1)
  - "bellos" → "schöne" (position 2)
  - ...
```

## Fixtures (conftest.py)

Gemeinsame Test-Daten für konsistente Tests:

- `sample_english_german_response`: "Hello world" EN→DE
- `sample_spanish_german_response`: "Yo te extrañaré" ES→DE
- `sample_multi_sentence_response`: Mehrere Sätze
- `sample_complex_spanish_response`: "Fueron tantos..."
- `sample_dekodierung_example`: "Lo que parecía..."

## Code Coverage

Die Provider-Tests erreichen hohe Coverage für:
- ✅ `base_translator.py`: 100%
- ✅ `models.py`: 100%
- ✅ `prompts.py`: 100%
- ⚠️ `openai_translator.py`: 67% (Integration-Tests nur mit API-Key)
- ⚠️ `anthropic_translator.py`: 67% (Integration-Tests nur mit API-Key)

Für 100% Coverage alle Tests inkl. Integration ausführen:
```bash
uv run pytest tests/providers/ --cov=src/birkenbihl/providers
```
