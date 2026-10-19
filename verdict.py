#!/usr/bin/env python3
"""Deux verdicts séparés et un certificat à empreintes SHA-256.

Usage : verdict.py DOSSIER_JOURNAUX   (issues des étapes par variables d'environnement)

VERDICT 1 — Certification formelle Lean (machine)
  ERREUR D'INFRASTRUCTURE   cache ou compilation d'OpenAI en échec : aucune conclusion
  ÉCART D'ÉNONCÉ            l'énoncé DeepMind recompilé ne se déduit pas du théorème
                            d'OpenAI par transfert champ par champ : les définitions
                            ne coïncident pas à égalité définitionnelle près
  ERREUR DU LEMME D'AUDIT   notre pont ne compile pas : défaut de l'audit, pas d'OpenAI
  AXIOME NON STANDARD       sorryAx, Lean.ofReduceBool ou axiome déclaré : hypothèse cachée
  CERTIFIÉ                  toutes les vérifications noyau ont réussi

VERDICT 2 — Correspondance avec le texte Clay (Fefferman)
  Jamais certifiable par machine. Toujours « À VALIDER HUMAINEMENT ».
"""
import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

logs = pathlib.Path(sys.argv[1])
keys = ("TEXTE", "TEXTE_CONTOURNEMENT", "CACHE", "BUILD", "REFERENCE", "BRIDGE", "AXIOMS")
o = {k: (os.environ.get(k) or "skipped") for k in keys}

if o["BUILD"] != "success":
    lean, nature = "ERREUR D'INFRASTRUCTURE", "technique : aucune conclusion mathématique"
elif o["REFERENCE"] != "success":
    lean, nature = "ÉCHEC DU TRANSFERT (CAUSE INDÉTERMINÉE)", ("Le transfert n’a pas abouti : examiner reference.log "
                                     "pour distinguer erreur technique, syntaxique ou écart mathématique")
elif o["BRIDGE"] != "success":
    lean, nature = "ERREUR DU LEMME D'AUDIT", "technique, dans notre fichier : OpenAI non mis en cause"
elif o["AXIOMS"] != "success":
    lean, nature = "CONTRÔLE DES AXIOMES NON VALIDÉ", "Examiner axioms.json et axioms.log : axiome, erreur ou sortie absente"
else:
    lean, nature = "CERTIFIÉ", "toutes les vérifications noyau ont réussi"

avertissements = []
if o["TEXTE"] != "success":
    avertissements.append("Comparaison textuelle des définitions : différences (voir definitions.json)")
if o["TEXTE_CONTOURNEMENT"] != "success":
    avertissements.append("Recherche textuelle : occurrences suspectes (voir contournement.txt) ; "
                          "le contrôle décisif reste #print axioms")

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
            "2_enonce_deepmind_par_transfert": o["REFERENCE"],
            "3_pont_regularite_bord": o["BRIDGE"],
            "4_axiomes_noyau": o["AXIOMS"],
        },
        "avertissements_indicatifs": avertissements,
    },
    "verdict_2_correspondance_clay": {
        "verdict": "À VALIDER HUMAINEMENT",
        "points": [
            "Fidélité de l'énoncé DeepMind au texte de Fefferman, clause par clause",
            "Condition d'énergie (7) : extraits-enonce.txt",
            "Périodicité de la pression, alternative (D) seulement : extraits-enonce.txt",
        ],
    },
    "hors_portee": [
        "Correspondance entre la preuve écrite (PDF) et la preuve Lean, "
        "dont le lemme 8.6 / éq. (8.19) : lemme-8-6.txt",
        "Relecture du noyau par un vérificateur indépendant (nanoda)",
    ],
    "commits": commits,
    "lean": (logs / "lean-version.txt").read_text().strip()
    if (logs / "lean-version.txt").exists() else None,
    "execution": {
        "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "github_run": f"{os.environ.get('GITHUB_SERVER_URL', '')}/"
                      f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
                      f"{os.environ.get('GITHUB_RUN_ID', '')}",
    },
    "empreintes_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(logs.iterdir()) if p.is_file() and p.name != "certificat.json"
    },
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
        for a in avertissements:
            fh.write(f"\n> ⚠ {a}\n")
        fh.write("\n# Verdict 2 — correspondance Clay : À VALIDER HUMAINEMENT\n\n")
        for pt in cert["verdict_2_correspondance_clay"]["points"]:
            fh.write(f"- {pt}\n")
        fh.write("\n**Hors portée :**\n")
        for pt in cert["hors_portee"]:
            fh.write(f"- {pt}\n")

sys.exit(0 if lean == "CERTIFIÉ" else 1)
