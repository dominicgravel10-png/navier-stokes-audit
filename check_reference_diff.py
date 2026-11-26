#!/usr/bin/env python3
"""Contrôle indépendant de la transformation faite par make_reference.py.

Usage : check_reference_diff.py ORIGINAL_NAVIERSTOKES.lean EUCLIDEAN.lean 3D.lean REFERENCE.lean RAPPORT.json

Le fichier REFERENCE.lean compilé par le workflow doit être l'énoncé DeepMind ORIGINAL,
modifié seulement par les transformations mécaniques annoncées. Ce script ne réutilise
pas le code de make_reference.py : il compare ligne à ligne les deux fichiers (lignes
vides ignorées) et classe chaque différence. Toute différence hors de la liste blanche
fait échouer le contrôle (code 1).

Différences autorisées :
  * retrait de `import FormalConjecturesUtil`, ajout de `import NavierStokes.ComparatorSolution` ;
  * ajout des deux notations ℝ^ et ℝ³, identiques à celles de DeepMind sauf `scoped[…]` → `local` ;
  * `namespace NavierStokes` → `namespace AuditRef`, `end NavierStokes` → `end AuditRef` ;
  * lignes d'attributs dont seuls les items `category …` et `AMS …` ont été retirés ;
  * retrait complet des stubs (A) et (B) (docstring, attributs, énoncé, `sorry`) ;
  * remplacement du `sorry` de (C) et (D) par les preuves de transfert attendues, mot pour mot ;
  * ajout des deux `#print axioms AuditRef.…` et de leur commentaire.
Les énoncés de (C) et (D) et toutes les définitions doivent rester identiques au caractère près.
"""
import difflib
import json
import re
import sys

PROOF_C = """obtain ⟨u₀, f, hu, hf, hno⟩ := NavierStokes.Comparator.navier_stokes_breakdown_R3 nu hnu
refine ⟨u₀, f, ?_, ?_, ?_⟩
· exact { div_free := hu.div_free, smooth := hu.smooth, decay := hu.decay }
· exact { smooth := hf.smooth, decay := hf.decay }
· rintro ⟨v, p, h⟩
exact hno ⟨v, p,
{ navier_stokes := h.navier_stokes
div_free := h.div_free
initial_condition := h.initial_condition
velocity_smooth := h.velocity_smooth
pressure_smooth := h.pressure_smooth
integrable := h.integrable
globally_bounded_energy := h.globally_bounded_energy }⟩"""

PROOF_D = """obtain ⟨u₀, f, hu, hf, hno⟩ := NavierStokes.Comparator.navier_stokes_breakdown_periodic nu hnu
refine ⟨u₀, f, ?_, ?_, ?_⟩
· exact { div_free := hu.div_free, smooth := hu.smooth, isOnePeriodic := hu.isOnePeriodic }
· exact { smooth := hf.smooth, isOnePeriodic := hf.isOnePeriodic, decay := hf.decay }
· rintro ⟨v, p, h⟩
exact hno ⟨v, p,
{ navier_stokes := h.navier_stokes
div_free := h.div_free
initial_condition := h.initial_condition
velocity_smooth := h.velocity_smooth
pressure_smooth := h.pressure_smooth
isOnePeriodic_velocity := h.isOnePeriodic_velocity
isOnePeriodic_pressure := h.isOnePeriodic_pressure }⟩"""

TRAILER = [
    "-- Axiomes : seuls propext, Classical.choice et Quot.sound sont acceptés.",
    "#print axioms AuditRef.navier_stokes_breakdown_R3",
    "#print axioms AuditRef.navier_stokes_breakdown_periodic",
]
STUBS = ("navier_stokes_existence_and_smoothness_R3",
         "navier_stokes_existence_and_smoothness_periodic")


def lines_of(path):
    """Lignes non vides, sans espaces de fin, avec leur numéro d'origine."""
    out = []
    for i, line in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
        if line.strip():
            out.append((i, line.rstrip()))
    return out


def notation(path, symbol):
    for line in open(path, encoding="utf-8"):
        if re.match(r'^\s*scoped\[[^\]]*\]\s+notation\s+"' + re.escape(symbol) + '"', line):
            return re.sub(r"^\s*scoped\[[^\]]*\]\s+", "local ", line.rstrip())
    raise SystemExit(f"Notation {symbol} introuvable dans {path}")


