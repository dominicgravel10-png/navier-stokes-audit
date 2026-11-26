import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_validation import MAIN_THEOREMS, STANDARD_AXIOMS

BASE = Path(__file__).resolve().parents[1] / "preuves" / "execution-13"


class HistoricalExecution13Tests(unittest.TestCase):
    def test_archived_hashes_match(self):
        expected = {}
        for line in (BASE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            expected[name] = digest
        self.assertEqual(set(expected), {"certificat.json", "axioms.json"})
        for name, digest in expected.items():
            actual = hashlib.sha256((BASE / name).read_bytes()).hexdigest()
            self.assertEqual(actual, digest)

    def test_historical_axiom_snapshot_has_exact_nine_theorems(self):
        report = json.loads((BASE / "axioms.json").read_text(encoding="utf-8"))
        self.assertEqual(set(report["theoremes"]), set(MAIN_THEOREMS))
        for entry in report["theoremes"].values():
            self.assertTrue(set(entry["axiomes"]) <= STANDARD_AXIOMS)
            self.assertEqual(entry["hors_standard"], [])
        certificate = json.loads((BASE / "certificat.json").read_text(encoding="utf-8"))
        self.assertEqual(certificate["verdict_1_certification_lean"]["verdict"], "CERTIFIÉ")
        self.assertEqual(certificate["empreintes_sha256"]["axioms.json"], hashlib.sha256((BASE / "axioms.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
