#!/usr/bin/env python3
"""Leistungsbilanz nach DIN 18015-1 für Wohn- und Nichtwohngebäude.

Rechnet die zu erwartende gleichzeitige Gesamtleistung eines Gebäudes, den
Bemessungsstrom am Hausanschluss und die nächste NH-Normsicherung, mit
vollständigem Rechenweg und Hinweisen mit Normbezug.

Bemessungsfall ist die Winter-Abendspitze: dunkel, kalt, Wärmepumpe und
Ladepunkte in Betrieb, PV-Ertrag null. Eine PV-Anlage senkt den Bezug deshalb
nie; sie wird nur in der Einspeiserichtung geprüft.

Grundlagen:
  - DIN 18015-1:2020-05, Anhang A: Bedarfskurven (Kurve A mit, Kurve B ohne
    elektrische Warmwasserbereitung), Sonderlasten separat.
  - VDE-AR-N 4100:2019-04: Anmelde- und Zustimmungspflichten, Schieflast
    4,6 kVA, Ladeeinrichtungen ab 3,6 kVA / 12 kVA.
  - § 14a EnWG: steuerbare Verbrauchseinrichtungen über 4,2 kW.
  - AMEV EltAnlagen 2025: Planungswerte in W/m² für Nichtwohnflächen.

Nutzung:
  python leistungsbilanz.py --beispiel
  python leistungsbilanz.py eingabe.json [--json]
  python leistungsbilanz.py --vorlage > eingabe.json

Nur Standardbibliothek, keine Netzverbindung. Die Rechnung ist eine
Planungsgrundlage; verbindlich sind die TAB und die Anschlusszusage des
Netzbetreibers.

MIT-Lizenz. Herkunft: BimWired, https://bimwired.com/landing/wissen/leistungsbilanz-din-18015-1.html
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------- Daten ----

# DIN 18015-1:2020-05, Anhang A: S_eff in kVA über der Zahl der Wohneinheiten.
KURVE_B = [  # OHNE elektrische Warmwasserbereitung
    (1, 14.5), (2, 24), (3, 32), (4, 37), (5, 41), (6, 44), (7, 47), (8, 50), (9, 53), (10, 55),
    (11, 57), (12, 59), (13, 61), (14, 63), (15, 65), (16, 67), (17, 69), (18, 70), (19, 71), (20, 72),
    (22, 74), (24, 76), (26, 78), (28, 80), (30, 82), (32, 84), (34, 86), (36, 87), (38, 88), (40, 89),
    (45, 92), (50, 95), (55, 97), (60, 99), (65, 101), (70, 102), (80, 104), (90, 106), (100, 108),
]
KURVE_A = [  # MIT elektrischer Warmwasserbereitung (Durchlauferhitzer)
    (1, 34), (2, 52), (3, 64), (4, 73), (5, 81), (6, 87), (7, 93), (8, 98), (9, 103), (10, 107),
    (11, 110), (12, 113), (13, 116), (14, 119), (15, 122), (16, 125), (17, 128), (18, 130), (19, 132), (20, 134),
    (22, 138), (24, 142), (26, 146), (28, 150), (30, 153), (32, 156), (34, 159), (36, 161), (38, 163), (40, 165),
    (45, 170), (50, 175), (55, 179), (60, 183), (65, 186), (70, 189), (80, 195), (90, 200), (100, 205),
]

U_NETZ = 400.0
WURZEL3 = math.sqrt(3)
SICHERUNGEN = [35, 50, 63, 80, 100, 125, 160, 200, 224, 250, 315, 400, 500, 630]  # NH gG
COSPHI_FLAECHE = 0.9

# Planungswerte für Nichtwohnflächen (AMEV-/VDI-orientiert): W/m² und Gleichzeitigkeit.
NUTZUNGEN = {
    "buero": (30, 0.7, "Büro / Verwaltung"),
    "verkauf": (60, 0.8, "Verkauf / Einzelhandel"),
    "gastro": (150, 0.6, "Gastronomie mit Küche"),
    "praxis": (40, 0.7, "Praxis (Arzt, Therapie)"),
    "werkstatt": (50, 0.6, "Werkstatt / Gewerbe"),
    "lager": (10, 0.8, "Lager / Logistik"),
    "parkhaus": (12, 0.7, "Parkhaus / Tiefgarage"),
    "hotel": (40, 0.7, "Hotel / Beherbergung"),
    "schule": (15, 0.8, "Schule / Bildung"),
    "custom": (50, 0.7, "Eigener Wert"),
}

# Netzbetreiber-Datensätze. geprüft=True: aus dem TAB-Dokument entnommen;
# False: Referenzwert nach VDE-AR-N 4100 / TAB 2023, projektbezogen zu prüfen.
NETZBETREIBER: dict[str, dict[str, Any]] = {
    "standard": dict(label="VDE-AR-N 4100 / TAB 2023", region="bundesweiter Standard", geprueft=True, min_sicherung=0,
                     bemessung="DIN 18015-1 Anhang A (Bedarfskurven), Sonderlasten separat",
                     quelle="VDE-AR-N 4100:2019-04, TAB 2023 (BDEW/FNN-Bundesmusterwortlaut), DIN 18015-1", hinweise=[]),
    "svs": dict(label="SVS Stadtwerke Villingen-Schwenningen", region="Villingen-Schwenningen (BW)", geprueft=True, min_sicherung=50, tabelle="svs",
                bemessung="eigene Zuordnungstabelle, konsistent mit DIN 18015-1",
                quelle="SVS Ergänzungen zur TAB Niederspannung, Kap. 6.2.1",
                hinweise=[("info", "Kleinste Hausanschluss-Sicherung 50 A (Wohnzwecke bzw. Nichtwohngebäude bis 30 kW).")]),
    "stuttgart_netze": dict(label="Stuttgart Netze", region="Stuttgart (BW)", geprueft=True, min_sicherung=0,
                            bemessung="DIN 18015-1 Anhang A (TAB 2023 mit Ergänzungen des Netzbetreibers)",
                            quelle="Stuttgart Netze, Ergänzungen zu den TAB 2023 (bzw. TAB BW 2019)",
                            hinweise=[("warn", "Ab einer Anschlussleistung über 156 kW ist eine kundeneigene Hausanschluss- oder NSHV-Kombination mit Zustimmung erforderlich. Datenleitung Cat. 5 vom Zählerplatz zur Wohnungsverteilung (DIN 18015-1, Abschnitt 5.2.6).")]),
    "enetz_sh": dict(label="e-netz Südhessen", region="Südhessen (Darmstadt und Umgebung)", geprueft=True, min_sicherung=0, tabelle="enetz",
                     bemessung="eigene Bemessungsgrundlage mit Warmwasser-Zuschlagsmethode",
                     quelle="e-netz Südhessen, Bemessungsgrundlage el. Warmwasserbereitung (06.03.2020)",
                     hinweise=[("info", "Anschlussgröße 1 bis 50 kW, Anschlussgröße 2 bis 100 kW, darüber Sonder-Anschlussgröße.")]),
    "netze_bw": dict(label="Netze BW", region="Baden-Württemberg", geprueft=False, min_sicherung=0,
                     bemessung="DIN 18015-1 Anhang A (TAB 2023 mit regionaler Ergänzung)",
                     quelle="Netze BW, Ergänzung zur TAB BW / TAB 2023 (Bundesmuster)",
                     hinweise=[("warn", "Hauptleitung mindestens 63 A. Kleinste Hausanschluss-Sicherung und Baukostenzuschuss projektbezogen abstimmen.")]),
    "freiburg_bn": dict(label="bnNETZE (badenovaNETZE)", region="Freiburg / Südbaden (BW)", geprueft=False, min_sicherung=0,
                        bemessung="DIN 18015-1 Anhang A (TAB BW 2019 mit Hinweisen des Netzbetreibers)",
                        quelle="bnNETZE GmbH (badenovaNETZE), Hinweise zu den TAB (TAB BW 2019)",
                        hinweise=[("warn", "Kleinste Hausanschluss-Sicherung und Baukostenzuschuss projektbezogen mit dem Netzbetreiber abstimmen.")]),
    "rng_koeln": dict(label="Rheinische NETZGesellschaft (RNG)", region="Köln (NRW)", geprueft=False, min_sicherung=0,
                      bemessung="DIN 18015-1 Anhang A (TAB 2023 mit Ergänzungen des Netzbetreibers)",
                      quelle="Rheinische NETZGesellschaft mbH (RNG), Ergänzungen zur TAB (RheinEnergie-Gruppe)",
                      hinweise=[("warn", "Kleinste Hausanschluss-Sicherung und Baukostenzuschuss projektbezogen mit dem Netzbetreiber abstimmen.")]),
    "bayernwerk": dict(label="Bayernwerk Netz", region="Bayern", geprueft=False, min_sicherung=0,
                       bemessung="DIN 18015-1 Anhang A (TAB 2023 mit Ergänzungen des Netzbetreibers)",
                       quelle="Bayernwerk Netz, Technische Ergänzungen Niederspannung / TAB 2023",
                       hinweise=[("warn", "Ab einer Summen-Wirkleistung von 135 kW ist ein Nachweis nach VDE-AR-N 4110 (Mittelspannung) zu führen.")]),
    "custom": dict(label="Anderer Netzbetreiber", region="nicht hinterlegt", geprueft=False, min_sicherung=0,
                   bemessung="DIN 18015-1 Anhang A (VDE-AR-N 4100 als Basis)", quelle="TAB des örtlichen Netzbetreibers",
                   hinweise=[("warn", "Verbindlich ist die TAB des örtlichen Netzbetreibers. Sie kann eine eigene Bemessungstabelle, eine abweichende kleinste Hausanschluss-Sicherung oder eine eigene BKZ-Regelung enthalten.")]),
}

GEBAEUDETYP = {
    "efh": "Einfamilienhaus",
    "mfh": "Mehrfamilienhaus",
    "mix": "Wohn- und Geschäftshaus",
    "nwg": "Nichtwohngebäude",
}

VORLAGE: dict[str, Any] = {
    "netzbetreiber": "standard",
    "gebaeudetyp": "mfh",
    "reserve": 10,
    "wohneinheiten": [
        {"bezeichnung": "3-Zimmer", "anzahl": 8, "el_warmwasser": False, "dle_kw": 21},
        {"bezeichnung": "2-Zimmer mit DLE", "anzahl": 4, "el_warmwasser": True, "dle_kw": 21},
    ],
    "nutzflaechen": [
        {"nutzung": "buero", "flaeche": 0, "w_pro_m2": 30, "g": 0.7},
    ],
    "sonderlasten": [
        {"bezeichnung": "Sauna", "p_kw": 0, "cos_phi": 1, "g": 1, "einphasig": False},
    ],
    "waermepumpe": {"aktiv": True, "anzahl": 1, "pel_kw": 8, "heizstab_kw": 6, "heizstab_gleichzeitig": True, "cos_phi": 0.95, "g": 1},
    "lueftung": {"aktiv": False, "p_kw": 0.5, "cos_phi": 0.9, "g": 1},
    "klima": {"aktiv": False, "p_kw": 4, "cos_phi": 0.9, "g": 1},
    "aufzug": {"aktiv": True, "anzahl": 1, "p_kw": 6.5, "cos_phi": 0.85, "g": 0.5},
    "allgemeinstrom": {"aktiv": True, "p_kw": 2, "cos_phi": 0.95, "g": 0.9},
    "e_mobilitaet": {"aktiv": True, "ladepunkte": 4, "leistung_je_ladepunkt_kw": 11, "lastmanagement": "statisch", "max_summenleistung_kw": 22},
    "pv": {"aktiv": True, "kwp": 30, "wechselrichter_kva": 27, "einspeiseart": "ueberschuss"},
}

# -------------------------------------------------------------- Modell ----


@dataclass
class Zeile:
    pos: str
    ansatz: str
    p_kw: float | None
    g: float | None
    cos_phi: float | None
    s_kva: float


@dataclass
class Schritt:
    titel: str
    formel: str = ""
    quelle: str = ""


@dataclass
class Hinweis:
    stufe: str  # info | warn | kritisch
    text: str


@dataclass
class Ergebnis:
    typ: str
    zeilen: list[Zeile] = field(default_factory=list)
    schritte: list[Schritt] = field(default_factory=list)
    hinweise: list[Hinweis] = field(default_factory=list)
    s_ges_kva: float = 0.0
    ib_a: float = 0.0
    ib_mit_reserve_a: float = 0.0
    sicherung: int | None = None
    sicherung_mit_reserve: int | None = None
    anzahl_we: int = 0
    anzahl_we_warmwasser: int = 0
    s_wohnen_kva: float = 0.0
    pv: dict[str, Any] | None = None
    normbezug: list[str] = field(default_factory=list)


def z1(v: float) -> str:
    return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def z2(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


def z0(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def zahl(v: Any) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return f if math.isfinite(f) else 0.0


# ------------------------------------------------------------ Kurve -------


def kurve(tabelle: list[tuple[int, float]], n: float) -> tuple[float, str, bool]:
    """Wert der Bedarfskurve bei n Wohneinheiten: (kVA, Herkunft, extrapoliert).

    Zwischen Stützstellen linear interpoliert; über der letzten Stützstelle
    mit einem Potenzansatz aus den letzten beiden extrapoliert. Das ist dann
    ausdrücklich außerhalb von Anhang A und wird gemeldet.
    """
    if n <= 0:
        return 0.0, "", False
    if n <= tabelle[0][0]:
        return float(tabelle[0][1]), f"Tabellenwert (n = {tabelle[0][0]})", False
    for i, (x, y) in enumerate(tabelle):
        if n == x:
            return float(y), "Tabellenwert", False
        if i < len(tabelle) - 1 and x < n < tabelle[i + 1][0]:
            x2, y2 = tabelle[i + 1]
            val = y + (y2 - y) * (n - x) / (x2 - x)
            return val, f"linear interpoliert zwischen n = {x} ({z1(y)} kVA) und n = {x2} ({z1(y2)} kVA)", False
    (x1, y1), (x2, y2) = tabelle[-2], tabelle[-1]
    k = math.log(y2 / y1) / math.log(x2 / x1)
    return y2 * (n / x2) ** k, f"über n = {x2} hinaus extrapoliert, also außerhalb von Anhang A", True


def sicherung_fuer(strom: float, mindest: float) -> int | None:
    for f in SICHERUNGEN:
        if f >= max(strom, mindest):
            return f
    return None


# ------------------------------------------------------------ Rechnung ----


def rechne(e: dict[str, Any]) -> Ergebnis:
    typ = e.get("gebaeudetyp", "mfh")
    if typ not in GEBAEUDETYP:
        typ = "mfh"
    reserve = max(0.0, zahl(e.get("reserve", 0)))
    nb_key = e.get("netzbetreiber", "standard")
    nb = NETZBETREIBER.get(nb_key, NETZBETREIBER["standard"])
    r = Ergebnis(typ=typ)
    hat_wohnteil = typ != "nwg"
    hat_flaechen = typ in ("mix", "nwg")

    # -- Wohnen (Bedarfskurven Anhang A) --
    anzahl_we = 0
    anzahl_ww = 0
    groesster_dle = 0.0
    if hat_wohnteil:
        for we in e.get("wohneinheiten") or []:
            n = max(0, round(zahl(we.get("anzahl"))))
            anzahl_we += n
            if we.get("el_warmwasser"):
                anzahl_ww += n
                groesster_dle = max(groesster_dle, zahl(we.get("dle_kw")))

    s_wohnen = 0.0
    if anzahl_we > 0:
        kb, qb, exb = kurve(KURVE_B, anzahl_we)
        r.schritte.append(Schritt(f"{anzahl_we} Wohneinheiten, davon {anzahl_ww} mit elektrischer Warmwasserbereitung"))
        extrapoliert = exb
        if anzahl_ww == 0:
            s_wohnen = kb
            r.schritte.append(Schritt("Grundlast Wohnen über Kurve B (ohne elektrische Warmwasserbereitung)",
                                      f"S_Wohnen = B({anzahl_we}) = {z1(kb)} kVA", qb))
            ansatz = "DIN 18015-1 Anhang A, Kurve B"
        elif anzahl_ww == anzahl_we:
            ka, qa, exa = kurve(KURVE_A, anzahl_we)
            extrapoliert = extrapoliert or exa
            s_wohnen = ka
            r.schritte.append(Schritt("Grundlast Wohnen über Kurve A (alle Wohneinheiten mit elektrischer Warmwasserbereitung)",
                                      f"S_Wohnen = A({anzahl_we}) = {z1(ka)} kVA", qa))
            ansatz = "DIN 18015-1 Anhang A, Kurve A"
        else:
            ka, _, exa = kurve(KURVE_A, anzahl_ww)
            kbww, _, _ = kurve(KURVE_B, anzahl_ww)
            extrapoliert = extrapoliert or exa
            zuschlag = ka - kbww
            s_wohnen = kb + zuschlag
            r.schritte.append(Schritt("Grundlast Wohnen über Kurve B für alle Wohneinheiten", f"B({anzahl_we}) = {z1(kb)} kVA", qb))
            r.schritte.append(Schritt(f"Zuschlag für die {anzahl_ww} Wohneinheiten mit Durchlauferhitzer, als Differenz der Bedarfskurven",
                                      f"ΔS_WW = A({anzahl_ww}) - B({anzahl_ww}) = {z1(ka)} - {z1(kbww)} = {z1(zuschlag)} kVA"))
            r.schritte.append(Schritt("Summe Wohnen", f"S_Wohnen = {z1(kb)} + {z1(zuschlag)} = {z1(s_wohnen)} kVA"))
            ansatz = "DIN 18015-1 Anhang A, Kurve B mit Warmwasser-Zuschlag"
        if extrapoliert:
            r.hinweise.append(Hinweis("kritisch", "Die Anzahl der Wohneinheiten liegt außerhalb des Geltungsbereichs der Bedarfskurven (Anhang A reicht bis 100 WE). Die Werte wurden extrapoliert. Bedarf mit dem Netzbetreiber oder über eine Lastgangbetrachtung abstimmen."))
        r.zeilen.append(Zeile(f"Wohnen: {anzahl_we} WE, davon {anzahl_ww} mit el. Warmwasser", ansatz, None, None, None, s_wohnen))

    # -- Nutzflächen --
    s_gewerbe = 0.0
    if hat_flaechen:
        for fl in e.get("nutzflaechen") or []:
            flaeche = zahl(fl.get("flaeche"))
            w = zahl(fl.get("w_pro_m2"))
            g = zahl(fl.get("g"))
            p_kw = flaeche * w / 1000
            if p_kw <= 0:
                continue
            s = p_kw * g / COSPHI_FLAECHE
            label = NUTZUNGEN.get(fl.get("nutzung", "custom"), NUTZUNGEN["custom"])[2]
            s_gewerbe += s
            r.zeilen.append(Zeile(f"Gewerbe: {label}", f"Planungswert {z0(w)} W/m² auf {z0(flaeche)} m²", p_kw, g, COSPHI_FLAECHE, s))
            r.schritte.append(Schritt(label, f"P = {z0(flaeche)} m² x {z0(w)} W/m² = {z1(p_kw)} kW;  S = P × g / cos φ = {z1(p_kw)} x {z2(g)} / {z2(COSPHI_FLAECHE)} = {z1(s)} kVA"))
        if s_gewerbe > 0:
            r.hinweise.append(Hinweis("warn", "Gewerbeflächen sind mit Planungs- und Erfahrungswerten in W/m² angesetzt, das sind keine Normwerte der DIN 18015-1. Werte mit dem Nutzerbedarf und gegebenenfalls einer AMEV-Leistungsbilanz abgleichen."))

    # -- Sonderlast-Blöcke --
    def block(pos: str, ansatz: str, p_kw: float, cos_phi: float, g: float, vorlauf: str = "") -> float:
        if p_kw <= 0:
            return 0.0
        s = p_kw * g / cos_phi
        r.zeilen.append(Zeile(pos, ansatz, p_kw, g, cos_phi, s))
        r.schritte.append(Schritt(pos, f"S = {vorlauf}{z1(p_kw)} kW × g {z2(g)} / cos φ {z2(cos_phi)} = {z1(s)} kVA"))
        return s

    wp = e.get("waermepumpe") or {}
    if wp.get("aktiv"):
        n = max(1, round(zahl(wp.get("anzahl", 1))))
        pel = zahl(wp.get("pel_kw"))
        heizstab = zahl(wp.get("heizstab_kw"))
        gleichzeitig = bool(wp.get("heizstab_gleichzeitig", True))
        mit_heizstab = gleichzeitig and heizstab > 0
        p_kw = n * pel + (heizstab if mit_heizstab else 0)
        vorlauf = f"({n} × {z1(pel)}{' + ' + z1(heizstab) if mit_heizstab else ''}) = " if (n > 1 or mit_heizstab) else ""
        block(f"Wärmepumpe ({n}-fach)" if n > 1 else "Wärmepumpe",
              f"Dauerbetrieb, Heizstab {z1(heizstab)} kW gleichzeitig" if mit_heizstab else "Dauerbetrieb",
              p_kw, zahl(wp.get("cos_phi")) or 0.95, zahl(wp.get("g", 1)), vorlauf)
        r.hinweise.append(Hinweis("info", "Wärmepumpe: anmelde- und zustimmungspflichtig beim Netzbetreiber (VDE-AR-N 4100, Heiz- und Klimageräte). Über 4,2 kW als steuerbare Verbrauchseinrichtung nach § 14a EnWG mit netzorientierter Steuerung einplanen, samt Steuer- und Kommunikationsanbindung am Zählerplatz."))
        if not gleichzeitig and heizstab > 0:
            r.hinweise.append(Hinweis("warn", "Der Heizstab ist als „nicht gleichzeitig“ angesetzt. Die Verriegelung muss tatsächlich vorgesehen und dokumentiert sein."))

    lu = e.get("lueftung") or {}
    if lu.get("aktiv"):
        block("Lüftungsanlage (KWL)", "Dauerbetrieb", zahl(lu.get("p_kw")), zahl(lu.get("cos_phi")) or 0.9, zahl(lu.get("g", 1)))

    kl = e.get("klima") or {}
    if kl.get("aktiv"):
        s = block("Klimatisierung", "Sommerfall", zahl(kl.get("p_kw")), zahl(kl.get("cos_phi")) or 0.9, zahl(kl.get("g", 1)))
        if s > 0:
            r.hinweise.append(Hinweis("info", "Klimageräte sind anmelde- und zustimmungspflichtig beim Netzbetreiber (VDE-AR-N 4100). Prüfen, ob Heizfall (Wärmepumpe) und Kühlfall gleichzeitig auftreten können, sonst nur den größeren Fall ansetzen."))

    az = e.get("aufzug") or {}
    if az.get("aktiv"):
        n = max(1, round(zahl(az.get("anzahl", 1))))
        je = zahl(az.get("p_kw"))
        block(f"Aufzugsanlage ({n}-fach)" if n > 1 else "Aufzugsanlage", "Aussetzbetrieb, Erfahrungswert",
              n * je, zahl(az.get("cos_phi")) or 0.85, zahl(az.get("g", 0.5)), f"({n} × {z1(je)}) = " if n > 1 else "")

    al = e.get("allgemeinstrom") or {}
    if al.get("aktiv"):
        block("Allgemeinstrom (Hausanlage)", "eigener Zählpunkt", zahl(al.get("p_kw")), zahl(al.get("cos_phi")) or 0.95, zahl(al.get("g", 0.9)))

    # -- E-Mobilität: ohne Lastmanagement volle Addition, sonst die Begrenzung --
    em = e.get("e_mobilitaet") or {}
    if em.get("aktiv"):
        n = max(1, round(zahl(em.get("ladepunkte", 1))))
        je = zahl(em.get("leistung_je_ladepunkt_kw"))
        p_sum = n * je
        lm = em.get("lastmanagement", "ohne")
        ohne_lm = lm not in ("statisch", "dynamisch")
        grenze = zahl(em.get("max_summenleistung_kw"))
        s = p_sum if ohne_lm else min(p_sum, grenze)
        g_eff = s / p_sum if p_sum > 0 else 1.0
        ansatz = ("ohne Lastmanagement, volle Addition (g = 1,00)" if ohne_lm
                  else f"{'statisches' if lm == 'statisch' else 'dynamisches'} Lastmanagement, Begrenzung {z1(grenze)} kW (g_eff = {z2(g_eff)})")
        r.zeilen.append(Zeile(f"E-Mobilität: {n} Ladepunkte a {z1(je)} kW", ansatz, p_sum, g_eff, 1.0, s))
        r.schritte.append(Schritt("E-Mobilität",
                                  f"S = {n} x {z1(je)} kW × g 1,00 = {z1(s)} kVA" if ohne_lm else f"S = min({n} × {z1(je)}; P_LM {z1(grenze)}) = {z1(s)} kVA",
                                  ansatz))
        if ohne_lm and n > 1:
            r.hinweise.append(Hinweis("warn", f"E-Mobilität ohne Lastmanagement: {z1(p_sum)} kW werden voll addiert. Ein statisches oder dynamisches Lastmanagement senkt den Ansatz erheblich."))
        if lm == "dynamisch":
            r.hinweise.append(Hinweis("info", "Dynamisches Lastmanagement wirkt am Netzanschlusspunkt, die Wohnungen haben Vorrang. Bilanzansatz ist die eingestellte Maximalleistung der Ladegruppe."))
        if 4.6 < je < 10:
            r.hinweise.append(Hinweis("kritisch", "Einphasige Ladeeinrichtungen über 4,6 kVA sind wegen der Schieflastgrenze unzulässig (VDE-AR-N 4100)."))
        r.hinweise.append(Hinweis("info", "Ladeeinrichtungen sind ab 3,6 kVA beim Netzbetreiber anzumelden, ab 12 kVA Summenbemessungsleistung zustimmungspflichtig (VDE-AR-N 4100). Über 4,2 kW gelten sie als steuerbare Verbrauchseinrichtung nach § 14a EnWG."))

    # -- Sonstige Sonderlasten --
    for so in e.get("sonderlasten") or []:
        p_kw = zahl(so.get("p_kw"))
        if p_kw <= 0:
            continue
        cos_phi = zahl(so.get("cos_phi")) or 1.0
        g = zahl(so.get("g", 1))
        bez = (so.get("bezeichnung") or "").strip() or "Sonderlast"
        s = p_kw * g / cos_phi
        einphasig = bool(so.get("einphasig"))
        r.zeilen.append(Zeile(f"Sonderlast: {bez}", "einphasig" if einphasig else "dreiphasig", p_kw, g, cos_phi, s))
        r.schritte.append(Schritt(f"Sonderlast: {bez}", f"S = {z1(p_kw)} kW × g {z2(g)} / cos φ {z2(cos_phi)} = {z1(s)} kVA"))
        if einphasig and p_kw / cos_phi > 4.6:
            r.hinweise.append(Hinweis("kritisch", f"„{bez}“: einphasige Last mit {z1(p_kw / cos_phi)} kVA überschreitet die Schieflastgrenze von 4,6 kVA (VDE-AR-N 4100). Dreiphasig anschließen oder aufteilen."))
        if p_kw > 12:
            r.hinweise.append(Hinweis("info", f"„{bez}“: Einzelgeräte über 12 kVA sind beim Netzbetreiber zustimmungspflichtig (VDE-AR-N 4100)."))

    if anzahl_ww > 0:
        r.hinweise.append(Hinweis("info", f"Durchlauferhitzer in {anzahl_ww} Wohneinheiten: Geräte über 12 kVA sind beim Netzbetreiber zustimmungspflichtig (VDE-AR-N 4100). Die zeitgleiche Leistung steckt bereits im Warmwasser-Zuschlag der Bedarfskurve, sie darf nicht zusätzlich als Sonderlast erscheinen."))
        if 0 < groesster_dle < 18:
            r.hinweise.append(Hinweis("warn", "Durchlauferhitzer unter 18 kW: Komfort für Dusch- und Badezwecke prüfen, üblich sind 18 bis 27 kW elektronisch geregelt."))

    # -- Summe und Bewertung --
    s_ges = sum(z.s_kva for z in r.zeilen)
    ib = s_ges * 1000 / (WURZEL3 * U_NETZ)
    ib_res = ib * (1 + reserve / 100)
    mind = float(nb["min_sicherung"])
    sich = sicherung_fuer(ib, mind)
    sich_res = sicherung_fuer(ib_res, mind)

    if r.zeilen:
        r.schritte.append(Schritt("Summe der zeitgleichen Leistung", "S_max = " + " + ".join(z1(z.s_kva) for z in r.zeilen) + f" = {z1(s_ges)} kVA"))
        r.schritte.append(Schritt("Bemessungsstrom bei symmetrischer Last, 3~ 400 V", f"I_b = S_max / (√3 x U) = {z1(s_ges)} kVA x 1000 / (1,732 × 400 V) = {z1(ib)} A"))
        basis = f"{sich} A" if sich else "> 630 A"
        if reserve > 0:
            formel = f"{basis};  mit {z0(reserve)} % Reserve: I = {z1(ib_res)} A -> {str(sich_res) + ' A' if sich_res else '> 630 A'}"
        else:
            formel = basis + (f"  (Auslastung {z0(ib / sich * 100)} %)" if sich else "")
        r.schritte.append(Schritt("Empfehlung Hausanschluss-Absicherung, nächste NH-Normgröße gG", formel))

    if reserve == 0 and anzahl_we > 0:
        r.hinweise.append(Hinweis("info", "Auslegung ohne pauschalen Reservezuschlag, als dokumentierte Planerentscheidung: die Bedarfskurven nach DIN 18015-1 Anhang A sind die obere Einhüllende gemessener Höchstlasten und damit bereits konservativ. Zusätzlich sind die Sonderlasten auf der sicheren Seite bilanziert."))

    # -- PV: senkt den Bezug NICHT --
    pv = e.get("pv") or {}
    if pv.get("aktiv"):
        kwp = zahl(pv.get("kwp"))
        wr = zahl(pv.get("wechselrichter_kva"))
        art = pv.get("einspeiseart", "ueberschuss")
        art_label = {"ueberschuss": "Überschusseinspeisung", "voll": "Volleinspeisung", "mieterstrom": "Mieterstrom"}.get(art, "Überschusseinspeisung")
        i_ein = wr * 1000 / (WURZEL3 * U_NETZ)
        massgebend = max(s_ges, wr)
        r.pv = {"kwp": kwp, "wr_kva": wr, "art": art_label, "i_ein_a": i_ein, "massgebend_kva": massgebend}
        r.schritte.append(Schritt(f"PV-Erzeugungsanlage: {z0(kwp)} kWp, Wechselrichter {z1(wr)} kVA, {art_label}",
                                  f"I_Ein = {z1(wr)} kVA x 1000 / (1,732 × 400 V) = {z1(i_ein)} A;  max(Bezug {z1(s_ges)}; Einspeisung {z1(wr)}) = {z1(massgebend)} kVA",
                                  "Die Erzeugung senkt die Bezugsleistung nicht. Bemessungsfall ist die Winter-Abendspitze bei einem PV-Ertrag von null."))
        r.hinweise.append(Hinweis("info", f"PV mit {z0(kwp)} kWp: Anmeldung als Erzeugungsanlage (VDE-AR-N 4105 im Niederspannungsnetz, VDE-AR-N 4110 bei Mittelspannung) und Eintrag im Marktstammdatenregister erforderlich. Ein Anlagenzertifikat wird erst über 500 kWp installierter Leistung bzw. 270 kW Einspeiseleistung nötig."))
        if wr > 30:
            r.hinweise.append(Hinweis("info", "Wechselrichter-Scheinleistung über 30 kVA: zentraler NA-Schutz erforderlich (VDE-AR-N 4105)."))
        if wr > s_ges:
            r.hinweise.append(Hinweis("kritisch", f"Die Einspeiseleistung von {z1(wr)} kVA übersteigt die Bezugsleistung von {z1(s_ges)} kVA. Der Netzanschluss ist damit durch die Einspeisung bemessen: Zuleitung, NSHV und Schutzorgane für die Rückspeisung auslegen und die Netzanschlussleistung entsprechend anmelden."))
        else:
            r.hinweise.append(Hinweis("info", "Die Einspeisung liegt unter dem Bezug. Der Netzanschluss bleibt durch den Bezug bemessen, die PV-Anlage erhöht die Anschlussgröße nicht."))

    # -- Anschlussgröße --
    if not sich_res:
        r.hinweise.append(Hinweis("kritisch", "Bemessungsstrom über 630 A: ein Niederspannungs-Hausanschluss reicht voraussichtlich nicht aus. Trafostation oder Mittelspannungsanschluss frühzeitig mit dem Netzbetreiber klären."))
    elif sich_res > 250:
        r.hinweise.append(Hinweis("warn", "Anschlussgröße über 250 A: die Ausführung (Doppelanschluss, Wandlermessung, gegebenenfalls Trafostation) frühzeitig mit dem Netzbetreiber abstimmen."))
    if s_ges > 30:
        r.hinweise.append(Hinweis("info", "Über 30 kW erheben viele Netzbetreiber oberhalb eines Freibetrags einen Baukostenzuschuss je kW."))

    # -- TAB des Netzbetreibers --
    if nb["geprueft"]:
        r.hinweise.append(Hinweis("info", f"Bemessungsgrundlage {nb['label']}: {nb['bemessung']}."))
    else:
        r.hinweise.append(Hinweis("info", f"Bemessungsgrundlage {nb['label']}: {nb['bemessung']}. Referenzwert nach VDE-AR-N 4100 / TAB 2023, die konkrete TAB ist projektbezogen zu prüfen."))
    for stufe, text in nb["hinweise"]:
        r.hinweise.append(Hinweis(stufe, f"{nb['label']}: {text}"))
    if mind and sich and sich <= mind:
        r.hinweise.append(Hinweis("info", f"Kleinste Hausanschluss-Sicherung nach TAB {nb['label']}: {int(mind)} A. Die Empfehlung darf entsprechend nicht kleiner ausfallen."))
    if nb.get("tabelle") == "svs" and anzahl_we > 0:
        klasse = svs_klasse(anzahl_we, anzahl_ww > 0)
        if klasse:
            r.hinweise.append(Hinweis("info", f"Zuordnungstabelle des Netzbetreibers für den Wohnanteil: NH {klasse} A für die Grundlast Wohnen. Sonderlasten wie Wärmepumpe oder E-Mobilität sind gesondert hinzuzurechnen, maßgebend bleibt die vorliegende Bilanz."))
        else:
            r.hinweise.append(Hinweis("warn", f"Die Zuordnungstabelle des Netzbetreibers endet vor {anzahl_we} Wohneinheiten. Maßgebend ist die vorliegende individuelle Leistungsbilanz."))
    if nb.get("tabelle") == "enetz" and s_ges > 0:
        r.hinweise.append(Hinweis("info", f"Rechnerisch {z1(s_ges)} kVA. Die Anschlussgröße nach der Tabelle des Netzbetreibers gegenprüfen (Warmwasser-Zuschlagsmethode)."))
    if nb_key == "bayernwerk" and s_ges > 135:
        r.hinweise.append(Hinweis("warn", f"Bemessungsleistung {z1(s_ges)} kVA über 135 kW: Nachweis nach VDE-AR-N 4110 (Mittelspannung) erforderlich."))
    if nb_key == "stuttgart_netze" and s_ges > 156:
        r.hinweise.append(Hinweis("warn", f"Anschlussleistung {z1(s_ges)} kVA über 156 kW: kundeneigene Hausanschluss- oder NSHV-Kombination mit Zustimmung des Netzbetreibers erforderlich."))

    r.hinweise.append(Hinweis("info", "AMEV EltAnlagen 2025: bei Liegenschaften mit mehreren Gebäuden verschiedenartiger Nutzung zusätzlich einen Gebäude-Gleichzeitigkeitsfaktor von 0,7 bis 0,9 für die Standort- und Trafobemessung ansetzen."))
    r.hinweise.append(Hinweis("info", "Diese Bilanz ist eine Planungsgrundlage nach DIN 18015-1. Verbindlich sind die TAB und die Anschlusszusage des Netzbetreibers. Zählerplätze und Messkonzept sind nach VDE-AR-N 4100 gesondert zu planen."))

    r.normbezug = [
        "DIN 18015-1:2020-05: Elektrische Anlagen in Wohngebäuden, Planungsgrundlagen. Leistungsbedarf über die Bedarfskurven in Anhang A (Kurve A mit, Kurve B ohne elektrische Warmwasserbereitung), Sonderlasten separat.",
        "DIN 18015-2:2021-10: Art und Umfang der Mindestausstattung (Stromkreise und Steckdosen je Raum, flächenabhaengig, vgl. RAL-RG 678).",
        "VDE-AR-N 4100:2019-04, TAR Niederspannung: Anmelde- und Zustimmungspflichten (Einzelgeräte über 12 kVA, Wärmepumpen und Klimageräte, Ladeeinrichtungen ab 3,6 kVA), Schieflastgrenze 4,6 kVA, Zählerplätze.",
        "§ 14a EnWG (BNetzA-Festlegungen seit 01.01.2024): netzorientierte Steuerung steuerbarer Verbrauchseinrichtungen über 4,2 kW: Wärmepumpen, Wallboxen, Klimageräte, Speicher.",
        (f"TAB {nb['label']} ({nb['region']}): {nb['quelle']}. Aus dem TAB-Dokument entnommen." if nb["geprueft"]
         else f"TAB {nb['label']} ({nb['region']}): {nb['quelle']}. Basis VDE-AR-N 4100 / TAB 2023, die konkreten TAB-Details sind projektbezogen zu prüfen."),
        "AMEV EltAnlagen 2025: Planungswerte für flächenbezogene Leistungen in W/m² und Gebäude-Gleichzeitigkeitsfaktoren.",
        "DIN VDE 0100 und DIN VDE 0298-4 sowie DIN 18015-1 Abschnitt 5: Bemessung der Haupt- und Stromkreisleitungen, Spannungsfall der Hauptleitung höchstens 0,5 %.",
    ]

    r.s_ges_kva = s_ges
    r.ib_a = ib
    r.ib_mit_reserve_a = ib_res
    r.sicherung = sich
    r.sicherung_mit_reserve = sich_res
    r.anzahl_we = anzahl_we
    r.anzahl_we_warmwasser = anzahl_ww
    r.s_wohnen_kva = s_wohnen
    return r


def svs_klasse(anzahl_we: int, mit_warmwasser: bool) -> int | None:
    ohne = [(3, 50), (5, 63), (10, 80), (17, 100), (36, 125), (70, 160)]
    mit = [(1, 63), (2, 80), (3, 100), (6, 125), (11, 160)]
    for n, a in (mit if mit_warmwasser else ohne):
        if anzahl_we <= n:
            return a
    return None


# -------------------------------------------------------------- Ausgabe ---

HERKUNFT = "Berechnung nach DIN 18015-1, Skript von BimWired (MIT), https://bimwired.com/landing/wissen/leistungsbilanz-din-18015-1.html"


def bericht(r: Ergebnis, nb_key: str) -> str:
    nb = NETZBETREIBER.get(nb_key, NETZBETREIBER["standard"])
    out: list[str] = []
    out.append(f"LEISTUNGSBILANZ NACH DIN 18015-1  ({GEBAEUDETYP[r.typ]}, Bemessungsgrundlage {nb['label']})")
    out.append("")
    out.append("Bilanz der zeitgleichen Leistung")
    out.append(f"{'Position':<48} {'Ansatz':<52} {'P [kW]':>8} {'g':>5} {'cos φ':>8} {'S [kVA]':>8}")
    for z in r.zeilen:
        out.append(f"{z.pos[:48]:<48} {z.ansatz[:52]:<52} {z1(z.p_kw) if z.p_kw is not None else '':>8} {z2(z.g) if z.g is not None else '':>5} {z2(z.cos_phi) if z.cos_phi is not None else '':>8} {z1(z.s_kva):>8}")
    out.append(f"{'Summe S_max':<48} {'':<52} {'':>8} {'':>5} {'':>8} {z1(r.s_ges_kva):>8}")
    out.append("")
    out.append(f"Bemessungsstrom I_b = {z1(r.ib_a)} A (3~ 400 V, symmetrisch)")
    if r.ib_mit_reserve_a != r.ib_a:
        out.append(f"Mit Reserve: I = {z1(r.ib_mit_reserve_a)} A")
    out.append(f"Empfehlung Hausanschluss-Sicherung: NH {r.sicherung_mit_reserve} A gG" if r.sicherung_mit_reserve else "Empfehlung: über 630 A, Niederspannungs-Hausanschluss reicht voraussichtlich nicht")
    if r.pv:
        out.append(f"PV: Einspeisung {z1(r.pv['wr_kva'])} kVA ({z1(r.pv['i_ein_a'])} A), maßgebend für den Netzanschluss: {z1(r.pv['massgebend_kva'])} kVA")
    out.append("")
    out.append("Rechenweg")
    for i, s in enumerate(r.schritte, 1):
        out.append(f"{i:>2}. {s.titel}")
        if s.formel:
            out.append(f"    {s.formel}")
        if s.quelle:
            out.append(f"    ({s.quelle})")
    out.append("")
    out.append("Hinweise")
    for h in r.hinweise:
        out.append(f"  [{h.stufe.upper():<8}] {h.text}")
    out.append("")
    out.append("Normen- und Regelwerksgrundlagen")
    for n in r.normbezug:
        out.append(f"  - {n}")
    out.append("")
    out.append(HERKUNFT)
    return "\n".join(out)


def als_dict(r: Ergebnis) -> dict[str, Any]:
    return {
        "typ": r.typ,
        "zeilen": [z.__dict__ for z in r.zeilen],
        "schritte": [s.__dict__ for s in r.schritte],
        "hinweise": [h.__dict__ for h in r.hinweise],
        "s_ges_kva": round(r.s_ges_kva, 3),
        "ib_a": round(r.ib_a, 3),
        "ib_mit_reserve_a": round(r.ib_mit_reserve_a, 3),
        "sicherung": r.sicherung,
        "sicherung_mit_reserve": r.sicherung_mit_reserve,
        "anzahl_we": r.anzahl_we,
        "anzahl_we_warmwasser": r.anzahl_we_warmwasser,
        "s_wohnen_kva": round(r.s_wohnen_kva, 3),
        "pv": r.pv,
        "normbezug": r.normbezug,
        "herkunft": HERKUNFT,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Leistungsbilanz nach DIN 18015-1")
    ap.add_argument("eingabe", nargs="?", help="JSON-Datei mit der Eingabe (siehe --vorlage)")
    ap.add_argument("--beispiel", action="store_true", help="Beispiel rechnen (12 WE, Wärmepumpe, Aufzug, 4 Ladepunkte, PV)")
    ap.add_argument("--vorlage", action="store_true", help="leere Eingabedatei als JSON ausgeben")
    ap.add_argument("--json", action="store_true", help="Ergebnis als JSON statt als Bericht")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    if a.vorlage:
        print(json.dumps(VORLAGE, ensure_ascii=False, indent=2))
        return 0
    if a.beispiel:
        eingabe = VORLAGE
    elif a.eingabe:
        with open(a.eingabe, encoding="utf-8") as fh:
            eingabe = json.load(fh)
    else:
        ap.print_help()
        return 2

    r = rechne(eingabe)
    if a.json:
        print(json.dumps(als_dict(r), ensure_ascii=False, indent=2))
    else:
        print(bericht(r, eingabe.get("netzbetreiber", "standard")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
