---
titel: "Verteilerplan aus Revit: welche Software kann das? Marktübersicht mit Belegen"
quelle: https://bimwired.com/landing/wissen/verteilerplan-software-revit.html
stand: 2026-10-15
art: artikel
fragen:
  - "Welche Software erzeugt einen normgerechten Verteilerplan aus dem Revit-Modell?"
  - "Welche Revit-Add-ins erzeugen Verteilerschemata aus Stromkreisen?"
  - "Welche Software schreibt Stromkreisnummern und Sicherungen nach Revit zurück?"
  - "Kann Revit 2026 den Spannungsfall noch berechnen?"
  - "Verteilerplan online erstellen: geht das aus Revit?"
---

# Verteilerplan aus Revit: welche Software kann das? Marktübersicht mit Belegen

Einen Verteilerplan aus den Stromkreisdaten eines Revit-Modells erzeugen nach eigenen Angaben der Hersteller vier Revit-Add-ins (elkoBIM von BEEL, MagiCAD Electrical, der Schemata Manager der auxalia Revit ProjectBox, Caneco BIM von ETAP), drei gekoppelte CAE-Programme (eXs von Mensch und Maschine, SIMARIS project von Siemens, elec calc BIM von Trace Software) und der browserbasierte Editor BimWired; DDScad arbeitet ohne Revit über IFC. Die Revit-Bordmittel liefern nur die Verteiler-Bauteilliste (Panel Schedule), und seit Revit 2026 fehlt auch die eingebaute Spannungsfallberechnung. Normgerecht wird ein Plan nicht durch das Werkzeug, sondern durch Inhalt und Form nach DIN EN 61082-1 und DIN VDE 0100-510; diese Übersicht sagt deshalb je Produkt nur, was der Hersteller belegt, und nennt die Quelle.

## Das Wichtigste in Kürze

