#!/usr/bin/env python3
"""Autotest de check_reference_diff.py : le contrôle doit ACCEPTER le Reference.lean
réellement généré et REJETER chacune des falsifications ci-dessous.

Usage : test_reference_diff.py CHECKER.py ORIGINAL.lean EUCLIDEAN.lean 3D.lean REFERENCE.lean
Code de sortie 0 seulement si tous les cas se comportent comme attendu.
"""
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
    r = subprocess.run([sys.executable, "-I", checker, orig, eucl, d3, ref, str(tmp / "r.json")],
                       capture_output=True)
    return r.returncode == 0


def main():
    checker, orig, eucl, d3, ref = sys.argv[1:6]
    src = pathlib.Path(ref).read_text(encoding="utf-8")
    failures = 0
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        ok = run(checker, orig, eucl, d3, ref, tmp)
        print(f"{'OK ' if ok else 'ÉCHEC'} fichier authentique accepté")
        failures += not ok
        for label, (a, b) in MUTATIONS.items():
            if a not in src:
                print(f"ÉCHEC mutation inapplicable : {label}")
                failures += 1
                continue
            m = tmp / "mut.lean"
            m.write_text(src.replace(a, b, 1), encoding="utf-8")
            rejected = not run(checker, orig, eucl, d3, str(m), tmp)
            print(f"{'OK ' if rejected else 'ÉCHEC'} falsification rejetée : {label}")
            failures += not rejected
    print(f"{failures} échec(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
