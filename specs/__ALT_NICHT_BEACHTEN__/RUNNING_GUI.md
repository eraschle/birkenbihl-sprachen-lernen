# Running the Birkenbihl GUI

Die Birkenbihl-Anwendung verfügt jetzt über eine native Qt-basierte GUI (PySide6).

## Voraussetzungen

Stelle sicher, dass alle Dependencies installiert sind:

```bash
uv sync
```

## Konfiguration

Erstelle eine `settings.yaml` im Benutzerverzeichnis:

```bash
# Kopiere die Beispiel-Konfiguration
cp settings.yaml.example ~/.birkenbihl/settings.yaml

# Bearbeite und füge deinen API-Key hinzu
nano ~/.birkenbihl/settings.yaml
```

Beispiel `settings.yaml`:

```yaml
providers:
  - name: "OpenAI GPT-4"
    provider_type: "openai"
    model: "gpt-4"
    api_key: "sk-..."
    is_default: true
    supports_streaming: true

target_language: "de"
```

## GUI Starten

### Option 1: Mit dem Entry Point

```bash
birkenbihl-gui
```

### Option 2: Direkt mit Python

```bash
uv run python -m birkenbihl.gui.main
```

### Option 3: Via main.py

```bash
uv run python -c "from birkenbihl.main import main_gui; main_gui()"
```

## Features

Die GUI bietet drei Hauptansichten:

### 1. Translation View (Neue Übersetzung)
- Titel eingeben
- Quelltext eingeben
- Quell- und Zielsprache wählen
- Provider auswählen
- Übersetzung mit Fortschrittsanzeige

### 2. Editor View (Übersetzung bearbeiten)
- Bestehende Übersetzungen laden
- Sätze durchgehen
- Natürliche Übersetzung bearbeiten
- Word-by-Word Alignment anpassen
- Änderungen speichern

### 3. Settings View (Einstellungen)
- Provider hinzufügen/bearbeiten/löschen
- Default Provider festlegen
- Zielsprache ändern
- Einstellungen speichern

## Menü

- **Datei**
  - Neue Übersetzung
  - Übersetzung bearbeiten
  - Beenden

- **Ansicht**
  - Erstellen
  - Editor
  - Einstellungen

- **Hilfe**
  - Über Birkenbihl

## Tastenkürzel

Die Standard-Qt-Tastenkürzel funktionieren:
- `Ctrl+Q` - Beenden
- `Alt+F` - Datei-Menü
- `Alt+A` - Ansicht-Menü
- `Alt+H` - Hilfe-Menü

## Troubleshooting

### GUI startet nicht

**Problem:** `ModuleNotFoundError: No module named 'PySide6'`

**Lösung:**
```bash
uv sync
```

### Kein Provider konfiguriert

**Problem:** `RuntimeError: No default provider configured`

**Lösung:**
1. Erstelle `~/.birkenbihl/settings.yaml`
2. Füge mindestens einen Provider mit `is_default: true` hinzu

### Settings werden nicht geladen

**Problem:** Settings werden nicht gefunden

**Lösung:**
```bash
# Prüfe ob die Datei existiert
cat ~/.birkenbihl/settings.yaml

# Erstelle das Verzeichnis wenn nötig
mkdir -p ~/.birkenbihl
```

## Entwicklung

### Tests ausführen

```bash
# Alle GUI Tests (mit Segfault-Warnung bei großen Suites)
uv run pytest tests/gui/ --no-cov

# Nur Command Tests (stabil)
uv run pytest tests/gui/commands/ --no-cov

# Nur ViewModel Tests (stabil)
uv run pytest tests/gui/models/test_settings_viewmodel.py --no-cov
```

### Logs aktivieren

Die GUI nutzt Python's logging:

```bash
# In main.py ist Logging bereits konfiguriert
# Logs werden auf stdout ausgegeben
```

## Architektur

Die GUI folgt dem MVVM (Model-View-ViewModel) Pattern:

```
┌──────────────────────────────────────┐
│           MainWindow                 │
│  ┌────────────────────────────────┐ │
│  │      QStackedWidget            │ │
│  │  ┌──────────────────────────┐ │ │
│  │  │   TranslationView        │ │ │
│  │  │   + ViewModel            │ │ │
│  │  └──────────────────────────┘ │ │
│  │  ┌──────────────────────────┐ │ │
│  │  │   EditorView             │ │ │
│  │  │   + ViewModel            │ │ │
│  │  └──────────────────────────┘ │ │
│  │  ┌──────────────────────────┐ │ │
│  │  │   SettingsView           │ │ │
│  │  │   + ViewModel            │ │ │
│  │  └──────────────────────────┘ │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
         │
         ├─> TranslationService
         ├─> SettingsService
         └─> StorageProvider (JSON)
```

Siehe `GUI_REFACTORING.md` für Details zur Architektur.
