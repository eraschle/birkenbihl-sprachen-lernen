# Birkenbihl Sprachlern-App

Eine Python-Anwendung zur Digitalisierung der Vera F. Birkenbihl Sprachlernmethode.

## Features

- **Automatische Spracherkennung** (Englisch/Spanisch → Deutsch)
- **Doppelte Übersetzung** nach Birkenbihl-Methode:
  - Natürliche, fließende Übersetzung
  - Wort-für-Wort Übersetzung für Sprachstruktur-Verständnis
- **Multi-Provider Support**: OpenAI und Anthropic Claude
- **Konfigurierbare Provider**: Mehrere AI-Provider in settings.yaml
- **CLI Interface**: Vollständige Kommandozeilen-Schnittstelle
- **Streamlit GUI**: Moderne Web-UI mit Provider-Verwaltung
- **JSON Storage**: Persistente Speicherung von Übersetzungen

## Installation

1. Python 3.13 installieren
2. Repository klonen
3. Dependencies installieren:

```bash
uv sync
```

4. Konfiguration einrichten:

```bash
# Provider-Konfiguration erstellen
cp settings.yaml.example settings.yaml
# settings.yaml bearbeiten: API Keys und Provider konfigurieren
```

**Empfohlen**: API Keys direkt in `settings.yaml` speichern (siehe `settings.yaml.example`).

**Alternative**: API Keys in `.env` speichern:
```bash
cp .env.example .env
# .env bearbeiten und in settings.yaml referenzieren: api_key: ${OPENAI_API_KEY}
```

## Verwendung

### CLI

```bash
# Übersetzung mit Auto-Spracherkennung
birkenbihl translate "Hello world"

# Übersetzung mit bestimmter Quellsprache
birkenbihl translate "Yo te extrañaré" -s es -t de

# Mit bestimmtem Provider
birkenbihl translate "Hello" -p "Claude Sonnet"

# Alle gespeicherten Übersetzungen anzeigen
birkenbihl list

# Bestimmte Übersetzung anzeigen
birkenbihl show <id>
```

### GUI (Streamlit)

```bash
birkenbihl-gui
```

Die App öffnet sich im Browser unter `http://localhost:8501`.

## Birkenbihl-Methode

Die App implementiert die 4 Schritte der Birkenbihl-Sprachlernmethode:

1. **Dekodieren**: Wort-für-Wort Übersetzung zum Verstehen der Sprachstruktur
2. **Aktives Hören**: Text lesen während Original-Audio läuft
3. **Passives Hören**: Audio im Hintergrund bei anderen Aktivitäten
4. **Aktivitäten**: Sprechen, Schreiben etc.

## Technische Details

- **Backend**: Python 3.13, Pydantic, Pydantic-AI
- **Frontend**: Streamlit (GUI), Click + Rich (CLI)
- **Storage**: JSON (SQLite geplant)
- **AI-Provider**: OpenAI GPT-4/4o, Anthropic Claude (via Pydantic-AI)
- **Audio**: Geplant (Phase 2)
- **Architektur**: SOLID-Prinzipien mit Protocol-basierter Abstraktion
- **Configuration**: YAML-basierte Multi-Provider Settings
