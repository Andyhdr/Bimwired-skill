# Elektroplanung in Revit: ein KI-Skill

Fachwissen und zwei offline laufende Rechner für die Elektroplanung mit Revit nach deutschen Normen, verpackt als Skill für ChatGPT, Claude, Codex und Cursor.

Die Texte stammen aus der Planungspraxis von Rowan Hamid, Elektrofachplanerin und BIM-Koordinatorin, veröffentlicht als [Praxiswissen auf bimwired.com](https://bimwired.com/landing/wissen/). Die Skripte rechnen dasselbe wie das Werkzeug BimWired, nur offen nachvollziehbar in Python.

## Was drin ist

- **12 Fachartikel und Checklisten**: Stromkreise in Revit aufteilen, Verteilerplan und Stromlaufplan nach DIN EN 61082-1, VDE-Regelprüfung, Leistungsbilanz nach DIN 18015-1, Revit-Familienbibliothek für TGA, Familien definieren statt modellieren, Software-Vergleich.
- **3 Praxisszenarien** mit offenen Annahmen und Beispielrechnungen.
- **Glossar** mit 14 Begriffen von BCF bis Spannungsfall.
- **`leistungsbilanz.py`**: Leistungsbilanz nach DIN 18015-1 Anhang A mit Sonderlasten, E-Mobilität, PV-Richtungsprüfung, NH-Empfehlung und vollständigem Rechenweg.
- **`stromkreis_check.py`**: Prüfung eines Stromkreisverzeichnisses auf Überlast, Mindestquerschnitt, RCD-Pflicht, Sicherheitstechnik hinter RCD, Drehstrom-Widerspruch, Steckdosenzahl, eigener Stromkreis und Nassraum, dazu ein Vorschlag für Sicherung, Kabel und Phasen.

## Installieren

**ChatGPT:** über das Plugin Directory („Elektroplanung in Revit"), sobald die Prüfung durch OpenAI abgeschlossen ist.

**Claude Code, Codex, Cursor und andere Agenten mit Skill-Ordnern:** diesen Ordner klonen und `skills/elektroplanung-in-revit/` in den Skill-Pfad des Werkzeugs legen (zum Beispiel `~/.claude/skills/` oder `.claude/skills/` im Projekt).

**Ohne Agent:** die Skripte laufen direkt mit Python 3.

```bash
cd skills/elektroplanung-in-revit/scripts
python leistungsbilanz.py --beispiel
python stromkreis_check.py --beispiel
python stromkreis_check.py --vorschlag Wallbox 22000
```

Eine eigene Eingabe beginnt mit `--vorlage`:

```bash
python leistungsbilanz.py --vorlage > meine-bilanz.json
python leistungsbilanz.py meine-bilanz.json
python stromkreis_check.py --vorlage > verzeichnis.csv
python stromkreis_check.py verzeichnis.csv
```

## Tests

```bash
cd skills/elektroplanung-in-revit/scripts
python -m unittest
```

Die Tests enthalten dieselben Fälle wie die Tests des BimWired-Editors, damit Skript und Werkzeug dieselben Zahlen liefern: Stützstellen der Bedarfskurven, Mischbelegung mit Durchlauferhitzern, Lastmanagement, PV-Richtung, Parser für Sicherungs- und Kabelangaben, Vorschläge für Herd, Wallbox, Durchlauferhitzer und Sicherheitstechnik.

## Grenzen

Beide Rechner liefern Planungsgrundlagen mit Normbezug. Verbindlich bleiben die TAB und die Anschlusszusage des Netzbetreibers. Nicht geprüft werden Spannungsfall, Strombelastbarkeit nach Verlegeart und Häufung, Selektivität und Kurzschlussfestigkeit; das bleibt Ingenieurleistung.

## Mitwirken

Fehler in einem Artikel oder einer Regel: Issue in diesem Repository oder E-Mail an info@bimwired.com. Die Artikel werden aus den Quelltexten auf bimwired.com generiert; Korrekturen landen deshalb zuerst dort und dann hier.

## Lizenz

Texte unter `references/`: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de), Rowan Hamid / BimWired. Skripte und alles andere: MIT. Siehe `LICENSE`.

Herausgeber des Skills: Andreas Hauber. Produkt und Marke BimWired: Rowan Hamid, [bimwired.com](https://bimwired.com).
