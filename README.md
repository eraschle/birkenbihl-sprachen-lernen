# Birkenbihl Sprachlern-App

Eine Python-Anwendung zur Digitalisierung der Vera F. Birkenbihl Sprachlernmethode.

## Features

- **Automatische Spracherkennung** (Englisch/Spanisch → Deutsch)
- **Doppelte Übersetzung** nach Birkenbihl-Methode:
  - Natürliche, fließende Übersetzung
  - Wort-für-Wort Übersetzung für Sprachstruktur-Verständnis
- **Wort-Alignment** in der Benutzeroberfläche
- **Audio-Wiedergabe** des Originaltexts
- **Speicherung** aller Übersetzungen in SQLite
- **Moderne Web-UI** mit NiceGUI

## Installation

1. Python 3.13 installieren
2. Repository klonen
3. Dependencies installieren:

```bash
uv sync
```

4. Umgebungsvariablen konfigurieren:

```bash
cp .env.example .env
# .env bearbeiten und API-Schlüssel eintragen
```

## Verwendung

```bash
uv run python -m src.birkenbihl_app.main
```

Die App öffnet sich im Browser unter `http://localhost:8080`.

## Birkenbihl-Methode

Die App implementiert die 4 Schritte der Birkenbihl-Sprachlernmethode:

1. **Dekodieren**: Wort-für-Wort Übersetzung zum Verstehen der Sprachstruktur
2. **Aktives Hören**: Text lesen während Original-Audio läuft
3. **Passives Hören**: Audio im Hintergrund bei anderen Aktivitäten
4. **Aktivitäten**: Sprechen, Schreiben etc.

## Technische Details

- **Backend**: Python 3.13, SQLModel, Pydantic-AI
- **Frontend**: NiceGUI
- **Datenbank**: SQLite
- **AI-Provider**: OpenAI (konfigurierbar)
- **Audio**: pyttsx3 (Text-to-Speech)
- **Architektur**: SOLID-Prinzipien mit Protocol-basierter Abstraktion
