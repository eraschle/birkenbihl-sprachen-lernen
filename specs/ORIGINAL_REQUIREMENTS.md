# Birkenbihl Learning App - Ursprüngliche Anforderungen

## Was der User wirklich wollte:

### Hauptziel

Eine einfache Python-App zur Digitalisierung der Vera F. Birkenbihl Sprachlernmethode

### Konkrete Anforderungen

1. **Text-Übersetzung nach Birkenbihl-Methode:**
   - Natürliche Übersetzung (*Siehe Formatierung-Natürlich*)
   - DE und ES sind mögliche Sprachen. Die Sprachen sollen jedoch jederzeit anpassbar sein
   - Wort-für-Wort Übersetzung (*Siehe Formatierung-Dekodierung*)
   - UI soll Wörter einer Zeile auseinanderziehen für vertikale Alignment

2. **Speicherung:**
   - Übersetzungen speichern
   - Dekodierung speichern ohne das die Dekodierung verloren geht
   - SQLite mit SQLModel - was weniger umständlich ist

3. **Audio:**
   - Stimme für klare, deutliche Aussprache der Original Sprache

4. **Technische Vorgaben:**
   - Python 3.13 mit uv
   - UI: NiceGUI (native=True, PyWebView oder Electron) verwenden
   - Übersetzung: generisch mit AI-Anbieter-Abstraktion aus Config
   - Keine typing imports für list, dict, tuple Union/Optional in neuer Syntax
   - SOLID + Design Patterns
   - Protokolle für Anpassungen
   - Ruff (max 120 Zeichen), Pyright
   - src-Layout

### Birkenbihl-Methode Schritte:
1. **Dekodieren:** Wort-für-Wort Übersetzung
2. **Aktives Hören:** Text lesen + Original anhören
3. **Passives Hören:** Audio im Hintergrund bei anderen Aktivitäten
4. **Aktivitäten:** Sprechen, Schreiben usw.

### Formatierung 

#### **Natürlich:** 
_Der originale Text und die Übersetzung werden untereinander geschrieben ohne spezielle Formatierung_

Lo que parecía no importante
unwichtig schien

#### **Dekodierung:** 
_Zwischen dem längeren Wort um dem nächsten Wort gibt es 2 Leerzeichen_

Tenlo   por  seguro
Hab-es  für  sicher

Fueron  tantos    bellos y    malos momentos
Waren   so-viele  schöne und  schlechte momente

Lo   que  parecía  no     importante
Das  was  schien   nicht  wichtig


### Was NICHT verlangt wurde:
- Komplexe Architekturen
- Dutzende von Dateien
- Stundenlange Implementierung
- Über komplizierte Lösungen

### Einfache Erwartung:
- Ansprechendes Design
- Übersetzung und Dekodierung in getrennten Bereichen darstellen
- Eine funktionsfähige App die einen Text nimmt, 
- übersetzt (natürlich + wort-für-wort), 
- UI aligned anzeigt, speichert und vorliest.
