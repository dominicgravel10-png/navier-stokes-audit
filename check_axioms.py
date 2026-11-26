#!/usr/bin/env python3
"""Vérifie la sortie de `#print axioms`.

Usage : check_axioms.py [--avec-classique] RAPPORT.json JOURNAL.log [JOURNAL.log ...]

  --avec-classique : exige aussi les théorèmes de ClassicalBoundary.lean (AuditClassical.*)
                     et les 5 maillons de la chaîne d'OpenAI qui y sont imprimés

Réussit seulement si :
  * chaque théorème attendu apparaît dans les journaux ;
  * chacun ne dépend que de propext, Classical.choice, Quot.sound (ou d'aucun axiome) ;
  * aucun journal ne contient d'avertissement « declaration uses sorry » (guillemets
    droits ou accents graves) ni d'erreur Lean ;
  * si un théorème apparaît plusieurs fois, l'UNION de ses axiomes est contrôlée.
"""
import json
import re
import sys

STANDARD = {"propext", "Classical.choice", "Quot.sound"}
EXPECTED = [
    "NavierStokes.Comparator.navier_stokes_breakdown_R3",
    "NavierStokes.Comparator.navier_stokes_breakdown_periodic",
    "Audit.uniqueDiffOn_halfspace",
    "Audit.contDiffOn_of_extension",
    "Audit.smooth_field_of_extension",
    "Audit.ExtensionSolution.toLean",
    "Audit.breakdown_R3_extension_version",
    "AuditRef.navier_stokes_breakdown_R3",
    "AuditRef.navier_stokes_breakdown_periodic",
]
CLASSICAL = [
    "AuditClassical.differentiable_time_slice",
    "AuditClassical.derivWithin_Ici_eq_deriv",
    "AuditClassical.ClassicalSolutionR3.toLean",
    "AuditClassical.breakdown_R3_classical",
    "AuditClassical.ClassicalSolutionPeriodic.toLean",
    "AuditClassical.breakdown_periodic_classical",
    # Maillons de la chaîne d'OpenAI (complément, sans effet sur le verdict 1)
    "NavierStokesR3.WholeSpaceUniqueness.classical_uniqueness_on_Icc",
    "NavierStokesR3.WholeSpaceUniqueness.candidate_global_agrees_before_one",
    "NavierStokesR3.ProblemStatement.CandidateProperties.no_global_solution_one",
    "NavierStokesR3.theorem_1_1",
    "NavierStokesR3.comparator_of_breakdown",
]
SORRY_WARNING = re.compile(r"declaration uses ['`‘’]sorry['`‘’]")
# `#print axioms` est calculé par Lean sur la fermeture complète des dépendances
# vérifiées par le noyau. Il révèle `sorryAx` (tout sorry), `Lean.ofReduceBool`
# (native_decide) et tout axiome déclaré par l'utilisateur.

DEPENDS = re.compile(r"'([^']+)' depends on axioms: \[([^\]]*)\]")
NONE = re.compile(r"'([^']+)' does not depend on any axioms")


def main():
    args = sys.argv[1:]
    expected = list(EXPECTED)
    if args and args[0] == "--avec-classique":
        expected += CLASSICAL
        args = args[1:]
    out_path, logs = args[0], args[1:]
    if not logs:
        sys.exit("aucun journal fourni")
    text = "\n".join(open(p, encoding="utf-8", errors="replace").read() for p in logs)
    # Les messages longs sont parfois coupés sur plusieurs lignes.
    flat = re.sub(r"\s*\n\s*", " ", text)

    found = {}
    for name, axioms in DEPENDS.findall(flat):
        found.setdefault(name, set()).update(a.strip() for a in axioms.split(",") if a.strip())
    for name in NONE.findall(flat):
        found.setdefault(name, set())
    found = {k: sorted(v) for k, v in found.items()}

    report = {"theoremes": {}, "sorry": bool(SORRY_WARNING.search(flat)),
              "erreurs_lean": len(re.findall(r"\berror:", text)), "ok": True}
    for name in expected:
        if name not in found:
            report["theoremes"][name] = "ABSENT DU JOURNAL"
            report["ok"] = False
            continue
        extra = sorted(set(found[name]) - STANDARD)
        report["theoremes"][name] = {"axiomes": found[name], "hors_standard": extra}
        if extra:
            report["ok"] = False
    if report["sorry"] or report["erreurs_lean"]:
        report["ok"] = False

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
