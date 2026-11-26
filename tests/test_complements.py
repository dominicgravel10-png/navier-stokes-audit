"""Tests de la fusion v3 : compléments ForceWitness / EnergyBridge / ClassicalBoundary,
statut GENERATION et étapes non exécutées."""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit_validation import (  # noqa: E402
    COMPLEMENTS,
    MAIN_THEOREMS,
    STATUS_KEYS,
    expected_theorems,
    make_axioms_report,
)
import verdict  # noqa: E402

STD = "propext, Classical.choice, Quot.sound"


def axiom_lines(names, axioms=STD):
    return "\n".join(f"'{n}' depends on axioms: [{axioms}]" for n in names) + "\n"


class ComplementTests(unittest.TestCase):
    def test_declared_theorems_match_lean_print_axioms_lines(self):
        """La liste attendue de chaque complément est exactement celle de son fichier Lean."""
        for key, (lean_file, *_rest, theorems) in COMPLEMENTS.items():
            src = (ROOT / lean_file).read_text(encoding="utf-8")
            printed = re.findall(r"^#print axioms (\S+)", src, flags=re.M)
            self.assertEqual(sorted(printed), sorted(theorems), key)

    def test_every_complement_has_a_status_key(self):
        for key in COMPLEMENTS:
            self.assertIn(key, STATUS_KEYS)
        self.assertIn("GENERATION", STATUS_KEYS)

    def test_expected_theorems_extend_main_list_exactly(self):
        for key, spec in COMPLEMENTS.items():
            self.assertEqual(expected_theorems(key), list(MAIN_THEOREMS) + list(spec[4]))
        self.assertEqual(expected_theorems(None), list(MAIN_THEOREMS))

    def _report(self, key, extra_text):
        with tempfile.TemporaryDirectory() as d:
            p1, p2 = Path(d) / "main.log", Path(d) / "comp.log"
            p1.write_text(axiom_lines(MAIN_THEOREMS), encoding="utf-8")
            p2.write_text(extra_text, encoding="utf-8")
            return make_axioms_report([p1, p2], complement=key)

    def test_complement_report_accepts_exact_standard_axioms(self):
        for key, spec in COMPLEMENTS.items():
            self.assertTrue(self._report(key, axiom_lines(spec[4]))["ok"], key)

    def test_complement_report_rejects_missing_theorem(self):
        self.assertFalse(self._report("WITNESS", "")["ok"])

    def test_complement_report_rejects_sorryax(self):
        r = self._report("ENERGY", axiom_lines(COMPLEMENTS["ENERGY"][4], "propext, sorryAx"))
        self.assertFalse(r["ok"])

    def test_complement_report_rejects_unexpected_extra_theorem(self):
        r = self._report("WITNESS", axiom_lines(list(COMPLEMENTS["WITNESS"][4]) + ["AuditWitness.intrus"]))
        self.assertFalse(r["ok"])

    def test_skipped_and_failed_complements_are_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            logs = Path(d) / "journaux"
            logs.mkdir()
            for key in COMPLEMENTS:
                v, _ = verdict.verify_complement(logs, Path(d), key, "skipped")
                self.assertEqual(v, "NON EXÉCUTÉ")
                v, _ = verdict.verify_complement(logs, Path(d), key, "failed")
                self.assertTrue(v.startswith("ÉCHEC"))
                v, errs = verdict.verify_complement(logs, Path(d), key, "success")
                self.assertTrue(v.startswith("PREUVES INSUFFISANTES"), v)
                self.assertTrue(errs)

    def test_generation_failure_is_technical_not_a_rejection(self):
        status = {k: "skipped" for k in STATUS_KEYS}
        status.update(CACHE="success", BUILD="success", GENERATION="failed")
        v, _, _ = verdict.classify_main(status, [], Path("."), Path("."), {})
        self.assertEqual(v, "GÉNÉRATION DE LA RÉFÉRENCE IMPOSSIBLE")

    def test_unexecuted_steps_never_yield_a_failure_verdict(self):
        status = {k: "skipped" for k in STATUS_KEYS}
        status.update(CACHE="success", BUILD="success", GENERATION="success")
        v, _, _ = verdict.classify_main(status, [], Path("."), Path("."), {})
        self.assertEqual(v, "PREUVES D'EXÉCUTION INSUFFISANTES")


if __name__ == "__main__":
    unittest.main()
