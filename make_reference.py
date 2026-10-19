#!/usr/bin/env python3
"""Fabrique `AuditRef/Reference.lean` à partir du fichier ORIGINAL de DeepMind.

Usage : make_reference.py FC_NAVIERSTOKES.lean FC_EUCLIDEAN.lean FC_3D.lean SORTIE.lean

Transformations mécaniques, et seulement celles-ci :
  * `import FormalConjecturesUtil` → `import NavierStokes.ComparatorSolution`
    (apporte Mathlib et le théorème d'OpenAI) ;
  * les notations ℝ^ et ℝ³, que DeepMind importe de ses propres fichiers, sont
    recopiées depuis ces fichiers (scoped → local) ;
  * `namespace NavierStokes` → `namespace AuditRef` (pour ne pas entrer en collision
    avec les définitions d'OpenAI) ;
  * les attributs de catalogage `category …` et `AMS …` sont retirés ;
  * les stubs (A) et (B) sont supprimés ; le `sorry` de (C) et (D) est remplacé par un
    transfert champ par champ depuis les théorèmes d'OpenAI.

Le noyau Lean vérifie alors que chaque champ de l'énoncé DeepMind coïncide, à
égalité définitionnelle près, avec le champ correspondant chez OpenAI. Une seule
différence de sens fait échouer la compilation.
"""
import re
import sys

PROOF_C = """
  obtain ⟨u₀, f, hu, hf, hno⟩ := NavierStokes.Comparator.navier_stokes_breakdown_R3 nu hnu
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
        globally_bounded_energy := h.globally_bounded_energy }⟩
"""

PROOF_D = """
  obtain ⟨u₀, f, hu, hf, hno⟩ := NavierStokes.Comparator.navier_stokes_breakdown_periodic nu hnu
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
        isOnePeriodic_pressure := h.isOnePeriodic_pressure }⟩
"""


def notation_line(path, symbol):
    for line in open(path, encoding="utf-8"):
        if re.match(r'^\s*scoped\[[^\]]*\]\s+notation\s+"' + re.escape(symbol) + '"', line):
            return re.sub(r"^\s*scoped\[[^\]]*\]\s+", "local ", line.rstrip())
    sys.exit(f"Notation {symbol} introuvable dans {path}")


def clean_attributes(text):
    def fix(m):
        items = [i.strip() for i in m.group(1).split(",")]
        items = [i for i in items if i and not re.match(r"^(category\b|AMS\b)", i)]
        return f"@[{', '.join(items)}]" if items else ""
    return re.sub(r"@\[([^\]]*)\]", fix, text)


def theorem_span(text, name):
    """Début (docstring incluse) et fin (après `sorry`) d'un théorème stub."""
    start = text.index(f"theorem {name} ")
    doc = text.rfind("/--", 0, start)
    if doc != -1 and "-/" in text[doc:start] and text[text.index("-/", doc) + 2:start].strip() == "":
        start = doc
    end = text.index("sorry", start) + len("sorry")
    return start, end


def main():
    src_path, eucl_path, d3_path, out_path = sys.argv[1:5]
    text = open(src_path, encoding="utf-8").read()

    assert text.count("import FormalConjecturesUtil") == 1
    text = text.replace("import FormalConjecturesUtil", "import NavierStokes.ComparatorSolution")

    notations = notation_line(eucl_path, "ℝ^") + "\n" + notation_line(d3_path, "ℝ³") + "\n"
    assert text.count("open scoped Laplacian\n") == 1
    text = text.replace("open scoped Laplacian\n", "open scoped Laplacian\n\n" + notations)

    assert text.count("namespace NavierStokes\n") == 1 and text.count("end NavierStokes") == 1
    text = text.replace("namespace NavierStokes\n", "namespace AuditRef\n")
    text = text.replace("end NavierStokes", "end AuditRef")

    text = clean_attributes(text)

    for name in ("navier_stokes_existence_and_smoothness_R3",
                 "navier_stokes_existence_and_smoothness_periodic"):
        s, e = theorem_span(text, name)
        text = text[:s] + text[e:]

    for name, proof in (("navier_stokes_breakdown_R3", PROOF_C),
                        ("navier_stokes_breakdown_periodic", PROOF_D)):
        s, e = theorem_span(text, name)
        block = text[s:e]
        assert block.rstrip().endswith("by\n  sorry") or re.search(r":= by\s+sorry$", block)
        block = re.sub(r"\s*sorry$", proof.rstrip(), block)
        text = text[:s] + block + text[e:]

    assert "sorry" not in text, "un sorry subsiste"
    text += (
        "\n-- Axiomes : seuls propext, Classical.choice et Quot.sound sont acceptés.\n"
        "#print axioms AuditRef.navier_stokes_breakdown_R3\n"
        "#print axioms AuditRef.navier_stokes_breakdown_periodic\n"
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"Écrit : {out_path}")


if __name__ == "__main__":
    main()
