#!/usr/bin/env python3
"""Vérifie la sortie de `#print axioms`.

Usage : check_axioms.py RAPPORT.json JOURNAL.log [JOURNAL.log ...]

Réussit seulement si :
  * chaque théorème attendu apparaît dans les journaux ;
  * chacun ne dépend que de propext, Classical.choice, Quot.sound (ou d'aucun axiome) ;
  * aucun journal ne contient « declaration uses 'sorry' » ni d'erreur Lean.
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
# `#print axioms` est calculé par Lean sur la fermeture complète des dépendances
# vérifiées par le noyau. Il révèle `sorryAx` (tout sorry), `Lean.ofReduceBool`
# (native_decide) et tout axiome déclaré par l'utilisateur.

DEPENDS = re.compile(r"'([^']+)' depends on axioms: \[([^\]]*)\]")
NONE = re.compile(r"'([^']+)' does not depend on any axioms")


def main():
    out_path, logs = sys.argv[1], sys.argv[2:]
    text = "\n".join(open(p, encoding="utf-8", errors="replace").read() for p in logs)
    # Les messages longs sont parfois coupés sur plusieurs lignes.
    flat = re.sub(r"\s*\n\s*", " ", text)

    found = {}
    for name, axioms in DEPENDS.findall(flat):
        found[name] = sorted(a.strip() for a in axioms.split(",") if a.strip())
    for name in NONE.findall(flat):
        found[name] = []

    report = {"theoremes": {}, "sorry": "sorry" in text and "declaration uses 'sorry'" in text,
              "erreurs_lean": len(re.findall(r"\berror:", text)), "ok": True}
    for name in EXPECTED:
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
