#!/usr/bin/env python3
"""Deux verdicts séparés et un certificat à empreintes SHA-256.

Usage : verdict.py DOSSIER_JOURNAUX   (statuts des étapes par variables d'environnement)

Statuts possibles d'une étape : success, failed, skipped (non exécutée).

VERDICT 1 — Certification formelle Lean (machine)
  ERREUR D'INFRASTRUCTURE            compilation d'OpenAI exécutée et échouée
  TRANSFORMATION DE RÉFÉRENCE REJETÉE  contrôle exécuté et transformation non autorisée détectée
  CONTRÔLE DE TRANSFORMATION NON VALIDÉ  vérificateur/autotest en échec sans différence établie
  ÉCHEC DU TRANSFERT (CAUSE INDÉTERMINÉE)  compilation du transfert exécutée et échouée
  ERREUR DU LEMME D'AUDIT            compilation de BoundaryBridge exécutée et échouée
  CONTRÔLE DES AXIOMES NON VALIDÉ    contrôle exécuté et axiome/sorry/erreur détecté
  PREUVES D'EXÉCUTION INSUFFISANTES  étape non exécutée, statut invalide ou pièce manquante
  CERTIFIÉ                           tout a réussi ET les pièces sont présentes et cohérentes

Complément (sans effet sur le verdict 1) : ClassicalBoundary.lean, pont classique (C) et (D).
Ses théorèmes sont aussi soumis au contrôle des axiomes quand il compile.

VERDICT 2 — Correspondance avec le texte Clay (Fefferman)
  Jamais certifiable par machine. Toujours « À VALIDER HUMAINEMENT ».
"""
import hashlib
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

EXPECTED_COMMITS = {
    "OPENAI": "f9e8bc5b38b6e212696e8a30e3e91517af887bbd",
    "DEEPMIND": "8bf45ed70d48b2b2a501de9c00b26bfa38c573ee",
}
EXPECTED_LEAN = "4.34.0-rc2"

logs = pathlib.Path(sys.argv[1])
keys = ("CACHE", "BUILD", "REFDIFF", "REFERENCE", "BRIDGE", "CLASSICAL", "AXIOMS")
valid_statuses = {"success", "failed", "skipped"}
o = {}
for key in keys:
    value = os.environ.get(key) or "skipped"
    o[key] = value if value in valid_statuses else "invalid"


def lire_json(nom):
    return json.loads((logs / nom).read_text(encoding="utf-8"))


if o["BUILD"] == "failed":
    lean, nature = "ERREUR D'INFRASTRUCTURE", "la compilation complète a été exécutée et a échoué"
elif o["BUILD"] != "success":
    lean, nature = "PREUVES D'EXÉCUTION INSUFFISANTES", f"compilation complète : étape {o['BUILD']}"
elif o["REFDIFF"] == "failed":
    reports = []
    for name in ("reference-diff.json", "reference-exact.json"):
        try:
            reports.append(lire_json(name))
        except (OSError, ValueError, TypeError):
            reports.append(None)
    if any(isinstance(report, dict) and report.get("ok") is False for report in reports):
        lean, nature = ("TRANSFORMATION DE RÉFÉRENCE REJETÉE",
                        "un rapport a détecté une différence non autorisée : examiner les rapports de référence")
    else:
        lean, nature = ("CONTRÔLE DE TRANSFORMATION NON VALIDÉ",
                        "un vérificateur ou son autotest a échoué sans rapport de différence exploitable")
elif o["REFDIFF"] != "success":
    lean, nature = "PREUVES D'EXÉCUTION INSUFFISANTES", f"contrôle de transformation : étape {o['REFDIFF']}"
elif o["REFERENCE"] == "failed":
    lean, nature = ("ÉCHEC DU TRANSFERT (CAUSE INDÉTERMINÉE)",
                    "examiner reference.log : erreur technique, syntaxique ou écart mathématique")
elif o["REFERENCE"] != "success":
    lean, nature = "PREUVES D'EXÉCUTION INSUFFISANTES", f"compilation du transfert : étape {o['REFERENCE']}"
elif o["BRIDGE"] == "failed":
    lean, nature = "ERREUR DU LEMME D'AUDIT", "technique, dans notre fichier : OpenAI non mis en cause"
elif o["BRIDGE"] != "success":
    lean, nature = "PREUVES D'EXÉCUTION INSUFFISANTES", f"pont de régularité : étape {o['BRIDGE']}"
elif o["AXIOMS"] == "failed":
    lean, nature = "CONTRÔLE DES AXIOMES NON VALIDÉ", "examiner axioms.json et axioms.log"
elif o["AXIOMS"] != "success":
    lean, nature = "PREUVES D'EXÉCUTION INSUFFISANTES", f"contrôle des axiomes : étape {o['AXIOMS']}"
else:
    lean, nature = "CERTIFIÉ", "toutes les vérifications noyau ont réussi et les pièces sont cohérentes"

