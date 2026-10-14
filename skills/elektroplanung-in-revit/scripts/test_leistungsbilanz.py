"""Tests fuer leistungsbilanz.py: dieselben Faelle wie die Tests des
BimWired-Editors (web/src/lib/leistungsbilanz/berechnung.test.ts), damit
Skript und Werkzeug dieselben Zahlen liefern.

Ausfuehren:  python -m unittest test_leistungsbilanz   (im Ordner scripts/)
"""

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import leistungsbilanz as lb  # noqa: E402


def bilanz(**teil):
    e = {
        "netzbetreiber": "standard",
        "gebaeudetyp": "mfh",
        "reserve": 0,
        "wohneinheiten": [],
        "nutzflaechen": [],
        "sonderlasten": [],
        "waermepumpe": {"aktiv": False},
        "lueftung": {"aktiv": False},
        "klima": {"aktiv": False},
        "aufzug": {"aktiv": False},
        "allgemeinstrom": {"aktiv": False},
        "e_mobilitaet": {"aktiv": False},
        "pv": {"aktiv": False},
    }
    e.update(teil)
    return e


def we(anzahl, el_warmwasser=False, dle_kw=21):
    return {"bezeichnung": "Typ", "anzahl": anzahl, "el_warmwasser": el_warmwasser, "dle_kw": dle_kw}


class Bedarfskurven(unittest.TestCase):
    def test_stuetzstellen(self):
        self.assertEqual(lb.kurve(lb.KURVE_B, 1)[0], 14.5)
        self.assertEqual(lb.kurve(lb.KURVE_B, 12)[0], 59)
        self.assertEqual(lb.kurve(lb.KURVE_A, 10)[0], 107)
        self.assertEqual(lb.kurve(lb.KURVE_A, 100)[0], 205)

    def test_linear_interpoliert(self):
        self.assertAlmostEqual(lb.kurve(lb.KURVE_B, 21)[0], 73, places=6)

    def test_extrapoliert_jenseits_100(self):
        kva, _, ex = lb.kurve(lb.KURVE_B, 140)
        self.assertTrue(ex)
        self.assertGreater(kva, 108)

    def test_unter_erster_stuetzstelle(self):
        self.assertEqual(lb.kurve(lb.KURVE_A, 0.5)[0], 34)
        self.assertEqual(lb.kurve(lb.KURVE_A, 0)[0], 0)


class GrundlastWohnen(unittest.TestCase):
    def test_kurve_b(self):
        r = lb.rechne(bilanz(wohneinheiten=[we(12)]))
        self.assertEqual(r.anzahl_we, 12)
        self.assertEqual(r.s_wohnen_kva, 59)
        self.assertEqual(r.s_ges_kva, 59)

    def test_kurve_a(self):
        r = lb.rechne(bilanz(wohneinheiten=[we(12, True)]))
        self.assertEqual(r.s_wohnen_kva, 113)

    def test_mischbelegung(self):
        # 12 WE, 4 davon mit DLE: B(12) + [A(4) - B(4)] = 59 + (73 - 37)
        r = lb.rechne(bilanz(wohneinheiten=[we(8), we(4, True)]))
        self.assertEqual(r.anzahl_we_warmwasser, 4)
        self.assertAlmostEqual(r.s_wohnen_kva, 59 + (73 - 37), places=6)

    def test_nichtwohngebaeude_ohne_wohnteil(self):
        r = lb.rechne(bilanz(gebaeudetyp="nwg", wohneinheiten=[we(12)]))
        self.assertEqual(r.anzahl_we, 0)
        self.assertEqual(r.s_ges_kva, 0)


class BemessungUndSicherung(unittest.TestCase):
    def test_bemessungsstrom(self):
        r = lb.rechne(bilanz(wohneinheiten=[we(12)]))
        self.assertAlmostEqual(r.ib_a, 59 * 1000 / (math.sqrt(3) * 400), places=6)
        self.assertEqual(r.sicherung, 100)  # 85,2 A -> 100 A

    def test_reserve_auf_strom(self):
        r = lb.rechne(bilanz(wohneinheiten=[we(12)], reserve=25))
        self.assertAlmostEqual(r.ib_mit_reserve_a, r.ib_a * 1.25, places=6)
        self.assertEqual(r.sicherung_mit_reserve, 125)

    def test_kleinste_sicherung_der_tab(self):
        r = lb.rechne(bilanz(netzbetreiber="svs", wohneinheiten=[we(1)]))
        self.assertEqual(r.sicherung, 50)  # 14,5 kVA = 20,9 A, TAB verlangt 50 A

    def test_ueber_630_a(self):
        r = lb.rechne(bilanz(gebaeudetyp="nwg", nutzflaechen=[{"nutzung": "gastro", "flaeche": 4000, "w_pro_m2": 150, "g": 1}]))
        self.assertIsNone(r.sicherung_mit_reserve)
        self.assertTrue(any(h.stufe == "kritisch" for h in r.hinweise))


