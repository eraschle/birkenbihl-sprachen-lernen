# Birkenbihl Learning App - Ursprüngliche Anforderungen

### Hauptziel

Eine einfache Python-App zur Digitalisierung der Vera F. Birkenbihl Sprachlernmethode

### Birkenbihl-Methode Schritte:
1. **Übersetzen:** _(1. Phase)_
    Der Text wird unter beachtung der Rechtschreibung übersetzt.
2. **Dekodieren:** _(1. Phase)_
    Natürlich Übersetzung wird in eine Wort für Wort übersetzung umgewandelt
3. **Aktives Hören:** _(2. Phase)_
    Text lesen + Original anhören
4. **Passives Hören:** 
    Audio im Hintergrund bei anderen Aktivitäten
5. **Aktivitäten:** 
    Sprechen, Schreiben usw.

### Konkrete Anforderungen

1. **Text-Übersetzung nach Birkenbihl-Methode:**
   - Natürliche Übersetzung (*Siehe Formatierung-Natürlich*)
   - Die ursprüngliche Sprache soll in Deutsch übersetzt werden.
   - Wort-für-Wort Übersetzung (*Siehe Formatierung-Dekodierung*)
   - UI soll Wörter einer Zeile auseinanderziehen für vertikale Alignment

2. **Speicherung:**
   - Übersetzungen speichern 
   - Dekodierung speichern ohne das die Dekodierung verloren geht
   - SQLite mit SQLModel - was weniger umständlich ist

3. **Audio:**
   - Stimme für klare, deutliche Aussprache der Original Sprache

4. **Technische Vorgaben:**
   - src-Layout
   - Python 3.13 
   - UV für Package Verwaltung 
   - Interface (Protkolle) für Übersetzung _(1. Phase)_ und Audio _(2. Phase)_ 
   - Keine typing imports für list, dict, tuple, | für Union und Optional verwenden
   - Ruff (max 120 Zeichen), Pyright
   - SOLID + Design Patterns

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

### Einfache Erwartung:
- Ansprechendes Design
- Übersetzung und Dekodierung in getrennten Bereichen darstellen
- Eine funktionsfähige App die einen Text nimmt, 
- übersetzt (natürlich + wort-für-wort), 