# Pièces justificatives : un « CERTIFIÉ » sans preuves d'exécution n'est pas un certificat.
if lean == "CERTIFIÉ":
    pieces = []
    try:
        ids = dict(l.split("=", 1) for l in (logs / "commits.txt").read_text().split() if "=" in l)
        for key, value in EXPECTED_COMMITS.items():
            if ids.get(key) != value:
                pieces.append(f"révision incorrecte ou absente : {key}")
        if not re.fullmatch(r"[0-9a-f]{40}", ids.get("AUDIT", "")):
            pieces.append("révision du dépôt d'audit absente")
        if EXPECTED_LEAN not in (logs / "lean-version.txt").read_text():
            pieces.append("version de Lean non attestée")
        ax = lire_json("axioms.json")
        if ax.get("ok") is not True or ax.get("sorry") or ax.get("erreurs_lean"):
            pieces.append("axioms.json ne valide pas le contrôle")
        if lire_json("reference-diff.json").get("ok") is not True:
            pieces.append("reference-diff.json ne valide pas les transformations")
        if lire_json("reference-exact.json").get("ok") is not True:
            pieces.append("reference-exact.json ne valide pas la comparaison exacte")
        required_files = (
            "Reference.lean", "reference.diff", "reference-diff-autotest.log",
            "sources.sha256", "extraits-enonce.txt", "lemme-8-6.txt",
        )
        for name in required_files:
            path = logs / name
            if not path.is_file() or path.stat().st_size == 0:
                pieces.append(f"pièce absente ou vide : {name}")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        pieces.append(f"lecture des pièces impossible : {type(exc).__name__}")
    if pieces:
        lean, nature = "PREUVES D'EXÉCUTION INSUFFISANTES", " ; ".join(pieces)

complement = {
    "success": "COMPILÉ — pont classique (C) et (D) établi ; axiomes standard, y compris 5 maillons de la chaîne d'OpenAI",
    "failed": "ÉCHEC — défaut du fichier d'audit, sans effet sur le verdict 1 (voir classical.log)",
    "skipped": "NON EXÉCUTÉ",
}.get(o["CLASSICAL"], o["CLASSICAL"])

commits = {}
if (logs / "commits.txt").exists():
    commits = dict(l.split("=", 1) for l in (logs / "commits.txt").read_text().split() if "=" in l)

cert = {
    "verdict_1_certification_lean": {
        "verdict": lean,
        "nature": nature,
        "etapes": {
            "cache_mathlib": o["CACHE"],
            "1_compilation_complete": o["BUILD"],
            "2a_controle_transformation_reference": o["REFDIFF"],
            "2b_enonce_deepmind_par_transfert": o["REFERENCE"],
            "3_pont_regularite_bord": o["BRIDGE"],
            "4_axiomes_noyau": o["AXIOMS"],
        },
    },
    "complement_pont_classique_C_D": complement,
    "verdict_2_correspondance_clay": {
        "verdict": "À VALIDER HUMAINEMENT",
        "points": [
            "Fidélité de l'énoncé DeepMind au texte de Fefferman, clause par clause",
            "Condition d'énergie (7) : extraits-enonce.txt",
            "Périodicité de la pression, alternative (D) seulement : extraits-enonce.txt",
            "Identification C^∞(ℝ³ × [0, ∞)) ⇔ prolongement lisse (théorème de Seeley), non formalisée",
        ],
    },
    "hors_portee": [
        "Correspondance entre la preuve écrite (PDF) et la preuve Lean, "
        "dont le lemme 8.6 / éq. (8.19) : lemme-8-6.txt",
        "Relecture du noyau par un vérificateur indépendant (nanoda)",
    ],
    "commits": commits,
    "lean": (logs / "lean-version.txt").read_text().strip().splitlines()[-1]
    if (logs / "lean-version.txt").exists() and (logs / "lean-version.txt").read_text().strip() else None,
    "execution": {
        "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "github_run": f"{os.environ.get('GITHUB_SERVER_URL', '')}/"
                      f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
                      f"{os.environ.get('GITHUB_RUN_ID', '')}",
    },
    "empreintes_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(logs.iterdir()) if p.is_file() and p.name != "certificat.json"
    } if logs.is_dir() else {},
}

(logs / "certificat.json").write_text(json.dumps(cert, ensure_ascii=False, indent=2))
print(json.dumps(cert, ensure_ascii=False, indent=2))

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    v1 = cert["verdict_1_certification_lean"]
    with open(summary, "a", encoding="utf-8") as fh:
        fh.write(f"# Verdict 1 — certification Lean : {lean}\n\n*Nature :* {nature}\n\n")
        fh.write("| Étape | Issue |\n|---|---|\n")
        for k, val in v1["etapes"].items():
            fh.write(f"| {k} | {val} |\n")
        fh.write(f"\n**Complément — pont classique (C) et (D) :** {complement}\n")
        fh.write("\n# Verdict 2 — correspondance Clay : À VALIDER HUMAINEMENT\n\n")
        for pt in cert["verdict_2_correspondance_clay"]["points"]:
            fh.write(f"- {pt}\n")
        fh.write("\n**Hors portée :**\n")
        for pt in cert["hors_portee"]:
            fh.write(f"- {pt}\n")

sys.exit(0 if lean == "CERTIFIÉ" else 1)