class Sonderlasten(unittest.TestCase):
    def test_waermepumpe_mit_heizstab(self):
        r = lb.rechne(bilanz(waermepumpe={"aktiv": True, "anzahl": 2, "pel_kw": 8, "heizstab_kw": 6, "heizstab_gleichzeitig": True, "cos_phi": 0.95, "g": 1}))
        self.assertAlmostEqual(r.s_ges_kva, (2 * 8 + 6) / 0.95, places=6)

    def test_verriegelter_heizstab(self):
        r = lb.rechne(bilanz(waermepumpe={"aktiv": True, "anzahl": 1, "pel_kw": 8, "heizstab_kw": 6, "heizstab_gleichzeitig": False, "cos_phi": 0.95, "g": 1}))
        self.assertAlmostEqual(r.s_ges_kva, 8 / 0.95, places=6)
        self.assertTrue(any(h.stufe == "warn" for h in r.hinweise))

    def test_ladepunkte_ohne_lastmanagement(self):
        r = lb.rechne(bilanz(e_mobilitaet={"aktiv": True, "ladepunkte": 4, "leistung_je_ladepunkt_kw": 11, "lastmanagement": "ohne", "max_summenleistung_kw": 22}))
        self.assertEqual(r.s_ges_kva, 44)

    def test_ladepunkte_mit_lastmanagement(self):
        r = lb.rechne(bilanz(e_mobilitaet={"aktiv": True, "ladepunkte": 4, "leistung_je_ladepunkt_kw": 11, "lastmanagement": "statisch", "max_summenleistung_kw": 22}))
        self.assertEqual(r.s_ges_kva, 22)

    def test_einphasige_sonderlast_schieflast(self):
        r = lb.rechne(bilanz(sonderlasten=[{"bezeichnung": "Sauna", "p_kw": 9, "cos_phi": 1, "g": 1, "einphasig": True}]))
        self.assertTrue(any(h.stufe == "kritisch" for h in r.hinweise))


class Photovoltaik(unittest.TestCase):
    def test_senkt_bezug_nicht(self):
        ohne = lb.rechne(bilanz(wohneinheiten=[we(12)]))
        mit = lb.rechne(bilanz(wohneinheiten=[we(12)], pv={"aktiv": True, "kwp": 30, "wechselrichter_kva": 27, "einspeiseart": "ueberschuss"}))
        self.assertEqual(mit.s_ges_kva, ohne.s_ges_kva)
        self.assertEqual(mit.pv["massgebend_kva"], ohne.s_ges_kva)

    def test_einspeisung_massgebend(self):
        r = lb.rechne(bilanz(wohneinheiten=[we(1)], pv={"aktiv": True, "kwp": 100, "wechselrichter_kva": 90, "einspeiseart": "voll"}))
        self.assertEqual(r.pv["massgebend_kva"], 90)
        self.assertTrue(any(h.stufe == "kritisch" for h in r.hinweise))


class Gewerbeflaechen(unittest.TestCase):
    def test_flaeche_mal_planungswert(self):
        r = lb.rechne(bilanz(gebaeudetyp="nwg", nutzflaechen=[{"nutzung": "buero", "flaeche": 1000, "w_pro_m2": 30, "g": 0.7}]))
        self.assertEqual(r.zeilen[0].p_kw, 30)
        self.assertAlmostEqual(r.s_ges_kva, 30 * 0.7 / 0.9, places=6)

    def test_flaechen_im_reinen_wohngebaeude_ignoriert(self):
        r = lb.rechne(bilanz(gebaeudetyp="mfh", wohneinheiten=[we(4)], nutzflaechen=[{"nutzung": "buero", "flaeche": 1000, "w_pro_m2": 30, "g": 0.7}]))
        self.assertEqual(r.s_ges_kva, 37)


class Kommandozeile(unittest.TestCase):
    def test_beispiel_laeuft_und_nennt_herkunft(self):
        out = subprocess.run([sys.executable, str(Path(__file__).parent / "leistungsbilanz.py"), "--beispiel"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        self.assertIn("LEISTUNGSBILANZ NACH DIN 18015-1", out)
        self.assertIn("bimwired.com", out)

    def test_json_ausgabe(self):
        out = subprocess.run([sys.executable, str(Path(__file__).parent / "leistungsbilanz.py"), "--beispiel", "--json"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        d = json.loads(out)
        self.assertEqual(d["anzahl_we"], 12)
        self.assertIn("sicherung_mit_reserve", d)

    def test_vorlage_ist_gueltige_eingabe(self):
        out = subprocess.run([sys.executable, str(Path(__file__).parent / "leistungsbilanz.py"), "--vorlage"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        self.assertIsNotNone(lb.rechne(json.loads(out)).sicherung)


if __name__ == "__main__":
    unittest.main()
