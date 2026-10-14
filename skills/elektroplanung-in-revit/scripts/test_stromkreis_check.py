"""Tests fuer stromkreis_check.py: Parser, Vorschlag und Regeln mit denselben
Faellen wie die Tests des BimWired-Editors
(tests/BimLibrary.Domain.Tests/Stromkreis/StromkreisRegelnTests.cs).

Ausfuehren:  python -m unittest test_stromkreis_check   (im Ordner scripts/)
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import stromkreis_check as sc  # noqa: E402


def codes(befunde):
    return [b.code for b in befunde]


class ParserSicherung(unittest.TestCase):
    def test_liest(self):
        faelle = [
            ("B16A", None, "B", 16), ("C 25", None, "C", 25), ("30mA/B16A", 30, "B", 16),
            ("D01/16A", None, "D01", 16), ("D02/35A", None, "D02", 35), ("NH00/80A", None, "NH00", 80),
            ("NH000/100A", None, "NH000", 100), ("nh3/630a", None, "NH3", 630), (" b13a ", None, "B", 13),
            ("  30MA/c25a", 30, "C", 25),
        ]
        for raw, ma, ch, a in faelle:
            with self.subTest(raw=raw):
                s = sc.parse_sicherung(raw)
                self.assertIsNotNone(s)
                self.assertEqual(s.rcd_ma, ma)
                self.assertEqual(s.charakteristik, ch)
                self.assertEqual(s.nennstrom_a, a)

    def test_freitext_ist_none(self):
        for raw in ["", "   ", "Reserve", "Vorsicherung", "foobar"]:
            self.assertIsNone(sc.parse_sicherung(raw), raw)


class ParserKabel(unittest.TestCase):
    def test_liest(self):
        faelle = [("5x2,5 mm²", 5, 2.5), ("3x1,5 mm²", 3, 1.5), ("3 × 2,5 mm²", 3, 2.5), ("5x16mm2", 5, 16), ("3x4 mm²", 3, 4),
                  ("NYM-J 3x2,5 mm²", 3, 2.5), ("NYY-J 5x16 mm²", 5, 16), ("NYY-J  5x6   mm²", 5, 6)]
        for raw, adern, q in faelle:
            with self.subTest(raw=raw):
                k = sc.parse_kabel(raw)
                self.assertIsNotNone(k)
                self.assertEqual((k.adern, k.querschnitt_mm2), (adern, q))

    def test_freitext_ist_none(self):
        for raw in ["", "   ", "foo", "5 mm²", "NYM-J", "NYM-J mm²"]:
            self.assertIsNone(sc.parse_kabel(raw), raw)


class Mindestquerschnitt(unittest.TestCase):
    def test_katalogwerte(self):
        # 6..16 A -> 1,5 ; 20 -> 2,5 ; 25 -> 4 ; 32 -> 6 ; 40 -> 10 ; 63 -> 16 mm²
        for a, q in [(6, 1.5), (10, 1.5), (16, 1.5), (20, 2.5), (25, 4), (32, 6), (40, 10), (63, 16), (35, 6), (80, 25), (100, 35)]:
            self.assertEqual(sc.mindest_querschnitt_mm2(a), q, a)
        self.assertIsNone(sc.mindest_querschnitt_mm2(250))
        self.assertIsNone(sc.mindest_querschnitt_mm2(0))


class VorschlagTests(unittest.TestCase):
    def v(self, erwartet, *args, **kw):
        got = sc.vorschlag(*args, **kw)
        self.assertEqual((got.funktion, got.sicherung, got.kabel, got.phasen), erwartet)

    def test_standardwerte(self):
        self.v(("Steckdose", "30mA/B16A", "3x2,5 mm²", 1), "Steckdose")
        self.v(("Licht", "30mA/B10A", "3x1,5 mm²", 1), "Licht")
        self.v(("Gerät", "B16A", "3x1,5 mm²", 1), "Gerät")
        self.v(("Steckdose", "B16A", "3x2,5 mm²", 1), "Steckdose", vorgeschalteter_fi=True)
        self.v(("Herd", "B16A", "5x2,5 mm²", 3), "Herd")

    def test_wallbox(self):
        self.v(("Wallbox", "30mA/B16A", "5x2,5 mm²", 3), "Wallbox", 11000)
        self.v(("Wallbox", "30mA/B32A", "NYY-J 5x6 mm²", 3), "Wallbox", 22000)
        self.assertEqual(sc.vorschlag("Wallbox", 11000, vorgeschalteter_fi=True).sicherung, "B16A")
        self.assertEqual(sc.vorschlag("Wallbox", 22000, vorgeschalteter_fi=True).sicherung, "B32A")

    def test_wallbox_vorschlag_ist_rcd_konform(self):
        v = sc.vorschlag("Wallbox", 22000)
        k = sc.Kreis(nummer="W", funktion="Wallbox", sicherung=v.sicherung, kabel=v.kabel, phasen=v.phasen, leistung_va=22000, drehstrom=True)
        self.assertNotIn("rcd-fehlt", codes(sc.pruefe_kreis(k)))

    def test_durchlauferhitzer(self):
        self.v(("Durchlauferhitzer", "B40A", "5x10 mm²", 3), "Durchlauferhitzer", 21000, drehstrom=True)
        self.v(("Durchlauferhitzer", "B32A", "5x6 mm²", 3), "Durchlauferhitzer", 18000, drehstrom=True)

    def test_sicherheitstechnik(self):
        for f in ["RWA", "BMZ", "EMZ", "Brandschutztür"]:
            self.v((f, "B16A", "3x2,5 mm²", 1), f)
        self.v(("RWA", "B16A", "5x2,5 mm²", 3), "RWA", drehstrom=True)

    def test_drehstrom_und_bemessung(self):
        self.v(("Gerät", "C32A", "5x6 mm²", 3), "Gerät", 20000, drehstrom=True)
        self.assertEqual(sc.vorschlag("Gerät", 5000).sicherung, "B25A")  # Ib = 5000/230 = 21,7 A


class Regeln(unittest.TestCase):
    def kreis(self, **kw):
        basis = dict(nummer="F1", funktion="Steckdose", sicherung="30mA/B16A", kabel="3x2,5 mm²", phasen=1, leistung_va=1000, elemente=2, raeume=["Wohnen"])
        basis.update(kw)
        return sc.Kreis(**basis)

    def test_sauberer_kreis_ohne_befund(self):
        self.assertEqual(codes(sc.pruefe_kreis(self.kreis())), [])

    def test_ueberlast(self):
        self.assertIn("ueberlast", codes(sc.pruefe_kreis(self.kreis(leistung_va=4000))))
        self.assertNotIn("ueberlast", codes(sc.pruefe_kreis(self.kreis(leistung_va=4000, phasen=3, kabel="5x2,5 mm²"))))

    def test_kabel_zu_klein(self):
        self.assertIn("kabel-zu-klein", codes(sc.pruefe_kreis(self.kreis(sicherung="30mA/B32A", kabel="3x2,5 mm²", leistung_va=100))))

    def test_querschnitt_nicht_geprueft(self):
        self.assertIn("querschnitt-nicht-geprueft", codes(sc.pruefe_kreis(self.kreis(kabel="Freitext"))))
        self.assertIn("querschnitt-nicht-geprueft", codes(sc.pruefe_kreis(self.kreis(sicherung="NH2/400A", kabel="5x16 mm²"))))

    def test_rcd_fehlt_und_gruppenschutz(self):
        self.assertIn("rcd-fehlt", codes(sc.pruefe_kreis(self.kreis(sicherung="B16A"))))
        self.assertNotIn("rcd-fehlt", codes(sc.pruefe_kreis(self.kreis(sicherung="B16A", gruppen_rcd="FI 30mA"))))
        self.assertNotIn("rcd-fehlt", codes(sc.pruefe_kreis(self.kreis(sicherung="B16A", bauteil="RCD 30mA"))))
        # Steckdosen ueber 32 A sind nicht RCD-pflichtig nach 411.3.3 a)
        self.assertNotIn("rcd-fehlt", codes(sc.pruefe_kreis(self.kreis(sicherung="C40A", kabel="3x10 mm²"))))

    def test_rcd_ohne_personenschutz(self):
        c = codes(sc.pruefe_kreis(self.kreis(sicherung="B16A", gruppen_rcd="FI 300mA")))
        self.assertIn("rcd-ohne-personenschutz", c)
        self.assertNotIn("rcd-fehlt", c)

    def test_fi_verboten(self):
        self.assertIn("fi-verboten", codes(sc.pruefe_kreis(self.kreis(funktion="RWA", sicherung="B16A", gruppen_rcd="FI 300mA", elemente=1))))
        self.assertNotIn("fi-verboten", codes(sc.pruefe_kreis(self.kreis(funktion="BMZ", sicherung="B16A", elemente=1))))

    def test_phasen_widerspruch(self):
        self.assertIn("phasen-widerspruch", codes(sc.pruefe_kreis(self.kreis(drehstrom=True, phasen=1))))

    def test_zu_viele_steckdosen(self):
        self.assertIn("zu-viele-steckdosen", codes(sc.pruefe_kreis(self.kreis(elemente=11))))

    def test_eigener_stromkreis(self):
        self.assertIn("eigener-stromkreis", codes(sc.pruefe_kreis(self.kreis(funktion="Waschmaschine", elemente=2))))

    def test_gemischte_raeume(self):
        self.assertIn("gemischte-raeume", codes(sc.pruefe_kreis(self.kreis(raeume=["A", "B", "C", "D"]))))

    def test_nassraum(self):
        # Geraet ohne RCD im Bad: Hinweis; mit 30-mA-Gruppen-RCD nicht.
        self.assertIn("nassraum-rcd", codes(sc.pruefe_kreis(self.kreis(funktion="Gerät", sicherung="B16A", raeume=["Bad EG"], elemente=1))))
        self.assertNotIn("nassraum-rcd", codes(sc.pruefe_kreis(self.kreis(funktion="Gerät", sicherung="B16A", raeume=["Bad EG"], elemente=1, gruppen_rcd="FI 30mA"))))
        # Steckdose ohne RCD im Bad meldet rcd-fehlt, nicht zusaetzlich nassraum
        c = codes(sc.pruefe_kreis(self.kreis(sicherung="B16A", raeume=["Bad"])))
        self.assertIn("rcd-fehlt", c)
        self.assertNotIn("nassraum-rcd", c)

    def test_fi_klumpen(self):
        kreise = [self.kreis(nummer=f"F{i}", sicherung="B16A", gruppen_rcd="FI 30mA") for i in range(7)]
        self.assertIn("fi-klumpen", codes(sc.pruefe_verzeichnis(kreise)))
        self.assertNotIn("fi-klumpen", codes(sc.pruefe_verzeichnis(kreise[:6])))
        # Kreise mit eigener FI/LS-Kombi zaehlen nicht mit
        eigen = [self.kreis(nummer=f"F{i}", sicherung="30mA/B16A", gruppen_rcd="FI 30mA") for i in range(7)]
        self.assertNotIn("fi-klumpen", codes(sc.pruefe_verzeichnis(eigen)))


class Eingabe(unittest.TestCase):
    def test_csv_mit_semikolon_und_komma(self):
        a = sc.lies_csv(sc.BEISPIEL_CSV)
        self.assertEqual(len(a), 12)
        self.assertEqual(a[3].funktion, "Herd")
        self.assertTrue(a[3].drehstrom)
        self.assertEqual(a[2].raeume, ["Schlafen", " Kind 1", " Kind 2", " Arbeiten"])
        b = sc.lies_csv("nummer,funktion,sicherung,kabel,phasen,leistung_va,elemente,raeume,drehstrom,gruppen_rcd\nF1,Licht,B10A,3x1.5 mm2,1,500,4,Flur,nein,FI 30mA\n")
        self.assertEqual(b[0].kabel, "3x1.5 mm2")

    def test_vorlage_ist_lesbar(self):
        self.assertEqual(len(sc.lies_csv(sc.VORLAGE_CSV)), 1)

    def test_json(self):
        k = sc.lies_json(json.dumps([{"nummer": "F1", "funktion": "Licht", "sicherung": "B10A", "kabel": "3x1,5 mm²", "phasen": 1, "leistung_va": 500, "elemente": 4, "raeume": ["Flur"], "drehstrom": False, "gruppen_rcd": "FI 30mA"}]))
        self.assertEqual(k[0].funktion, "Licht")
        self.assertEqual(codes(sc.pruefe_verzeichnis(k)), [])


class Kommandozeile(unittest.TestCase):
    def run_(self, *args):
        return subprocess.run([sys.executable, str(Path(__file__).parent / "stromkreis_check.py"), *args],
                              capture_output=True, text=True, encoding="utf-8", check=True).stdout

    def test_beispiel(self):
        out = self.run_("--beispiel")
        self.assertIn("STROMKREISVERZEICHNIS GEPRÜFT", out)
        self.assertIn("bimwired.com", out)

    def test_json(self):
        d = json.loads(self.run_("--beispiel", "--json"))
        self.assertEqual(d["stromkreise"], 12)
        self.assertTrue(any(b["code"] == "fi-verboten" for b in d["befunde"]))

    def test_vorschlag(self):
        self.assertIn("30mA/B16A", self.run_("--vorschlag", "Steckdose", "2300"))


if __name__ == "__main__":
    unittest.main()
