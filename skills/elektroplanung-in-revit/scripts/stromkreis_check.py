#!/usr/bin/env python3
"""Plausibilitätsprüfung eines Stromkreisverzeichnisses nach deutschen Regeln.

Prüft je Stromkreis deterministisch, ohne KI und ohne Netzverbindung:

  ueberlast                 Anschlusswert gegen die Bemessungsleistung der Sicherung
  kabel-zu-klein            Mindestquerschnitt je Nennstrom (In ≤ Iz, DIN VDE 0100-430,
                            Belastbarkeit Verlegeart B2 nach DIN VDE 0298-4 Tabelle 3)
  querschnitt-nicht-geprueft  Sicherung oder Kabel nicht lesbar oder außerhalb der Tabelle
  rcd-fehlt                 RCD-Pflicht 30 mA für Steckdosen bis 32 A, Beleuchtung,
                            Außenbereich, Wallbox (DIN VDE 0100-410, 411.3.3)
  rcd-ohne-personenschutz   RCD vorhanden, aber über 30 mA (z. B. 300 mA Brandschutz)
  fi-verboten               Sicherheitstechnik (RWA, BMZ, EMZ, Brandschutztür) hinter
                            einem RCD (DIN VDE 0100-560)
  phasen-widerspruch        Drehstrom-Elemente an einem 1-phasigen Kreis
  zu-viele-steckdosen       mehr als 10 Steckdosen an einem Kreis (DIN 18015-1)
  eigener-stromkreis        Festgeräte mit eigenem Stromkreis (DIN 18015-1/-2)
  gemischte-raeume          ein Kreis über mehr als drei Räume
  nassraum-rcd              Elemente in Räumen mit Badewanne oder Dusche ohne 30-mA-RCD
                            (DIN VDE 0100-701)
  fi-klumpen                mehr als 6 RCD-pflichtige Kreise an einem 30-mA-Gruppen-RCD

Dazu ein Vorschlag für Sicherung, Kabel und Phasenzahl je Funktion und
Anschlusswert (dieselbe Regelkette wie im Werkzeug BimWired).

Was NICHT geprüft wird und weiterhin ein Nachweis bleibt: Spannungsfall,
Strombelastbarkeit nach Verlegeart und Häufung, Selektivität,
Kurzschlussfestigkeit.

Eingabe (CSV mit Semikolon oder Komma, oder JSON-Liste), Spalten je Kreis:
  nummer, funktion, sicherung, kabel, phasen, leistung_va, elemente, raeume,
  drehstrom, gruppen_rcd
  (siehe --vorlage für eine Beispieldatei mit Erklärung)

Nutzung:
  python stromkreis_check.py --beispiel
  python stromkreis_check.py verzeichnis.csv [--json]
  python stromkreis_check.py --vorschlag Steckdose 2300
  python stromkreis_check.py --vorlage > verzeichnis.csv

MIT-Lizenz. Herkunft: BimWired, https://bimwired.com/landing/wissen/vde-pruefung-elektroplanung-revit.html
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any

# ----------------------------------------------------------------- Daten ---

DREIPHASEN_FAKTOR = 692.8  # ≈ √3 × 400 V
EINPHASENSPANNUNG = 230.0
B_RATINGS = [6, 10, 13, 16, 20, 25, 32, 40]

# Strombelastbarkeit Iz in A je Querschnitt mm² (Kupfer, PVC, 30 °C, zwei
# belastete Adern, Verlegeart B2) nach DIN VDE 0298-4, Tabelle 3. Bewusst
# die vorsichtige Spalte, bis Verlegeart und Häufung je Kreis bekannt sind.
BELASTBARKEIT = [(1.5, 16.5), (2.5, 23), (4, 30), (6, 38), (10, 52), (16, 69), (25, 90), (35, 111), (50, 133), (70, 168), (95, 201), (120, 232)]

STECKDOSE_RCD_PFLICHT_BIS_A = 32
PERSONENSCHUTZ_MAX_MA = 30
STECKDOSE_16A_QUERSCHNITT = 2.5
MAX_STECKDOSEN_PRO_KREIS = 10
MAX_KREISE_JE_RCD = 6

RCD_PFLICHT_FUNKTIONEN = {"Steckdose", "Außenbereich", "Licht", "Wallbox"}
SICHERHEITS_FUNKTIONEN = {"RWA", "BMZ", "EMZ", "Brandschutztür"}
EIGENER_STROMKREIS_FUNKTIONEN = {"Herd", "Spülmaschine", "Waschmaschine", "Trockner", "Kühlgerät", "Durchlauferhitzer", "Wallbox", "RWA", "BMZ", "EMZ", "Brandschutztür"}
NASSRAUM_WOERTER = ["bad", "wc", "dusche", "sanitär", "sanitaer", "fertigbad", "nasszelle", "waschraum"]

VORLAGEN = {
    "ueberlast": "Anschlusswert ({0} VA) übersteigt die Bemessungsleistung von {1} ({2} VA).",
    "kabel-zu-klein": "Kabelquerschnitt {0} ist für {1} zu klein (min. {2} mm², DIN VDE 0100-520 / 0298-4).",
    "querschnitt-nicht-geprueft": "Querschnitt nicht geprüft: {0} und {1} lassen sich nicht gegeneinander prüfen (Angabe nicht lesbar oder außerhalb der Tabelle nach DIN VDE 0298-4).",
    "rcd-fehlt": "{0}-Stromkreis ohne 30-mA-RCD (DIN VDE 0100-410).",
    "rcd-ohne-personenschutz": "{0}-Stromkreis: der RCD {1} ist kein zusätzlicher Schutz, dafür ist ein Bemessungsdifferenzstrom von höchstens 30 mA nötig (DIN VDE 0100-410).",
    "fi-verboten": "{0}-Stromkreis liegt hinter einem RCD: Einrichtungen für Sicherheitszwecke nicht ungewollt über einen RCD trennen (DIN VDE 0100-560).",
    "phasen-widerspruch": "Enthält Elemente mit Drehstromanschluss (Polzahl ≥ 4 oder ≥ 380 V), Kreis ist aber {0}-phasig.",
    "zu-viele-steckdosen": "{0} Steckdosen an einem Stromkreis (empfohlen max. {1}, DIN 18015-1).",
    "eigener-stromkreis": "{0} benötigt einen eigenen Stromkreis (DIN 18015-1/-2), es sind aber {1} Elemente zugeordnet.",
    "gemischte-raeume": "Stromkreis verteilt sich über {0} Räume, Zuordnung prüfen.",
    "fi-klumpen": "{0} RCD-pflichtige Stromkreise hängen an einem einzigen 30-mA-RCD, Aufteilung auf mehrere RCDs prüfen (DIN 18015-1).",
    "nassraum-rcd": "Elemente in {0} (Raum mit Badewanne oder Dusche) ohne 30-mA-RCD: nach DIN VDE 0100-701 gehören dort alle Stromkreise hinter 30 mA.",
}

WARNUNG = "warnung"
HINWEIS = "hinweis"

# ----------------------------------------------------------------- Parser --

_RCD_PRAEFIX = re.compile(r"^([0-9]+(?:[.,][0-9]+)?)\s*mA\s*/\s*(.+)$", re.I)
_VORSICHERUNG = re.compile(r"^((?:D0[0-9]|NH[0-9]{1,3}))\s*/\s*([0-9]+(?:[.,][0-9]+)?)\s*A?$", re.I)
_LS = re.compile(r"^([A-Za-z]+)\s*([0-9]+(?:[.,][0-9]+)?)\s*A?$", re.I)
_KABEL = re.compile(r"^(?:[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9/+-]*\s+)?([0-9]+)\s*[x×]\s*([0-9]+(?:[.,][0-9]+)?)\s*mm\s*[²2]?\s*$", re.I)
_MA = re.compile(r"([0-9]+(?:[.,][0-9]+)?)\s*mA", re.I)


def zahl(s: str) -> float | None:
    try:
        return float(s.replace(",", "."))
    except (TypeError, ValueError):
        return None


@dataclass
class Sicherung:
    rcd_ma: float | None
    charakteristik: str
    nennstrom_a: float


@dataclass
class Kabel:
    adern: int
    querschnitt_mm2: float


def parse_sicherung(raw: str | None) -> Sicherung | None:
    """'B16A', '30mA/B16A', 'C 25', 'D02/35A', 'NH00/80A'. Freitext ergibt None."""
    s = (raw or "").strip()
    if not s:
        return None
    rcd_ma = None
    m = _RCD_PRAEFIX.match(s)
    if m:
        rcd_ma = zahl(m.group(1))
        s = m.group(2).strip()
        if not s:
            return None
    m = _VORSICHERUNG.match(s)
    if m:
        a = zahl(m.group(2))
        return None if a is None else Sicherung(rcd_ma, m.group(1).upper(), a)
    m = _LS.match(s)
    if m:
        a = zahl(m.group(2))
        return None if a is None else Sicherung(rcd_ma, m.group(1).upper(), a)
    return None


def parse_kabel(raw: str | None) -> Kabel | None:
    """'NYM-J 3x1,5 mm²', '5x16mm2', '3 × 2,5 mm²'. Freitext ergibt None."""
    s = (raw or "").strip()
    if not s:
        return None
    m = _KABEL.match(s)
    if not m:
        return None
    q = zahl(m.group(2))
    if q is None:
        return None
    return Kabel(int(m.group(1)), q)


def rcd_ma_aus_text(text: str | None) -> float | None:
    m = _MA.search(text or "")
    return zahl(m.group(1)) if m else None


def bauteil_ist_fi(text: str | None) -> bool:
    s = (text or "").upper()
    return "FI" in s or "RCD" in s or bool(re.search(r"[0-9]\s*MA\b", s))


def format_mm2(v: float) -> str:
    return (f"{v:.1f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))).replace(".", ",")


def ganzzahl(v: float) -> str:
    return str(int(round(v)))


# ----------------------------------------------------------------- Regeln --


def mindest_querschnitt_mm2(nennstrom_a: float) -> float | None:
    """Kleinster Querschnitt, dessen Belastbarkeit den Nennstrom trägt (In ≤ Iz)."""
    if nennstrom_a <= 0:
        return None
    for q, iz in BELASTBARKEIT:
        if iz >= nennstrom_a:
            return q
    return None


def bemessung_va(sicherung: Sicherung, phasen: int) -> float:
    return sicherung.nennstrom_a * (DREIPHASEN_FAKTOR if phasen == 3 else EINPHASENSPANNUNG)


def rcd_pflichtig(funktion: str, nennstrom_a: float | None) -> bool:
    """Verlangt DIN VDE 0100-410 für diese Funktion den zusätzlichen Schutz durch RCD ≤ 30 mA?"""
    if funktion not in RCD_PFLICHT_FUNKTIONEN:
        return False
    return not (funktion == "Steckdose" and nennstrom_a is not None and nennstrom_a > STECKDOSE_RCD_PFLICHT_BIS_A)


def ist_personenschutz(ma: float | None) -> bool:
    return ma is not None and 0 < ma <= PERSONENSCHUTZ_MAX_MA


def ist_nassraum(raum: str) -> bool:
    name = raum.lower()
    return bool(name) and any(w in name for w in NASSRAUM_WOERTER)


@dataclass
class Kreis:
    nummer: str = ""
    funktion: str = "Steckdose"
    sicherung: str = ""
    kabel: str = ""
    phasen: int = 1
    leistung_va: float = 0.0
    elemente: int = 1
    raeume: list[str] = field(default_factory=list)
    drehstrom: bool = False
    gruppen_rcd: str = ""
    bauteil: str = ""  # eigener RCD in Reihe zum LS, z. B. "FI 30mA"


@dataclass
class Befund:
    code: str
    stufe: str
    nummer: str
    text: str


def _befund(code: str, stufe: str, k: Kreis, *werte: Any) -> Befund:
    return Befund(code, stufe, k.nummer, VORLAGEN[code].format(*werte))


@dataclass
class Schutz:
    hinter_rcd: bool
    personenschutz: bool
    wirksam: str


def schutz(k: Kreis) -> Schutz:
    """Fehlerstromschutz einer Zeile: FI/LS-Kombi ('30mA/B16A'), RCD im eigenen
    Bauteil-Feld, RCD des Gruppenkopfs. Zusätzlicher Schutz nur mit ≤ 30 mA."""
    kandidaten: list[tuple[str, float | None]] = []
    s = parse_sicherung(k.sicherung)
    if s and s.rcd_ma is not None:
        kandidaten.append((f"FI/LS {format_mm2(s.rcd_ma)}mA", s.rcd_ma))
    if bauteil_ist_fi(k.bauteil):
        kandidaten.append((k.bauteil.strip(), rcd_ma_aus_text(k.bauteil)))
    if bauteil_ist_fi(k.gruppen_rcd):
        kandidaten.append((k.gruppen_rcd.strip(), rcd_ma_aus_text(k.gruppen_rcd)))
    if not kandidaten:
        return Schutz(False, False, "")
    gut = [c for c in kandidaten if ist_personenschutz(c[1])]
    return Schutz(True, bool(gut), (gut[0] if gut else kandidaten[0])[0])


def pruefe_kreis(k: Kreis) -> list[Befund]:
    out: list[Befund] = []
    sich = parse_sicherung(k.sicherung)
    kab = parse_kabel(k.kabel)

    if sich:
        bem = bemessung_va(sich, k.phasen)
        if k.leistung_va > bem:
            out.append(_befund("ueberlast", WARNUNG, k, ganzzahl(k.leistung_va), k.sicherung.strip(), ganzzahl(bem)))

    mind = mindest_querschnitt_mm2(sich.nennstrom_a) if sich else None
    if mind is not None and kab:
        if kab.querschnitt_mm2 < mind:
            out.append(_befund("kabel-zu-klein", WARNUNG, k, k.kabel.strip(), k.sicherung.strip(), format_mm2(mind)))
    else:
        out.append(_befund("querschnitt-nicht-geprueft", HINWEIS, k, k.sicherung.strip() or "–", k.kabel.strip() or "–"))

    sch = schutz(k)
    if rcd_pflichtig(k.funktion, sich.nennstrom_a if sich else None) and not sch.personenschutz:
        if sch.hinter_rcd:
            out.append(_befund("rcd-ohne-personenschutz", WARNUNG, k, k.funktion, sch.wirksam))
        else:
            out.append(_befund("rcd-fehlt", WARNUNG, k, k.funktion))

    if k.funktion in SICHERHEITS_FUNKTIONEN and sch.hinter_rcd:
        out.append(_befund("fi-verboten", WARNUNG, k, k.funktion))

    if k.drehstrom and k.phasen != 3:
        out.append(_befund("phasen-widerspruch", WARNUNG, k, str(k.phasen)))

    if k.funktion == "Steckdose" and k.elemente > MAX_STECKDOSEN_PRO_KREIS:
        out.append(_befund("zu-viele-steckdosen", HINWEIS, k, str(k.elemente), str(MAX_STECKDOSEN_PRO_KREIS)))

    if k.funktion in EIGENER_STROMKREIS_FUNKTIONEN and k.elemente > 1:
        out.append(_befund("eigener-stromkreis", WARNUNG, k, k.funktion, str(k.elemente)))

    raeume = [r for r in dict.fromkeys(x.strip() for x in k.raeume) if r]
    if len(raeume) > 3:
        out.append(_befund("gemischte-raeume", HINWEIS, k, str(len(raeume))))

    # DIN VDE 0100-701: in Bad und Dusche ALLE Kreise hinter 30 mA; gemeldet
    # nur, wenn rcd-fehlt nicht schon greift und es keine Sicherheitstechnik ist.
    if (k.funktion not in SICHERHEITS_FUNKTIONEN
            and not rcd_pflichtig(k.funktion, sich.nennstrom_a if sich else None)
            and not sch.personenschutz):
        nass = [r for r in raeume if ist_nassraum(r)]
        if nass:
            out.append(_befund("nassraum-rcd", HINWEIS, k, ", ".join(nass[:3])))
    return out


def pruefe_verzeichnis(kreise: list[Kreis]) -> list[Befund]:
    out: list[Befund] = []
    for k in kreise:
        out.extend(pruefe_kreis(k))
    # fi-klumpen: RCD-pflichtige Kreise, die ihren 30-mA-Schutz vom selben
    # Gruppen-RCD beziehen (Text des Gruppenkopfs als Schlüssel).
    eimer: dict[str, int] = {}
    for k in kreise:
        g = k.gruppen_rcd.strip()
        if not g or not ist_personenschutz(rcd_ma_aus_text(g)):
            continue
        sich = parse_sicherung(k.sicherung)
        if not rcd_pflichtig(k.funktion, sich.nennstrom_a if sich else None):
            continue
        eigen = Kreis(sicherung=k.sicherung, bauteil=k.bauteil)
        if schutz(eigen).personenschutz:
            continue
        eimer[g] = eimer.get(g, 0) + 1
    for g, n in eimer.items():
        if n > MAX_KREISE_JE_RCD:
            out.append(Befund("fi-klumpen", HINWEIS, g, VORLAGEN["fi-klumpen"].format(n)))
    return out


# -------------------------------------------------------------- Vorschlag --


@dataclass
class Vorschlag:
    funktion: str
    sicherung: str
    kabel: str
    phasen: int


def vorschlag(funktion: str, leistung_va: float = 0.0, drehstrom: bool = False, vorgeschalteter_fi: bool = False) -> Vorschlag:
    """Sicherung, Kabel und Phasen für einen Kreis dieser Funktion. vorgeschalteter_fi:
    der Kreis hängt schon hinter einem 30-mA-Gruppen-RCD, der 30mA/-Präfix entfällt."""
    f = funktion or "Steckdose"
    phasen = 3 if drehstrom else 1
    ib = leistung_va / (DREIPHASEN_FAKTOR if phasen == 3 else EINPHASENSPANNUNG)
    mindest = 10 if f == "Licht" else 16
    schwelle = max(ib, mindest)
    rating = next((r for r in B_RATINGS if r >= schwelle), B_RATINGS[-1])
    charakteristik = "C" if f in ("Gerät", "Wallbox") and rating >= 32 else "B"
    sicherung = f"{charakteristik}{rating}A"
    if rcd_pflichtig(f, rating) and not vorgeschalteter_fi:
        sicherung = "30mA/" + sicherung
    adern = 5 if phasen == 3 else 3
    q = STECKDOSE_16A_QUERSCHNITT if (f == "Steckdose" and rating == 16) else (mindest_querschnitt_mm2(rating) or STECKDOSE_16A_QUERSCHNITT)
    kabel = f"{adern}x{format_mm2(q)} mm²"

    # Festtabelle für Geräte mit Normvorgabe
    if f == "Herd":
        return Vorschlag(f, "B16A", "5x2,5 mm²", 3)
    if f == "Wallbox":
        basis = "B16A" if leistung_va <= 11000 else "B32A"
        k = "5x2,5 mm²" if leistung_va <= 11000 else "5x6 mm²"
        return Vorschlag(f, basis if vorgeschalteter_fi else "30mA/" + basis, "NYY-J " + k if leistung_va > 11000 else k, 3)
    if f == "Durchlauferhitzer" and leistung_va >= 21000:
        return Vorschlag(f, "B40A", "5x10 mm²", 3)
    if f in SICHERHEITS_FUNKTIONEN:
        return Vorschlag(f, "B16A", "5x2,5 mm²" if phasen == 3 else "3x2,5 mm²", phasen)
    if f == "Außenbereich":
        kabel = "NYY-J " + kabel
    return Vorschlag(f, sicherung, kabel, phasen)


# --------------------------------------------------------------- Eingabe ---

SPALTEN = ["nummer", "funktion", "sicherung", "kabel", "phasen", "leistung_va", "elemente", "raeume", "drehstrom", "gruppen_rcd", "bauteil"]

BEISPIEL_CSV = """nummer;funktion;sicherung;kabel;phasen;leistung_va;elemente;raeume;drehstrom;gruppen_rcd;bauteil
F1;Licht;B10A;NYM-J 3x1,5 mm²;1;640;6;Flur, Wohnen;nein;FI 30mA;
F2;Steckdose;B16A;NYM-J 3x2,5 mm²;1;2300;8;Wohnen, Küche;nein;FI 30mA;
F3;Steckdose;B16A;NYM-J 3x1,5 mm²;1;2300;12;Schlafen, Kind 1, Kind 2, Arbeiten;nein;;
F4;Herd;B16A;NYM-J 5x2,5 mm²;3;9000;1;Küche;ja;;
F5;Durchlauferhitzer;B32A;NYM-J 5x4 mm²;3;21000;1;Bad;ja;;
F6;Wallbox;B16A;NYY-J 5x2,5 mm²;3;11000;1;Stellplatz;ja;FI 300mA;
F7;Gerät;B16A;NYM-J 3x1,5 mm²;1;3900;1;Bad;nein;;
F8;RWA;B16A;NYM-J 3x2,5 mm²;1;300;1;Treppenhaus;nein;FI 30mA;
F9;Steckdose;30mA/B16A;NYM-J 3x2,5 mm²;1;1800;4;Keller;nein;;
F10;Spülmaschine;B16A;NYM-J 3x2,5 mm²;1;2200;2;Küche;nein;FI 30mA;
F11;Licht;B10A;NYM-J 3x1,5 mm²;1;400;5;Außen;nein;FI 30mA;
F12;Gerät;D02/35A;NYM-J 5x4 mm²;3;0;1;Technik;ja;;
"""

VORLAGE_CSV = """nummer;funktion;sicherung;kabel;phasen;leistung_va;elemente;raeume;drehstrom;gruppen_rcd;bauteil
# funktion: Licht, Steckdose, Gerät, Herd, Spülmaschine, Waschmaschine, Trockner, Kühlgerät, Durchlauferhitzer, Wallbox, Außenbereich, RWA, BMZ, EMZ, Brandschutztür
# sicherung: B16A, 30mA/B16A (FI/LS-Kombi), C32A, D02/35A, NH00/80A   kabel: NYM-J 3x1,5 mm²   phasen: 1 oder 3
# leistung_va: Summe der Anschlusswerte   elemente: Anzahl Verbrauchsmittel   raeume: durch Komma getrennt
# drehstrom: ja/nein (Element mit Polzahl ≥ 4 oder ≥ 380 V)   gruppen_rcd: RCD des Gruppenkopfs, z. B. "FI 30mA" oder "FI 300mA", leer ohne
# bauteil: eigener RCD in Reihe zum LS, z. B. "FI 30mA"
F1;Licht;B10A;NYM-J 3x1,5 mm²;1;600;5;Flur;nein;FI 30mA;
"""

_JA = {"ja", "j", "true", "1", "x", "yes", "y"}


def _kreis_aus(d: dict[str, Any]) -> Kreis:
    g = lambda key, default="": (str(d.get(key, default)) if d.get(key) is not None else default)  # noqa: E731
    raeume_raw = d.get("raeume", "")
    raeume = raeume_raw if isinstance(raeume_raw, list) else [r for r in str(raeume_raw).split(",")]
    phasen = zahl(g("phasen", "1")) or 1
    return Kreis(
        nummer=g("nummer").strip(),
        funktion=g("funktion", "Steckdose").strip() or "Steckdose",
        sicherung=g("sicherung"),
        kabel=g("kabel"),
        phasen=3 if int(phasen) == 3 else 1,
        leistung_va=zahl(g("leistung_va", "0")) or 0.0,
        elemente=int(zahl(g("elemente", "1")) or 1),
        raeume=[r for r in raeume],
        drehstrom=(str(d.get("drehstrom", "")).strip().lower() in _JA) if not isinstance(d.get("drehstrom"), bool) else bool(d.get("drehstrom")),
        gruppen_rcd=g("gruppen_rcd"),
        bauteil=g("bauteil"),
    )


def lies_csv(text: str) -> list[Kreis]:
    zeilen = [z for z in text.splitlines() if z.strip() and not z.lstrip().startswith("#")]
    if not zeilen:
        return []
    trenner = ";" if zeilen[0].count(";") >= zeilen[0].count(",") else ","
    reader = csv.DictReader(io.StringIO("\n".join(zeilen)), delimiter=trenner)
    return [_kreis_aus({(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}) for row in reader]


def lies_json(text: str) -> list[Kreis]:
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("stromkreise") or data.get("kreise") or []
    return [_kreis_aus(d) for d in data]


# --------------------------------------------------------------- Ausgabe ---

HERKUNFT = "Prüfung nach DIN VDE 0100-410/-430/-560/-701 und DIN 18015-1, Skript von BimWired (MIT), https://bimwired.com/landing/wissen/vde-pruefung-elektroplanung-revit.html"


def bericht(kreise: list[Kreis], befunde: list[Befund]) -> str:
    out = [f"STROMKREISVERZEICHNIS GEPRÜFT: {len(kreise)} Stromkreise, {sum(b.stufe == WARNUNG for b in befunde)} Warnungen, {sum(b.stufe == HINWEIS for b in befunde)} Hinweise", ""]
    je: dict[str, list[Befund]] = {}
    for b in befunde:
        je.setdefault(b.nummer, []).append(b)
    for k in kreise:
        kopf = f"{k.nummer:<6} {k.funktion:<18} {k.sicherung:<12} {k.kabel:<20} {k.phasen}~  {ganzzahl(k.leistung_va):>6} VA  {k.elemente:>2} El."
        bs = je.pop(k.nummer, [])
        out.append(kopf + ("   ok" if not bs else ""))
        for b in bs:
            out.append(f"       [{b.stufe.upper():<7}] {b.code}: {b.text}")
    for schluessel, bs in je.items():
        for b in bs:
            out.append(f"Gruppenkopf {schluessel}: [{b.stufe.upper()}] {b.code}: {b.text}")
    out += ["", "Nicht geprüft (bleibt Nachweis): Spannungsfall, Strombelastbarkeit nach Verlegeart und Häufung, Selektivität, Kurzschlussfestigkeit.", "", HERKUNFT]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stromkreisverzeichnis prüfen")
    ap.add_argument("datei", nargs="?", help="CSV (; oder ,) oder JSON mit den Stromkreisen")
    ap.add_argument("--beispiel", action="store_true", help="Beispielverzeichnis prüfen")
    ap.add_argument("--vorlage", action="store_true", help="CSV-Vorlage mit Spaltenerklärung ausgeben")
    ap.add_argument("--vorschlag", nargs="+", metavar=("FUNKTION", "LEISTUNG_VA"), help="Sicherung, Kabel, Phasen für einen Kreis vorschlagen; optional 'drehstrom' und 'fi' anhängen")
    ap.add_argument("--json", action="store_true", help="Befunde als JSON")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    if a.vorlage:
        print(VORLAGE_CSV, end="")
        return 0
    if a.vorschlag:
        f = a.vorschlag[0]
        rest = [x.lower() for x in a.vorschlag[1:]]
        va = next((zahl(x) for x in rest if zahl(x) is not None), 0.0) or 0.0
        v = vorschlag(f, va, drehstrom="drehstrom" in rest, vorgeschalteter_fi="fi" in rest)
        if a.json:
            print(json.dumps(v.__dict__, ensure_ascii=False, indent=2))
        else:
            print(f"Vorschlag für {v.funktion} mit {ganzzahl(va)} VA: Sicherung {v.sicherung}, Kabel {v.kabel}, {v.phasen}-phasig")
            print(HERKUNFT)
        return 0

    if a.beispiel:
        kreise = lies_csv(BEISPIEL_CSV)
    elif a.datei:
        with open(a.datei, encoding="utf-8-sig") as fh:
            text = fh.read()
        kreise = lies_json(text) if a.datei.lower().endswith(".json") or text.lstrip().startswith(("[", "{")) else lies_csv(text)
    else:
        ap.print_help()
        return 2

    befunde = pruefe_verzeichnis(kreise)
    if a.json:
        print(json.dumps({"stromkreise": len(kreise), "befunde": [b.__dict__ for b in befunde], "herkunft": HERKUNFT}, ensure_ascii=False, indent=2))
    else:
        print(bericht(kreise, befunde))
    return 0


if __name__ == "__main__":
    sys.exit(main())