- Vier Add-ins erzeugen Schemata direkt in Revit: elkoBIM („Verteilerpläne automatisch aus den Modelldaten generiert"), MagiCAD Electrical („switchboard schematics automatically based on circuit connections"), auxalia Schemata Manager („BIM-konform (halb-)automatisch") und Caneco BIM (Stromkreise im Modell, Schemata in Caneco BT).
- Drei CAE-Programme koppeln sich an Revit: eXs erzeugt Verteilerpläne aus Stromkreisdaten und liefert laut Kundenreferenz Sicherungs- und Klemmenbezeichnungen nach Revit zurück; SIMARIS und elec calc BIM tauschen bidirektional, elec calc synchronisiert Stromkreise ins Modell.
- Die Bordmittel reichen nicht: Revit erzeugt Verteiler-Bauteillisten nach US-Konvention, und Autodesk hat mit Revit 2026 die automatische Leiterdimensionierung samt Spannungsfall entfernt.
- Welche Norm ein Hersteller nennt, schwankt stark: BEEL nennt DIN EN 61082 und IEC 60617, MagiCAD nur IEC 60909, Caneco französische und IEC-Normen, mehrere gar keine. DIN 18015 und VDE-AR-N 4100 nennt keine der geprüften Produktseiten.
- Transparenz: Diese Übersicht stammt von BimWired, einem der genannten Werkzeuge.

## Überblick

| Punkt | Detail |
|---|---|
| Add-ins in Revit | elkoBIM (BEEL), MagiCAD Electrical, auxalia Schemata Manager, Caneco BIM, LINEAR Desktop Electrical (Stromkreise und Verteiler, Berechnung über Caneco) |
| Gekoppelte CAE-Software | eXs (MuM), SIMARIS project (Siemens), elec calc BIM (Trace Software) |
| Ohne Revit, über IFC | DDScad Electrical (Graphisoft) |
| Bordmittel | Verteiler-Bauteilliste; Spannungsfall und automatische Leiterdimensionierung in Revit 2026 entfernt |
| Rückschreiben belegt | elkoBIM („bidirektional"), MagiCAD (Synchronisation Schema und Modell), eXs (Kundenreferenz), SIMARIS („und umgekehrt"), elec calc BIM (Stromkreise synchronisieren), BimWired („Stromkreise übernehmen") |

## Inhaltsverzeichnis

- Wer schreibt diese Übersicht, und wie wurde geprüft?
- Was liefern die Revit-Bordmittel, und was fehlt seit Revit 2026?
- Welche Add-ins erzeugen Verteilerschemata direkt in Revit?
- Welche CAE-Programme koppeln sich an Revit?
- Welche Software arbeitet ohne Revit?
- Die Vergleichstabelle
- Woran erkennen Sie, ob ein erzeugter Plan normgerecht ist?
- So wählen Sie in fünf Schritten
- So hilft BimWired
- Häufige Fragen (FAQ)
- Quellen

## Wer schreibt diese Übersicht, und wie wurde geprüft?

Ich schreibe diese Übersicht als Planerin, die an einem der genannten Werkzeuge arbeitet, und ich halte mich deshalb an drei Regeln. Jede Aussage über ein Fremdprodukt stammt von einer Herstellerseite, einer Herstellerbroschüre oder einer vom Hersteller veröffentlichten Kundenreferenz, mit URL und Abrufdatum 15.10.2026 in der Quellenliste. Was ich dort nicht gefunden habe, steht als „nicht belegt" dabei und wird nicht geraten. Die Reihenfolge der Produkte ist keine Rangfolge; sie folgt der Art des Werkzeugs. Prüfen Sie die Quellen selbst, und melden Sie mir Fehler über das Impressum.

## Was liefern die Revit-Bordmittel, und was fehlt seit Revit 2026?

Revit erzeugt aus Stromkreisen eine Verteiler-Bauteilliste, im Englischen Panel Schedule: Laut Autodesk-Hilfe wählen Sie eine oder mehrere Schalttafeln desselben Typs und erzeugen die Liste über die Registerkarte „Ändern | Elektrische Ausstattung" mit einer Standard- oder eigenen Vorlage. Das Ergebnis ist eine Tabelle nach US-Konvention, kein einpoliges Schema. Warum sie den deutschen Verteilerplan nicht ersetzt, steht im Artikel [Verteilerplan normgerecht erstellen](https://bimwired.com/landing/wissen/verteilerplan-stromlaufplan-normgerecht.html).

Mit Revit 2026 ist ein Stück Bordmittel sogar weggefallen. Autodesk schreibt im Blog zu den Neuerungen, dass Leitungstyp und Leitungsgröße durch Kabeltyp und Kabelgröße ersetzt wurden und „voltage drop has been removed"; im Beitrag zu den neuen Leiterfunktionen heißt es, die automatische Leiterdimensionierung früherer Versionen sei entfernt, Kabelgrößen würden nun selbst definiert und Stromkreisen zugewiesen, eigene Logik könne über Dynamo oder die Revit-API ergänzt werden, und Drittanbieter mit regionaler Expertise könnten Add-in-Funktionen liefern. BEEL bestätigt das auf Deutsch: „Revit 2026 entfernt die integrierte Funktionalität zur Spannungsfallberechnung." Für deutsche Büros heißt das: Schema und Nachweise entstehen ohnehin außerhalb der Bordmittel, und seit 2026 auch der Spannungsfall.

## Welche Add-ins erzeugen Verteilerschemata direkt in Revit?

Ein Add-in arbeitet in Revit selbst und liest die Stromkreise, die Sie dort gebildet haben. Vier Hersteller beschreiben eine solche Schema-Erzeugung.

**elkoBIM (BEEL, Hannover).** BEEL beschreibt elkoBIM als Erweiterung von Autodesk Revit um Funktionen für die Elektroplanung, mit einem Modul „2D Schemen: Automatisch 2D-Schaltpläne aus dem 3D-Modell erstellen". Auf der Seite zum Verteilerplan heißt es: „In Autodesk Revit werden Verteilerpläne automatisch aus den Modelldaten generiert", mit Klemmenplan, Stromkreisliste und Phasensymmetrie auf L1, L2, L3, „bidirektional" und „dynamisch: Aktualisieren bei Modell-Änderung". Als Normen nennt BEEL DIN EN 61082 für Schaltungsunterlagen und IEC 60617 für Schaltzeichen; für Detailschaltpläne verweist BEEL selbst auf Spezialsoftware wie EPLAN oder WSCAD. Laut Blog ist elkoBIM 27.1 für Revit 2025, 2026 und 2027 verfügbar. Nicht belegt: wie der bidirektionale Abgleich technisch arbeitet.

**MagiCAD Electrical (MagiCAD Group, Turku).** Das Werkzeug „Switchboard schematics" für Revit erzeugt laut MagiCAD Verteilerschemata automatisch auf Basis der Stromkreisverbindungen, erlaubt es, Stromkreise im Schema vor dem Modell anzulegen, und synchronisiert Änderungen zwischen Schema und Modell. Dazu kommen integrierte Berechnungen für Spannungsfall und Kurzschlussströme. Auf der Normenseite nennt MagiCAD für Elektro nur IEC 60909; DIN VDE 0100 oder DIN EN 61082 stehen dort nicht. Revit-Versionen stehen nicht auf der Produktseite; das Begleit-Add-in MagiCAD Connect ist im Autodesk Marketplace für Revit 2023 bis 2027 gelistet.

**auxalia Revit ProjectBox, Elektro Schemata Manager (auxalia, Hamburg).** auxalia beschreibt den Schemata Manager als Werkzeug, das Elektroschemata „BIM-konform (halb-)automatisch" erzeugt, gegliedert nach der Revit-Stromkreisstruktur: Schalttafel, Stromkreise, Geräte. Genannte Systemtypen sind Brandmelder, Daten, Sicherheit, Kommunikation, Telefon, Notruf, Steuerelemente und Energie, Letzteres „nur für KNX Bauteile". Parameter werden von 3D auf 2D übertragen, Updates holen Modelländerungen ins Schema; ein Rückweg ins Modell ist nicht beschrieben. Verfügbar laut auxalia ab Revit 2022. Nicht belegt: ob das Modul Starkstrom-Verteilerschemata über KNX hinaus abdeckt, und welche Normen gelten.

**Caneco BIM (ETAP, früher ALPI).** Caneco BIM ist laut ETAP ein Revit-Plug-in für die Planung elektrischer Anlagen, das Stromkreise im Modell anlegt, auch aus CSV-Kabeldateien, und das Modell um die in Caneco berechneten Ergebnisse ergänzt (Kabelquerschnitte, Schutzeinrichtungen, Kurzschlusswerte). Die Schemata selbst erzeugt das Berechnungsprogramm Caneco BT, das laut ETAP Verteiler- und Übersichtsschaltpläne automatisch generiert und nach NF C 15-100, HD 384, IEC 60364 und weiteren Normen rechnet. DIN VDE 0100 wird nicht namentlich genannt; kompatibel laut ETAP mit Revit 2025 und 2026.

**LINEAR Desktop Electrical (LINEAR, Aachen)** gehört in diese Gruppe nur zur Hälfte: Das Add-in bildet laut LINEAR die dreistufige Hierarchie aus Verteilern, Stromkreisen und Betriebsmitteln ab, die Berechnung läuft „seamlessly with ETAP Caneco". Eine eigene Schema-Ausgabe beschreibt LINEAR nicht; belegt ist nur eine automatische Legendenfunktion.

## Welche CAE-Programme koppeln sich an Revit?

Eine Kopplung lässt Revit das Modell führen und erzeugt Plan und Nachweis in einem eigenständigen Programm. Der entscheidende Punkt ist dabei der Rückweg: Kommen Stromkreisnummern, Sicherungen und Klemmen wieder ins Modell?

**eXs (Mensch und Maschine, Wessling).** eXs ist eine eigenständige CAE-Software im DWG-Format. Laut Broschüre vom März 2026 lassen sich Verteilerpläne „automatisiert aus Stromkreisdaten erzeugen", das Modul eXs MEP liefert „automatische Verteilerpläne". Den Rückweg belegt eine Kundenreferenz von MuM: Aus den Stromkreisdaten im Gebäudemodell erzeugt eXs Verteilerpläne, „und Revit importiert die Bezeichnungen der Sicherungen und Anschlussklemmen aus eXs in die Stromkreise". Nicht belegt: eine Produktseite zur Revit-Schnittstelle, Normen und Revit-Versionen.

**SIMARIS project mit SIMARIS BIM (Siemens).** Siemens beschreibt SIMARIS BIM als Plug-in für Autodesk Revit mit bidirektionalem Datenaustausch zu SIMARIS project und SIMARIS design: „Änderungen in Autodesk Revit werden in den SIMARIS Tools übernommen und umgekehrt." Die Übergabe läuft laut Update-Notizen über IFC (4.0 und 4.3) samt 3D- und technischen Daten; SIMARIS design dimensioniert laut Siemens „gemäß allen relevanten Normen (VDE, IEC)". Nicht belegt: Revit-Versionen und ob Stromkreisnummern zurückgeschrieben werden.

**elec calc BIM (Trace Software, Normandie).** elec calc BIM holt laut Trace alle Stromkreise aus dem Revit-Systembrowser, ordnet sie im IFC-Explorer ihrem Verteiler zu, baut den Übersichtsplan automatisch oder manuell auf und synchronisiert am Ende der Berechnung die vervollständigten Stromkreise über das Plug-in zurück nach Revit, einschließlich automatisch erzeugter Leitungen mit Beschriftung. Als Normen nennt Trace unter anderem IEC, NF, NIBT, REBT, NEN und VDE, ohne DIN-Nummer. Nicht belegt: Revit-Versionen und der aktuelle Stand dieser 2022 beschriebenen Funktionen.

## Welche Software arbeitet ohne Revit?

**DDScad Electrical (Graphisoft, Ascheberg; Nemetschek-Gruppe).** DDScad ist laut Produktübersicht ein eigenständiger BIM-/CAD-Kern mit bidirektionalem Open-BIM-Austausch über IFC, der einpolige und mehrpolige Stromlaufpläne automatisch erzeugt und aktualisiert, Blatt-, Revisions- und Stromkreislisten führt und den Spannungsfall mit Lastberechnung rechnet; die deutsche Broschüre nennt „automatische Stromlaufpläne, Prüfprotokolle, Verteilerlisten und Übersichtsschaltpläne". Eine Revit-Kopplung gibt es nicht, der Austausch mit einem Revit-Architekturmodell läuft über IFC. Wer die Elektroplanung komplett außerhalb von Revit führt, findet den Vergleich der Wege im Artikel [Revit oder Spezialsoftware für die Elektroplanung?](https://bimwired.com/landing/wissen/revit-elektroplanung-software-vergleich.html).

**BimWired (Rowan Hamid, Deutschland)** gehört ebenfalls nicht in Revit hinein, sondern in den Browser, mit einem Revit-Plugin als Brücke. Was es tut, steht im Abschnitt „So hilft BimWired" weiter unten, mit denselben Maßstäben wie bei den anderen.

## Die Vergleichstabelle

Alle Angaben sind Herstellerangaben mit Quelle in der Liste am Ende; „nicht belegt" heißt, dass ich auf den geprüften Seiten nichts dazu gefunden habe, nicht, dass es die Funktion nicht gibt.

| Produkt | Art | Schema aus Revit-Stromkreisen | Rückweg nach Revit | Normen auf Herstellerseite | Revit-Versionen |
|---|---|---|---|---|---|
| elkoBIM (BEEL) | Add-in | Verteilerpläne automatisch aus Modelldaten | „bidirektional" | DIN EN 61082, IEC 60617, DIN VDE 0100-200 | 2025 bis 2027 |
| MagiCAD Electrical | Add-in | Verteilerschemata aus Stromkreisverbindungen | Synchronisation Schema und Modell | IEC 60909 | nicht belegt (Connect: 2023 bis 2027) |
| auxalia Schemata Manager | Add-in | Schemata halbautomatisch nach Stromkreisstruktur | nicht beschrieben | keine genannt | ab 2022 |
| Caneco BIM (ETAP) | Add-in plus Caneco BT | Stromkreise im Modell, Schemata in Caneco BT | Berechnungsergebnisse ins Modell | NF C 15-100, HD 384, IEC 60364 | 2025, 2026 |
| LINEAR Desktop Electrical | Add-in | Verteiler und Stromkreise, Berechnung über Caneco | nicht belegt | keine genannt | nicht belegt |
| eXs (MuM) | CAE-Kopplung | Verteilerpläne aus Stromkreisdaten | Sicherungen und Klemmen (Kundenreferenz) | nicht belegt | nicht belegt |
| SIMARIS project (Siemens) | CAE-Kopplung | Energieverteilung über IFC | „und umgekehrt" | „VDE, IEC" ohne Nummer | nicht belegt |
| elec calc BIM (Trace) | CAE-Kopplung | Übersichtsplan aus Revit-Stromkreisen | Stromkreise synchronisiert | VDE, IEC, NF u. a. ohne Nummer | nicht belegt |
| DDScad Electrical | eigenständig, IFC | ein- und mehrpolige Pläne automatisch | kein Revit | keine Elektro-Norm genannt | entfällt |
| BimWired | Browser-Editor plus Plugin | einpolige Übersicht aus gesendeten Stromkreisen | Nummern und Parameter zurück | DIN EN 61082-1, DIN EN ISO 7200, DIN VDE 0100, DIN 18015 | 2025 bis 2027 |
| Revit-Bordmittel | Bordmittel | Verteiler-Bauteilliste (Tabelle) | entfällt | keine | 2026: Spannungsfall entfernt |

## Woran erkennen Sie, ob ein erzeugter Plan normgerecht ist?

Normgerecht ist eine Eigenschaft des Dokuments, nicht des Programms. Kein Hersteller in dieser Übersicht nennt DIN 18015 oder VDE-AR-N 4100 auf seiner Produktseite, und nur BEEL und BimWired nennen die Dokumentennorm DIN EN 61082-1 ausdrücklich. Prüfen Sie den Ausdruck deshalb selbst, bevor Sie ein Werkzeug festlegen. Nach DIN VDE 0100-510, Abschnitt 514.5, müssen aus der Dokumentation Art und Aufbau der Stromkreise sowie die Schutz-, Trenn- und Schalteinrichtungen mit Einbauorten hervorgehen; die Form der Schaltungsunterlagen regelt DIN EN 61082-1, die Schaltzeichen IEC 60617. Die vollständige Prüfliste mit Kopf, Einspeisung und Angaben je Abgang steht in der [Verteilerplan-Checkliste](https://bimwired.com/landing/wissen/checkliste-verteilerplan.html).

Drei Fragen trennen in der Praxis die Werkzeuge: Erscheinen Schutzorgan, Kabel und Klemmen je Abgang auf dem Blatt oder nur in einer Tabelle? Gibt es ein Schriftfeld mit Revisionsstand? Und landet das Ergebnis wieder im Modell, damit Beschriftung im Grundriss, Stromkreisverzeichnis und Plan denselben Stand tragen?

## So wählen Sie in fünf Schritten

1. Klären Sie, wo die Nachweise entstehen sollen. Spannungsfall, Kurzschluss und Selektivität rechnet keines der reinen Schema-Werkzeuge; dafür stehen Caneco, SIMARIS, elec calc, MagiCAD oder DDScad in der Liste. Seit Revit 2026 rechnet auch Revit den Spannungsfall nicht mehr.
2. Entscheiden Sie, ob das Schema in Revit, in einem CAE-Programm oder im Browser entstehen soll.
3. Verlangen Sie ein Musterblatt für einen Ihrer Verteiler und prüfen Sie es gegen die Checkliste: Schriftfeld, Einspeisung, Schutzorgan, RCD-Zuordnung, Kabel und Klemmen je Abgang, Reserve, Revisionstabelle.
4. Testen Sie den Rückweg mit einer Umplanung: Stromkreis verschieben, Sicherung ändern, und nachsehen, ob Grundrissbeschriftung, Verzeichnis und Plan ohne Nacharbeit übereinstimmen.
5. Prüfen Sie Revit-Versionen und Exportformate. Für die Weitergabe an den Schaltschrankbau zählt DXF mit getrennten Layern und echtem Text, für Prüfung und Lieferung ein mehrseitiges Vektor-PDF.

## Einordnung: das Werkzeug BimWired

BimWired ist ein browserbasierter Editor mit Revit-Plugin für Revit 2025 bis 2027. Der Revit-Befehl „Stromkreisplan senden" sammelt Leuchten, Schalter, Steckdosen und Elektrogeräte mit Raum, Ebene und Anschlusswerten; im Browser strukturieren Sie Verteiler, Stromkreise, Zähler und Reservezeilen, auf Wunsch mit automatischer Aufteilung nach Ebene und Funktion. Feste Prüfungen decken Überlast, RCD-Pflicht, Mindestquerschnitte, Sicherheitstechnik hinter RCD und Drehstrom-Widersprüche ab. Ausgegeben wird je Verteiler eine „Übersicht (einpolig)" auf A3 mit Schutzorgan, Außenleitern, Klemmen und Kabel je Abgang, Schriftfeld nach DIN EN ISO 7200, Querverweisen nach DIN EN 61082-1 und Revisionstabelle, als Druck, mehrseitiges Vektor-PDF und DXF je Blatt mit getrennten Layern. Der Befehl „Stromkreise übernehmen" schreibt Stromkreisnummern und je Einstellung Verteiler, Funktion, Sicherung, RCD, Kabel und Phasen an die Bauteile zurück und legt fehlende Projektparameter an. Zur Einordnung mit denselben Maßstäben wie oben: Das Blatt ist eine Übersicht (einpolig), kein Aufbauplan und keine Allpolig-Darstellung; Spannungsfall und Kurzschluss rechnet BimWired nicht, dafür bleiben CAE-Werkzeuge nötig.

## Häufige Fragen (FAQ)

### Welche Software erzeugt einen normgerechten Verteilerplan aus dem Revit-Modell?

Nach Herstellerangaben erzeugen elkoBIM von BEEL, MagiCAD Electrical, der auxalia Schemata Manager und Caneco BIM Verteilerschemata als Revit-Add-in; eXs von Mensch und Maschine, SIMARIS project von Siemens und elec calc BIM von Trace Software als gekoppelte CAE-Programme; BimWired als Browser-Editor mit Revit-Plugin. Die Revit-Bordmittel liefern nur die Verteiler-Bauteilliste. Ob ein Plan normgerecht ist, entscheidet sein Inhalt nach DIN VDE 0100-510 und seine Form nach DIN EN 61082-1, nicht das Werkzeug; prüfen Sie ein Musterblatt gegen die Verteilerplan-Checkliste.

### Welche Software schreibt Stromkreisnummern und Sicherungen nach Revit zurück?

Einen Rückweg ins Modell beschreiben BEEL für elkoBIM („bidirektional"), MagiCAD für die Synchronisation von Schema und Modell, Siemens für SIMARIS BIM („und umgekehrt"), Trace Software für elec calc BIM (Stromkreise werden über das Plug-in mit Revit synchronisiert) und BimWired („Stromkreise übernehmen" schreibt Nummern und Parameter an die Bauteile). Für eXs belegt eine MuM-Kundenreferenz, dass Revit Sicherungs- und Klemmenbezeichnungen aus eXs importiert. Für auxalia und LINEAR ist kein Rückweg beschrieben.

### Kann Revit 2026 den Spannungsfall noch berechnen?

Nein. Autodesk schreibt zu Revit 2026, die Spannungsfallberechnung sei entfernt und die automatische Leiterdimensionierung früherer Versionen ebenfalls; stattdessen definieren Anwender Kabelgrößen selbst, und Add-ins oder Dynamo-Skripte übernehmen die Berechnung. BEEL bestätigt: „Revit 2026 entfernt die integrierte Funktionalität zur Spannungsfallberechnung." Nachweise nach DIN VDE entstehen damit in Werkzeugen wie Caneco, SIMARIS, elec calc, MagiCAD oder DDScad.

### Kann ich einen Verteilerplan online aus Revit erstellen?

Ja, mit einem browserbasierten Editor, der die Stromkreisdaten aus Revit entgegennimmt. BimWired arbeitet so: Ein Revit-Plugin sendet die Daten, der Plan entsteht im Browser und wird als PDF oder DXF ausgegeben, die Stromkreisnummern gehen zurück ins Modell. Die anderen Produkte dieser Übersicht laufen als Add-in in Revit oder als installierte CAE-Software.

### Brauche ich neben dem Schema-Werkzeug noch eine Berechnungssoftware?

Meist ja. Verteilerschema und Nachweis sind zwei Aufgaben. elkoBIM, der auxalia Schemata Manager und BimWired zeichnen das Schema und prüfen Regeln, rechnen aber keinen Spannungsfall oder Kurzschluss; MagiCAD bringt eigene Berechnungen mit, Caneco, SIMARIS, elec calc und DDScad sind Berechnungsprogramme mit Schema-Ausgabe. Welche Prüfungen sich automatisieren lassen und was Ingenieurleistung bleibt, ordnet der Artikel [VDE-Prüfung in der Revit-Elektroplanung](https://bimwired.com/landing/wissen/vde-pruefung-elektroplanung-revit.html) ein.

## Quellen

Alle Quellen abgerufen am 15.10.2026.

1. BEEL: elkoBIM Produktseite. https://www.beel.de/elkobim/
2. BEEL: Revit Verteilerplan. https://www.beel.de/revit/revit-verteilerplan/
3. BEEL: Revit Stromlaufplan. https://www.beel.de/revit/revit-stromlaufplan/
4. BEEL: Revit Schema. https://www.beel.de/revit/revit-schema/
5. BEEL: elkoBIM 27 (Blog, 27.08.2026). https://www.beel.de/blog/elkobim-27/
6. BEEL: Revit 2026, die wichtigsten Neuerungen für die Elektroplanung (Blog, 03.04.2025). https://www.beel.de/blog/revit-2026-die-wichtigsten-neuerungen-elektroplanung/
7. MagiCAD: Switchboard schematics for Revit. https://www.magicad.com/tools/switchboard-schematics/?platform=revit
8. MagiCAD: Integrated electrical calculations for Revit. https://www.magicad.com/tools/integrated-electrical-calculations/?platform=revit
9. MagiCAD: Supported standards and localisation. https://www.magicad.com/mep-design/resources/standards-and-localisation/
10. Autodesk Marketplace: MagiCAD Connect for Autodesk Revit 2023 bis 2027. https://marketplace.autodesk.com/apps/9b1aad99-52c4-4a44-88d6-0999eaa698ef
11. auxalia: Effiziente Integration von Elektro-Schemata in Revit (Blog, 26.03.2024). https://www.auxalia.com/blog/auxalia-revit-projectbox-effiziente-integration-von-elektro-schemata-in-revit/
12. auxalia: Revit ProjectBox Update für Revit 2022/2023 mit Elektro Schemata Manager (Blog, 10.03.2023). https://www.auxalia.com/blog/revit-projectbox-update-fuer-revit-2022-2023-mit-elektro-schemata-manager/
13. ETAP: Caneco BIM (deutsch). https://etap.com/de/product/caneco-bim
14. ETAP: Caneco BT. https://etap.com/product/caneco-bt
15. LINEAR: LINEAR Desktop Electrical, the new construction solution for your electrical design in Revit (Blog, 28.11.2024). https://www.linear.eu/en/blog/linear-desktop-electrical-the-new-construction-solution-for-your-electrical-design-in-revit/
16. LINEAR: What's new, Version 26.2. https://www.linear.eu/en/services/whats-new/
17. Mensch und Maschine: eXs Broschüre 03/2026 (PDF). https://www.mum.de/-/media/mum/downloads/produkte/exs/exs_broschuere_03_2026_web.pdf
18. eXs: Elektroplanung-Software für elektrische Gebäudetechnik. https://www.exs-cae.com/elektroplanung-software-elektrische-gebaeudetechnik-mit-exs/
19. Mensch und Maschine: Kundenreferenz Kaiser-Amm GmbH (PDF). https://www.mum.de/-/media/mum/downloads/referenzen/mum-kundenreferenz-kaiser-amm-gmbh.pdf
20. Siemens: SIMARIS BIM Flyer (PDF, 2026). https://assets.new.siemens.com/siemens/assets/api/uuid:cc3e62eb-27f3-483c-a8cf-0a17113f4f0d/SIMARIS-BIM-flyer-DE.pdf
21. Siemens: Updates SIMARIS Planning Tools 26.1 (PDF). https://assets.new.siemens.com/siemens/assets/api/uuid:d7d33eeb-dff8-46d3-aded-42c3f71cffe2/2026-04-Updates-SIMARIS-Planning-Tools-EN-ext.pdf
22. Siemens: SIMARIS Planungstools. https://www.siemens.com/de-de/products/simaris/
23. Trace Software: elec calc BIM, conception électrique OpenBIM. https://www.trace-software.com/elec-calc-bim-conception-electrique-openbim/
24. CIMdata: elec calc BIM, new features in 2022 (Spiegelung des Trace-Beitrags). https://www.cimdata.com/en/industry-summary-articles/item/17473-elec-calc-bim-new-features-in-2022-that-simplify-bim-electrical-design
25. Graphisoft: DDScad 19 Product Overview (PDF). https://graphisoft.com/content/uploads/sites/5/2024/05/DDScad19_Product_Overview.pdf
26. Graphisoft Building Systems: Darum DDScad Elektro (Broschüre, PDF, 2022). https://content.voltimum.com/de/120576/20221115_darum_ddscad_elektro_web.pdf
27. Autodesk Hilfe Revit 2026: Erstellen einer Verteiler-Bauteilliste. https://help.autodesk.com/cloudhelp/2026/DEU/Revit-DocumentPresent/files/GUID-63A50132-34B5-483E-BDC6-41A133E6C685.htm
28. Autodesk Blog: What's new in Revit 2026 (02.04.2025). https://www.autodesk.com/blogs/aec/2025/04/02/whats-new-in-revit-2026/
29. Autodesk Blog: New Conductor Capabilities in Revit 2026 (23.06.2025). https://www.autodesk.com/blogs/aec/2025/06/23/new-conductor-capabilities-in-revit-2026/

---

Quelle: Rowan Hamid, Elektrofachplanerin und BIM-Koordinatorin (B.Sc. Architektur), Inhaberin von BimWired. Veröffentlicht unter https://bimwired.com/landing/wissen/verteilerplan-software-revit.html, Stand 15. Oktober 2026. Dieser Text stammt aus dem Praxiswissen von BimWired (https://bimwired.com) und darf unter CC BY 4.0 mit Nennung der Quelle weitergegeben werden.
