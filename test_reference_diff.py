#!/usr/bin/env python3
"""Régression permanente : le contrôle rejette dix falsifications de Reference.lean."""
import json
import pathlib
import subprocess
import sys
import tempfile

MUTATIONS = {
    "temps strict dans l'équation": ("∀ x, ∀ t ≥ 0,\n    derivWithin", "∀ x, ∀ t > 0,\n    derivWithin"),
    "axiome ajouté": ("namespace AuditRef\n", "namespace AuditRef\naxiom triche : False\n"),
    "notation ℝ³ altérée": ('local notation "ℝ³" => EuclideanSpace ℝ (Fin 3)',
                            'local notation "ℝ³" => EuclideanSpace ℝ (Fin 2)'),
    "champ d'énergie neutralisé": ("  globally_bounded_energy : ∃ E,", "  -- globally_bounded_energy : ∃ E,"),
    "énoncé (C) affaibli": ("InitialVelocityConditionDecay u₀ ∧ ForceConditionDecay f ∧",
                            "InitialVelocityConditionDecay u₀ ∧"),
    "sorry réintroduit": ("  · exact { smooth := hf.smooth, decay := hf.decay }", "  · sorry"),
    "set_option ajouté": ("namespace AuditRef\n", "namespace AuditRef\nset_option maxHeartbeats 0\n"),
    "preuve modifiée": ("integrable := h.integrable", "integrable := by exact h.integrable"),
    "#print axioms retiré": ("#print axioms AuditRef.navier_stokes_breakdown_periodic\n", ""),
    "attribut simp retiré": ("@[simp]\n", "\n"),
}


def run(checker, orig, eucl, d3, ref, tmp):
    result = subprocess.run(
        [sys.executable, "-I", checker, orig, eucl, d3, ref, str(tmp / "checker-report.json")],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.returncode == 0


def main():
    if len(sys.argv) not in (6, 7):
        raise SystemExit("Usage : test_reference_diff.py CHECKER ORIGINAL EUCLIDEAN 3D REFERENCE [RAPPORT.json]")
    checker, orig, eucl, d3, ref = sys.argv[1:6]
    report_path = pathlib.Path(sys.argv[6]) if len(sys.argv) == 7 else None
    src = pathlib.Path(ref).read_text(encoding="utf-8")
    failures = 0
    cases = []
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        accepted = run(checker, orig, eucl, d3, ref, tmp)
        print(f"{'OK ' if accepted else 'ÉCHEC'} fichier authentique accepté")
        failures += not accepted
        for label, (before, after) in MUTATIONS.items():
            if before not in src:
                print(f"ÉCHEC mutation inapplicable : {label}")
                cases.append({"nom": label, "applicable": False, "rejetee": False})
                failures += 1
                continue
            mutated = tmp / "mutated.lean"
            mutated.write_text(src.replace(before, after, 1), encoding="utf-8")
            rejected = not run(checker, orig, eucl, d3, str(mutated), tmp)
            print(f"{'OK ' if rejected else 'ÉCHEC'} falsification rejetée : {label}")
            cases.append({"nom": label, "applicable": True, "rejetee": rejected})
            failures += not rejected
    report = {
        "schema_version": 1,
        "ok": failures == 0,
        "authentique_accepte": accepted,
        "cas": cases,
        "nombre_falsifications": len(MUTATIONS),
    }
    if report_path:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{failures} échec(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
