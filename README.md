# Audit indépendant — Navier–Stokes, alternative (C)

Audit de la formalisation Lean publiée par OpenAI le 8 septembre 2026
(`openai/NavierStokesAndEuler`, commit `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`).

Auteur : Dominic Gravel — ORCID [0009-0004-2819-2902](https://orcid.org/0009-0004-2819-2902).
Rédigé avec l'assistance de Claude (Anthropic).

## Question posée

Le théorème Lean `NavierStokes.Comparator.navier_stokes_breakdown_R3` implique-t-il
l'alternative (C) du problème du millénaire, sans hypothèse cachée ?

## Deux verdicts séparés

Un succès informatique ne doit pas être présenté comme une preuve plus large que ce
qui a été contrôlé. Le certificat contient donc deux verdicts distincts :

1. **Certification formelle Lean** — décidée par la machine.
2. **Correspondance avec le texte Clay (Fefferman)** — toujours
   « À VALIDER HUMAINEMENT » : aucune machine ne peut comparer un texte en langue
   naturelle à un énoncé formel.

## Verdict 1 : ce que vérifie la machine

Le flux `.github/workflows/certification.yml` exécute, à chaque envoi :

| # | Vérification | Niveau |
|---|---|---|
| 1 | `lake build` : toutes les cibles du `lakefile.toml` (NavierStokes, Euler, ComparatorChallenges), Lean 4.34.0-rc2, dépendances verrouillées par `lake-manifest.json` | noyau |
| 2 | L'énoncé ORIGINAL de DeepMind (`formal-conjectures`, commit `8bf45ed`, écrit avant la preuve) est recompilé, et ses alternatives (C) et (D) sont prouvées par transfert champ par champ depuis les théorèmes d'OpenAI | noyau |
| 3 | Le pont de régularité au bord `Audit/BoundaryBridge.lean` compile | noyau |
| 4 | `#print axioms` sur tous les théorèmes : uniquement `propext`, `Classical.choice`, `Quot.sound` | noyau |

### Pourquoi l'étape 2 remplace une comparaison de texte

Le script `scripts/make_reference.py` ne fait que des transformations mécaniques du
fichier DeepMind (import, espace de noms `AuditRef`, notations recopiées de leurs
propres fichiers, attributs de catalogage retirés) et remplace le `sorry` de (C) et
(D) par un transfert : chaque champ de la structure DeepMind reçoit le champ
correspondant de la structure d'OpenAI. Lean n'accepte ce transfert que si les deux
champs sont **définitionnellement égaux**. Une seule différence de sens (par exemple
`Ici 0` contre `Ioi 0`) fait échouer la compilation. Le diff exact du fichier généré
contre l'original est conservé dans `reference.diff`.

La comparaison textuelle et la recherche de `sorry` par `grep` restent présentes,
mais seulement comme **avertissements indicatifs**.

### Pourquoi `#print axioms` est le contrôle décisif

`#print axioms` parcourt la fermeture complète des dépendances vérifiées par le
noyau. Tout `sorry` y apparaît comme `sorryAx`, tout `native_decide` comme
`Lean.ofReduceBool`, tout axiome ajouté sous son nom. Les attributs
`implemented_by` et `@[extern]` n'affectent pas les preuves vérifiées par le noyau.

### Lecture du verdict 1

| Verdict | Signification |
|---|---|
| `CERTIFIÉ` | Les quatre vérifications noyau ont réussi. |
| `ÉCART D'ÉNONCÉ` | L'énoncé DeepMind ne se déduit pas de celui d'OpenAI. Lire `reference.log` : une erreur du script reste possible. |
| `AXIOME NON STANDARD` | Hypothèse cachée. |
| `ERREUR D'INFRASTRUCTURE` | Réseau, cache ou compilation. Aucune conclusion mathématique. |
| `ERREUR DU LEMME D'AUDIT` | Notre pont ne compile pas. OpenAI n'est pas mis en cause. |

## Le pont de régularité au bord

La définition Lean impose `ContDiffOn ℝ ∞ (↿v) (univ ×ˢ Ici 0)` : régularité
directement sur le demi-espace fermé `t ≥ 0`, dérivées à droite en `t = 0`.

L'alternative (C) est un énoncé de **non-existence**. Exiger moins des solutions
exclues rend l'énoncé plus fort. Il suffit donc que toute solution lisse par
extension au-delà de `t = 0` soit admissible au sens Lean.

`ExtensionSolution` énonce chaque condition séparément ((1), (2), (3), (7)) et
n'exprime la régularité (6) que par l'existence d'extensions lisses. Elle **ne
contient pas** la définition d'OpenAI. Le théorème `ExtensionSolution.toLean` doit
donc réellement établir `velocity_smooth` et `pressure_smooth` à partir des
extensions, par le lemme `smooth_field_of_extension`. **Le théorème d'extension de
Seeley n'est pas nécessaire**, et le dépôt OpenAI n'y fait aucune référence.

## Verdict 2 : correspondance avec le texte Clay

### Condition d'énergie (7)

Fefferman : `∫ |u(x,t)|² dx < C` pour tout `t ≥ 0`.
Lean : `integrable : ∀ t ≥ 0, MemLp (‖v · t‖) 2` et
`globally_bounded_energy : ∃ E, ∀ t ≥ 0, (∫ x, ‖v x t‖ ^ 2) < E`.

En Lean, l'intégrale d'une fonction non intégrable vaut 0 par convention ; sans le
champ `MemLp`, la borne serait vide de sens. Avec lui, les deux conditions réunies
équivalent à (7). **Analyse : fidèle.**

### Périodicité de la pression

Ajoutée seulement dans l'alternative (D), conformément à l'errata du document Clay.
Elle restreint la classe de solutions exclues, donc (D) formalisée est légèrement
plus faible qu'une lecture littérale. **L'alternative (C) n'est pas touchée.**

## Hors portée : la preuve écrite

Bastounis, Circelli et Hansen (arXiv:2610.08144) montrent que
`norm_derivativeWord_inverse_le` utilise `m + 5` dérivées au lieu de `m + 4`, une série
en `(1+|k₁|+|k₂|)⁻⁴` au lieu de `(1+|k|)⁻³`, et un seul multi-indice au lieu du supremum.
La version Lean est strictement plus faible que l'équation (8.19) du PDF.

C'est un écart entre la preuve écrite et la preuve Lean, pas une erreur de l'énoncé
final : le noyau a vérifié que (C) découle de ce qui a été formalisé. En revanche,
(8.19) tel qu'écrit dans le PDF n'est pas certifié par Lean. Les auteurs ne
prétendent pas que le théorème Lean est faux.

Aussi hors portée : la relecture du noyau par un vérificateur indépendant (nanoda).

## Sources

- OpenAI, *On the Navier–Stokes Millennium Prize Problem* (8 sept. 2026)
- `github.com/openai/NavierStokesAndEuler`, commit `f9e8bc5`
- `github.com/google-deepmind/formal-conjectures`, commit `8bf45ed`
- C. Fefferman, *Existence and smoothness of the Navier–Stokes equation*, Clay Mathematics Institute
- A. Bastounis, F. Circelli, A. C. Hansen, *Navier–Stokes lost in translation*, arXiv:2610.08144
