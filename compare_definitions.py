#!/usr/bin/env python3
"""Compare, déclaration par déclaration, les définitions Lean utilisées par OpenAI
avec la référence indépendante de Google DeepMind (formal-conjectures).

Usage : compare_definitions.py REFERENCE.lean OPENAI_DEFS.lean OPENAI_SOLUTION.lean RAPPORT.json
        [FICHIERS_DE_NOTATION_IMPORTES.lean ...]

Ce qui est ignoré (différences sans contenu mathématique) :
  commentaires, docstrings, attributs @[...], imports, en-têtes `namespace`/`end`,
  `open`, mot-clé `local` devant `notation`, espaces.
Ce qui est comparé :
  chaque `structure`, `def`, `abbrev`, `lemma`/`theorem` prouvé et `notation` ;
  l'énoncé des alternatives (C) et (D) contre le stub de la référence.
Code de sortie 0 seulement si tout concorde.
"""
import json
import re
import sys

DECL_START = re.compile(
    r"^(?:noncomputable\s+|private\s+|protected\s+)*"
    r"(structure|def|abbrev|lemma|theorem|instance|class|inductive)\s+([^\s(:{\[]+)"
)
NOTATION = re.compile(r"^(?:local\s+)?(?:scoped(?:\[[^\]]*\])?\s+)?(?:notation|infix[lr]?|prefix|postfix)\b(.*)$")
TOP_LEVEL = re.compile(
    r"^(?:@\[|/--|/-!|namespace\b|end\b|open\b|section\b|variable\b|import\b|set_option\b|"
    r"(?:local\s+)?(?:scoped(?:\[[^\]]*\])?\s+)?(?:notation|infix|prefix|postfix)\b|"
    r"(?:noncomputable\s+|private\s+|protected\s+)*(?:structure|def|abbrev|lemma|theorem|instance|class|inductive)\b|#)"
)


def strip_comments(src: str) -> str:
    # commentaires de bloc (y compris docstrings), imbriqués
    out, depth, i = [], 0, 0
    while i < len(src):
        if src.startswith("/-", i):
            depth += 1
            i += 2
        elif depth and src.startswith("-/", i):
            depth -= 1
            i += 2
        elif depth:
            i += 1
        else:
            out.append(src[i])
            i += 1
    text = "".join(out)
    text = re.sub(r"--[^\n]*", "", text)
    text = re.sub(r"@\[[^\]]*\]", "", text)
    return text


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse(path: str):
    text = strip_comments(open(path, encoding="utf-8").read())
    lines = text.split("\n")
    decls, notations, current = {}, {}, None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        top = not line.startswith((" ", "\t")) and TOP_LEVEL.match(stripped)
        if top:
            current = None
            m = DECL_START.match(stripped)
            n = NOTATION.match(stripped)
            if m:
                current = m.group(2)
                decls[current] = [stripped]
            elif n:
                body = norm(n.group(1))
                key = re.search(r'"([^"]+)"', body)
                notations[key.group(1) if key else body] = body
            continue
        if current:
            decls[current].append(stripped)
    return {k: norm(" ".join(v)) for k, v in decls.items()}, notations


def statement_only(block: str) -> str:
    """Partie énoncé d'un théorème : tout ce qui précède le `:=` final."""
    cut = block.split(":= by")[0].split(":=")[0]
    return norm(cut)


def main():
    ref_path, defs_path, sol_path, out_path = sys.argv[1:5]
    ref_decls, ref_not = parse(ref_path)
    our_decls, our_not = parse(defs_path)
    sol_decls, _ = parse(sol_path)

    report = {"declarations": {}, "notations": {}, "enonces": {}, "ok": True}

    # 1. Définitions et structures (on ignore les stubs `sorry` de la référence)
    for name, body in ref_decls.items():
        is_stub = "sorry" in body
        if is_stub:
            continue
        if name not in our_decls:
            report["declarations"][name] = "ABSENTE chez OpenAI"
            report["ok"] = False
        elif our_decls[name] != body:
            report["declarations"][name] = {"reference": body, "openai": our_decls[name]}
            report["ok"] = False
        else:
            report["declarations"][name] = "identique"
    for name in our_decls:
        if name not in ref_decls:
            report["declarations"][name] = "AJOUTÉE par OpenAI (absente de la référence)"
            report["ok"] = False

    # 2. Notations
    for key, body in ref_not.items():
        if our_not.get(key) == body:
            report["notations"][key] = "identique"
        else:
            report["notations"][key] = {"reference": body, "openai": our_not.get(key)}
            report["ok"] = False

    # 3. Énoncés (C) et (D) : stub de la référence contre théorème prouvé
    for name in ("navier_stokes_breakdown_R3", "navier_stokes_breakdown_periodic"):
        ref = ref_decls.get(name)
        sol = sol_decls.get(name)
        if ref is None or sol is None:
            report["enonces"][name] = "INTROUVABLE"
            report["ok"] = False
            continue
        a, b = statement_only(ref), statement_only(sol)
        if a == b:
            report["enonces"][name] = "identique"
        else:
            report["enonces"][name] = {"reference": a, "openai": b}
            report["ok"] = False

    # 4. Notations importées par la référence depuis d'autres fichiers (ex. ℝ^)
    for extra in sys.argv[5:]:
        _, extra_not = parse(extra)
        for key, body in extra_not.items():
            if key in our_not:
                same = our_not[key] == body
                report["notations"][key + " (importée)"] = (
                    "identique" if same else {"reference": body, "openai": our_not[key]}
                )
                report["ok"] &= same

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
