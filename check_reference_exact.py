#!/usr/bin/env python3
"""Contrôle EXACT (version d'octobre 2026) : `make_reference.py` n'a pas changé le sens de l'énoncé DeepMind.

Second contrôle, indépendant de check_reference_diff.py (méthode différente : on défait
les transformations puis on exige l'égalité caractère par caractère).

Usage : check_reference_exact.py ORIGINAL.lean GENERE.lean FC_EUCLIDEAN.lean FC_3D.lean RAPPORT.json

Méthode : on défait, dans le fichier généré, les seules transformations autorisées,
puis on exige l'égalité EXACTE (caractère par caractère) avec l'original, après avoir
appliqué à l'original les deux seules suppressions autorisées.

Transformations autorisées, et rien d'autre :
  1. ligne d'import remplacée ;
  2. ajout des notations ℝ^ et ℝ³, recopiées des fichiers DeepMind (scoped → local) ;
  3. `namespace NavierStokes` / `end NavierStokes` renommés en `AuditRef` ;
  4. attributs `category …` et `AMS …` retirés ;
  5. stubs (A) et (B) supprimés en entier ;
  6. dans (C) et (D), le seul mot `sorry` remplacé par une preuve ;
  7. lignes `#print axioms` ajoutées à la fin.
Toute autre différence, même d'un caractère, fait échouer le contrôle.
"""
import json
import re
import sys


def strip_attrs(text):
    def fix(m):
        items = [i.strip() for i in m.group(1).split(",")]
        items = [i for i in items if i and not re.match(r"^(category\b|AMS\b)", i)]
        return f"@[{', '.join(items)}]" if items else ""
    return re.sub(r"@\[([^\]]*)\]", fix, text)


def remove_theorem(text, name):
    start = text.index(f"theorem {name} ")
    doc = text.rfind("/--", 0, start)
    if doc != -1 and text[text.index("-/", doc) + 2:start].strip() == "":
        start = doc
    end = text.index("sorry", start) + len("sorry")
    return text[:start] + text[end:]


def expected_notation(path, symbol):
    for line in open(path, encoding="utf-8"):
        if re.match(r'^\s*scoped\[[^\]]*\]\s+notation\s+"' + re.escape(symbol) + '"', line):
            return re.sub(r"^\s*scoped\[[^\]]*\]\s+", "local ", line.rstrip())
    raise SystemExit(f"notation {symbol} introuvable dans {path}")


def main():
    orig_p, gen_p, eucl_p, d3_p, out_p = sys.argv[1:6]
    orig = open(orig_p, encoding="utf-8").read()
    gen = open(gen_p, encoding="utf-8").read()
    problems = []

    # Côté original : seules suppressions autorisées (4 et 5).
    exp = strip_attrs(orig)
    for name in ("navier_stokes_existence_and_smoothness_R3",
                 "navier_stokes_existence_and_smoothness_periodic"):
        exp = remove_theorem(exp, name)

    # Côté généré : défaire 1, 2, 3, 6, 7.
    g = gen
    if g.count("import NavierStokes.ComparatorSolution") != 1:
        problems.append("ligne d'import inattendue")
    g = g.replace("import NavierStokes.ComparatorSolution", "import FormalConjecturesUtil", 1)

    notations = [expected_notation(eucl_p, "ℝ^"), expected_notation(d3_p, "ℝ³")]
    block = "\n".join(notations) + "\n\n"
    if g.count(block) != 1:
        problems.append("notations ajoutées absentes ou différentes des fichiers DeepMind")
    g = g.replace(block, "", 1)

    g = g.replace("namespace AuditRef\n", "namespace NavierStokes\n", 1)
    g = g.replace("end AuditRef", "end NavierStokes", 1)

    # 6 : chaque preuve de (C)/(D) va de la ligne qui suit `:= by` jusqu'à la
    # prochaine ligne vide ; elle est remplacée par `  sorry`.
    for name in ("navier_stokes_breakdown_R3", "navier_stokes_breakdown_periodic"):
        i = g.index(f"theorem {name} ")
        j = g.index(":= by\n", i) + len(":= by\n")
        k = g.index("\n\n", j)
        proof = g[j:k]
        if "sorry" in proof or "axiom" in proof:
            problems.append(f"preuve de {name} suspecte")
        g = g[:j] + "  sorry" + g[k:]

    # 7 : lignes finales #print axioms et commentaire associé.
    tail = re.search(r"\n\n-- Axiomes :[^\n]*\n(#print axioms [^\n]+\n)+$", g)
    if not tail:
        problems.append("fin de fichier inattendue")
    else:
        g = g[:tail.start()] + "\n"

    identical = g == exp
    if not identical:
        a, b = exp.splitlines(), g.splitlines()
        for n, (x, y) in enumerate(zip(a, b), 1):
            if x != y:
                problems.append(f"ligne {n} : attendu {x!r}, obtenu {y!r}")
                break
        else:
            problems.append(f"longueurs différentes : {len(a)} contre {len(b)} lignes")

    report = {"ok": identical and not problems, "problemes": problems}
    with open(out_p, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