def stub_lines(orig):
    """Indices (dans la liste filtrée) des lignes des stubs (A) et (B)."""
    idx = set()
    texts = [t for _, t in orig]
    for name in STUBS:
        hits = [k for k, t in enumerate(texts) if re.match(rf"^theorem {name}\b", t)]
        if len(hits) != 1:
            raise SystemExit(f"Stub {name} introuvable ou ambigu dans l'original")
        k = hits[0]
        start = k
        while start > 0 and (texts[start - 1].startswith("@[") or texts[start - 1].startswith("/--")
                             or (texts[start - 1].endswith("-/") and "/--" in texts[start - 1])):
            start -= 1
        end = k
        while texts[end].strip() != "sorry":
            end += 1
        idx.update(range(start, end + 1))
    return idx


def cleaned_attr(o, n):
    """`n` est-il `o` privé seulement de ses items category/AMS ?"""
    m = re.fullmatch(r"(\s*)@\[([^\]]*)\]", o)
    if not m:
        return False
    keep = [i.strip() for i in m.group(2).split(",")
            if i.strip() and not re.match(r"^(category\b|AMS\b)", i.strip())]
    expected = f"{m.group(1)}@[{', '.join(keep)}]" if keep else None
    return n == expected


def main():
    orig_p, eucl_p, d3_p, ref_p, out_p = sys.argv[1:6]
    orig, ref = lines_of(orig_p), lines_of(ref_p)
    ot, rt = [t for _, t in orig], [t for _, t in ref]
    stubs = stub_lines(orig)
    notations = {notation(eucl_p, "ℝ^"), notation(d3_p, "ℝ³")}
    proofs = [[l.strip() for l in PROOF_C.splitlines()], [l.strip() for l in PROOF_D.splitlines()]]

    problems, allowed = [], []
    used = {"import": 0, "notations": set(), "ns": 0, "end": 0, "proofs": [], "trailer": 0}

    sm = difflib.SequenceMatcher(a=ot, b=rt, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        dels, ins = list(range(i1, i2)), rt[j1:j2]
        # 1) suppressions autorisées
        rest_dels = []
        for k in dels:
            t = ot[k]
            if k in stubs:
                allowed.append(f"stub retiré : {t}")
            elif t in ("import FormalConjecturesUtil", "namespace NavierStokes", "end NavierStokes"):
                allowed.append(f"remplacé : {t}")
            elif t.strip() == "sorry":
                allowed.append("sorry de (C)/(D) remplacé")
            else:
                rest_dels.append(k)
        # attributs nettoyés : appariement dans l'ordre
        ins_left = list(ins)
        for k in list(rest_dels):
            if ins_left and cleaned_attr(ot[k], ins_left[0]):
                allowed.append(f"attribut nettoyé : {ot[k]} → {ins_left[0]}")
                rest_dels.remove(k)
                ins_left.pop(0)
            elif cleaned_attr(ot[k], None):
                allowed.append(f"attribut retiré entièrement (category/AMS seuls) : {ot[k]}")
                rest_dels.remove(k)
        for k in rest_dels:
            problems.append(f"ligne {orig[k][0]} de l'original supprimée ou modifiée : {ot[k]}")
        # 2) insertions autorisées
        buf = []
        for t in ins_left:
            s = t.strip()
            if t == "import NavierStokes.ComparatorSolution":
                used["import"] += 1
            elif t in notations:
                used["notations"].add(t)
            elif t == "namespace AuditRef":
                used["ns"] += 1
            elif t == "end AuditRef":
                used["end"] += 1
            elif t in TRAILER:
                used["trailer"] += 1
            else:
                buf.append(s)
        if buf:
            if buf in proofs:
                used["proofs"].append(proofs.index(buf))
                allowed.append(f"preuve de transfert {'CD'[proofs.index(buf)]} insérée")
            else:
                for s in buf:
                    problems.append(f"ligne insérée non autorisée : {s}")

    if used["import"] != 1: problems.append("import NavierStokes.ComparatorSolution absent ou multiple")
    if used["notations"] != notations: problems.append("notations ℝ^/ℝ³ absentes ou différentes de DeepMind")
    if used["ns"] != 1 or used["end"] != 1: problems.append("espace de noms AuditRef incorrect")
    if sorted(used["proofs"]) != [0, 1]: problems.append("preuves de transfert (C) et (D) absentes ou dupliquées")
    if used["trailer"] != len(TRAILER): problems.append("#print axioms AuditRef.* absents")
    if any(t.strip() == "sorry" or re.search(r"\bsorry\b", t) for t in rt): problems.append("un sorry subsiste")
    for name in ("navier_stokes_breakdown_R3", "navier_stokes_breakdown_periodic"):
        if sum(1 for t in rt if re.match(rf"^theorem {name}\b", t)) != 1:
            problems.append(f"énoncé {name} absent ou dupliqué")

    report = {"ok": not problems, "problemes": problems, "differences_autorisees": allowed}
    with open(out_p, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
