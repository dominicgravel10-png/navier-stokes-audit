import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_validation import (
    CLASSICAL_THEOREMS,
    MAIN_THEOREMS,
    parse_manifest,
    validate_axioms_report,
    validate_commit_record,
    validate_reference_diff_report,
    validate_reference_exact_report,
    validate_autotest_report,
    verify_manifest,
    validate_installer_evidence,
    EXPECTED_ELAN_SOURCE,
)


class ValidationRegressionTests(unittest.TestCase):
    def test_bare_ok_true_is_not_a_reference_certificate(self):
        self.assertTrue(validate_reference_diff_report({"ok": True}))
        self.assertTrue(validate_reference_exact_report({"ok": True}))
        self.assertTrue(validate_axioms_report({"ok": True}, MAIN_THEOREMS))
        self.assertTrue(validate_autotest_report({"ok": True}))

    def test_fake_manifest_and_wrong_digest_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "tracked.txt").write_text("real input\n", encoding="utf-8")
            digest = "0" * 64
            self.assertTrue(verify_manifest(root, f"{digest}  tracked.txt\n", {"tracked.txt"}, set()))
            self.assertTrue(parse_manifest("invalid manifest fake\n")[1])

    def test_duplicate_manifest_paths_are_rejected(self):
        line = "a" * 64 + "  tracked.txt\n"
        _, errors = parse_manifest(line + line)
        self.assertTrue(errors)

    def test_zero_or_unbound_audit_commit_is_rejected(self):
        record = (
            "OPENAI=f9e8bc5b38b6e212696e8a30e3e91517af887bbd\n"
            "DEEPMIND=8bf45ed70d48b2b2a501de9c00b26bfa38c573ee\n"
            "AUDIT=" + "0" * 40 + "\n"
        )
        actual = {
            "OPENAI": "f9e8bc5b38b6e212696e8a30e3e91517af887bbd",
            "DEEPMIND": "8bf45ed70d48b2b2a501de9c00b26bfa38c573ee",
            "AUDIT": "1" * 40,
        }
        self.assertTrue(validate_commit_record(record, actual, "0" * 40))

    def test_installer_source_and_digest_are_bound_to_pinned_script(self):
        script = b"#!/bin/sh\necho elan\n"
        checksum = hashlib.sha256(script).hexdigest() + "  elan-init.sh\n"
        self.assertEqual(validate_installer_evidence(EXPECTED_ELAN_SOURCE, script, checksum, "elan installed"), [])
        self.assertTrue(validate_installer_evidence("https://example.invalid/elan.sh", script, checksum, "elan installed"))
        self.assertTrue(validate_installer_evidence(EXPECTED_ELAN_SOURCE, script, "0" * 64 + "  elan-init.sh", "elan installed"))

    def test_theorem_report_rejects_missing_extra_and_nonstandard_axiom(self):
        expected = sorted(MAIN_THEOREMS)
        report = {
            "schema_version": 2,
            "expected_theoremes": expected,
            "axiomes_autorises": ["Classical.choice", "Quot.sound", "propext"],
            "theoremes": {
                theorem: {"axiomes": ["Classical.choice", "Quot.sound", "propext"], "hors_standard": []}
                for theorem in MAIN_THEOREMS
            },
            "sorry": False,
            "erreurs_lean": 0,
            "journaux_sha256": {"reference.log": "a" * 64},
            "problemes": [],
            "ok": True,
        }
        self.assertEqual(validate_axioms_report(report, MAIN_THEOREMS), [])
        report["axiomes_autorises"].append("sorryAx")
        self.assertTrue(validate_axioms_report(report, MAIN_THEOREMS))
        report["axiomes_autorises"].remove("sorryAx")
        del report["theoremes"][MAIN_THEOREMS[0]]
        self.assertTrue(validate_axioms_report(report, MAIN_THEOREMS))
        report["theoremes"][MAIN_THEOREMS[0]] = {"axiomes": ["sorryAx"], "hors_standard": []}
        self.assertTrue(validate_axioms_report(report, MAIN_THEOREMS))
        report["theoremes"][MAIN_THEOREMS[0]] = {"axiomes": ["Classical.choice", "Quot.sound", "propext"], "hors_standard": []}
        report["theoremes"]["Audit.injected_theorem"] = {"axiomes": [], "hors_standard": []}
        self.assertTrue(validate_axioms_report(report, MAIN_THEOREMS))

    def test_classical_theorem_allowlist_is_separate_and_exact(self):
        combined = list(MAIN_THEOREMS) + list(CLASSICAL_THEOREMS)
        self.assertTrue(validate_axioms_report({"ok": True}, combined))

    def test_reference_reports_reject_fake_hashes_and_nonempty_problem_claims(self):
        report = {
            "schema_version": 1,
            "ok": True,
            "problemes": [],
            "differences_autorisees": ["modification mécanique"],
            "source_sha256": "a" * 64,
            "generated_sha256": "b" * 64,
        }
        self.assertEqual(validate_reference_diff_report(report), [])
        report["generated_sha256"] = "fake"
        self.assertTrue(validate_reference_diff_report(report))
        exact = {k: v for k, v in report.items() if k != "differences_autorisees"}
        exact["generated_sha256"] = "b" * 64
        exact["problemes"] = ["un changement non autorisé"]
        self.assertTrue(validate_reference_exact_report(exact))

    def test_autotest_requires_all_ten_named_negative_cases(self):
        report = {
            "schema_version": 1,
            "ok": True,
            "authentique_accepte": True,
            "cas": [],
            "nombre_falsifications": 10,
        }
        self.assertTrue(validate_autotest_report(report))

    def test_full_v2_counterexample_cannot_certify_in_v3(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            logs = root / "journaux"
            logs.mkdir()
            (logs / "commits.txt").write_text(
                "OPENAI=f9e8bc5b38b6e212696e8a30e3e91517af887bbd\n"
                "DEEPMIND=8bf45ed70d48b2b2a501de9c00b26bfa38c573ee\n"
                "AUDIT=" + "0" * 40 + "\n", encoding="utf-8"
            )
            (logs / "lean-version.txt").write_text("Lean (version 4.34.0-rc2, fake build)\n", encoding="utf-8")
            for name in ("axioms.json", "reference-diff.json", "reference-exact.json"):
                (logs / name).write_text('{"ok":true}\n', encoding="utf-8")
            (logs / "sources.sha256").write_text("invalid manifest fake\n", encoding="utf-8")
            for name in ("Reference.lean", "reference.diff", "reference-diff-autotest.log", "extraits-enonce.txt", "lemme-8-6.txt"):
                (logs / name).write_text("fake\n", encoding="utf-8")
            env = os.environ.copy()
            for key in ("CACHE", "BUILD", "REFDIFF", "REFERENCE", "BRIDGE", "CLASSICAL", "AXIOMS"):
                env[key] = "success"
            env.update({
                "GITHUB_ACTIONS": "true",
                "GITHUB_REPOSITORY": "dominicgravel10-png/navier-stokes-audit",
                "GITHUB_SERVER_URL": "https://github.com",
                "GITHUB_RUN_ID": "99999999999",
                "GITHUB_SHA": "0" * 40,
            })
            verdict = Path(__file__).resolve().parents[1] / "verdict.py"
            result = subprocess.run([sys.executable, "-I", "-B", str(verdict), str(logs)], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            certificate = json.loads((logs / "certificat.json").read_text(encoding="utf-8"))
            self.assertNotEqual(certificate["verdict_1_certification_lean"]["verdict"], "CERTIFIÉ")


if __name__ == "__main__":
    unittest.main()
