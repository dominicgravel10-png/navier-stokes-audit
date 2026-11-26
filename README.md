# Audit indépendant — Navier–Stokes, alternative (C)

Audit de la formalisation Lean publiée par OpenAI le 8 septembre 2026
(`openai/NavierStokesAndEuler`, commit `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`).

Auteur : Dominic Gravel — ORCID [0009-0004-2819-2902](https://orcid.org/0009-0004-2819-2902).
Rédigé avec l'assistance de Claude (Anthropic).

## Question posée

Le théorème Lean `NavierStokes.Comparator.navier_stokes_breakdown_R3` implique-t-il
l'alternative (C) du problème du millénaire, sans hypothèse cachée ?

## Résultat : exécution #13 du 7 novembre 2026 — CERTIFIÉ

| Élément | Valeur |
|---|---|
| Exécution | [run 42338240579](https://github.com/dominicgravel10-png/navier-stokes-audit/actions/runs/42338240579) |
| Verdict 1 (Lean) | **CERTIFIÉ** : compilation complète, transfert DeepMind (C) et (D), pont (C), 9 théorèmes limités à `propext`, `Classical.choice`, `Quot.sound` |
| Verdict 2 (Clay) | À VALIDER HUMAINEMENT |
| `certificat.json` | SHA-256 `747dac87f831fe4f9714dc3eb0b7c695fe7ced8116c2a35919e78cc9790e1f8f` |
| `axioms.json` | SHA-256 `6b51cd7c95bffa040103ccbed17f9c018614fe842cbe1e21ea1289c4a59ceef4` (inscrite dans le certificat) |

Les pièces sont archivées dans `preuves/execution-13/` (l'artefact GitHub expire le 5 février 2027).
Les deux « avertissements indicatifs » du certificat #13 renvoient à des contrôles textuels
**non exécutés** ; le `verdict.py` de l'époque les qualifiait à tort de « différences ». Corrigé en version 2.

### Version 2 (à certifier par une nouvelle exécution)

- **2a.** `check_reference_diff.py` et `check_reference_exact.py` (deux méthodes indépendantes) vérifient que le
  `Reference.lean` compilé est l'original DeepMind modifié seulement mécaniquement ;
  `test_reference_diff.py` s'assure que ce contrôle rejette 10 falsifications délibérées.
  `Reference.lean` et son diff sont conservés avec leurs empreintes.
- **Complément.** `ClassicalBoundary.lean` : solutions classiques pour (C) **et (D)**, avec des
  dérivées bilatérales (`deriv` en temps, `fderiv`, `Δ`, `gradient` en espace) de fonctions
  lisses sur `ℝ³ × ℝ` ; aucune `derivWithin`. Contrôle aussi les axiomes de 5 maillons de la
  chaîne d'OpenAI (`theorem_1_1`, `comparator_of_breakdown`…). Rapporté sans effet sur le verdict 1.
- **Pièces justificatives.** Sans commits attendus, version de Lean, JSON valides et
  `Reference.lean`, le verdict devient « PREUVES D'EXÉCUTION INSUFFISANTES ».

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
| 2a | `Reference.lean` contrôlé contre l'original DeepMind (`check_reference_diff.py`, autotest de 10 falsifications) | texte, liste blanche |
| 2b | L'énoncé ORIGINAL de DeepMind (`formal-conjectures`, commit `8bf45ed`, écrit avant la preuve) est recompilé, et ses alternatives (C) et (D) sont prouvées par transfert champ par champ depuis les théorèmes d'OpenAI | noyau |
| 3 | Le pont de régularité au bord `BoundaryBridge.lean` compile | noyau |
| 4 | `#print axioms` sur tous les théorèmes : uniquement `propext`, `Classical.choice`, `Quot.sound` | noyau |

### Pourquoi l'étape 2 remplace une comparaison de texte

Le script `make_reference.py` ne fait que des transformations mécaniques du
fichier DeepMind (import, espace de noms `AuditRef`, notations recopiées de leurs
propres fichiers, attributs de catalogage retirés) et remplace le `sorry` de (C) et
(D) par un transfert : chaque champ de la structure DeepMind reçoit le champ
correspondant de la structure d'OpenAI. Lean n'accepte ce transfert que si les deux
champs sont **définitionnellement égaux**. Une seule différence de sens (par exemple
`Ici 0` contre `Ioi 0`) fait échouer la compilation. Le diff exact du fichier généré
contre l'original est conservé dans `reference.diff`.

La version 2 rend ces contrôles bloquants : deux scripts comparent le texte transformé
à la source DeepMind, l'autotest vérifie le rejet de dix falsifications, et le contrôle
des axiomes recherche `sorry` dans les journaux Lean. Si une étape est ignorée, le
certificat indique « PREUVES D'EXÉCUTION INSUFFISANTES » ; il ne la présente pas comme
une différence détectée.

### Pourquoi `#print axioms` est le contrôle décisif

`#print axioms` parcourt la fermeture complète des dépendances vérifiées par le
noyau. Tout `sorry` y apparaît comme `sorryAx`, tout `native_decide` comme
`Lean.ofReduceBool`, tout axiome ajouté sous son nom. Les attributs
`implemented_by` et `@[extern]` n'affectent pas les preuves vérifiées par le noyau.

### Lecture du verdict 1

| Verdict | Signification |
|---|---|
| `CERTIFIÉ` | Les contrôles requis ont réussi et les pièces sont présentes et cohérentes. |
| `TRANSFORMATION DE RÉFÉRENCE REJETÉE` | Un contrôle exécuté a détecté une transformation non autorisée. |
| `CONTRÔLE DE TRANSFORMATION NON VALIDÉ` | Un vérificateur ou son autotest a échoué sans preuve exploitable d'une différence. |
| `ÉCHEC DU TRANSFERT (CAUSE INDÉTERMINÉE)` | Le transfert n'a pas compilé; une erreur technique ou un écart d'énoncé reste possible. |
| `CONTRÔLE DES AXIOMES NON VALIDÉ` | Le contrôle exécuté détecte une dépendance non standard, un théorème absent, `sorry` ou une erreur Lean. |
| `ERREUR D'INFRASTRUCTURE` | La compilation complète a été exécutée et a échoué. |
| `ERREUR DU LEMME D'AUDIT` | Notre pont a été compilé et a échoué. OpenAI n'est pas mis en cause. |
| `PREUVES D'EXÉCUTION INSUFFISANTES` | Une étape n'a pas été exécutée, son statut est invalide ou une pièce manque. |

## Le pont de régularité au bord

La définition Lean impose `ContDiffOn ℝ ∞ (↿v) (univ ×ˢ Ici 0)` : régularité
directement sur le demi-espace fermé `t ≥ 0`, dérivées à droite en `t = 0`.

L'alternative (C) est un énoncé de **non-existence**. Exiger moins des solutions
exclues rend l'énoncé plus fort. Le pont établi porte sur la classe restreinte des
solutions qui ont un prolongement lisse au-delà de `t = 0`.

`ExtensionSolution` énonce chaque condition séparément ((1), (2), (3), (7)) et
n'exprime la régularité (6) que par l'existence d'extensions lisses. Elle **ne
contient pas** la définition d'OpenAI. Le théorème `ExtensionSolution.toLean` établit
`velocity_smooth` et `pressure_smooth` à partir de ces extensions, par le lemme
`smooth_field_of_extension`. Seeley n'est donc pas requis pour cette classe définie
par l'existence d'un prolongement lisse. En revanche, l'audit ne formalise pas ici
l'équivalence entre cette classe et toutes les fonctions lisses C∞ sur le demi-espace
fermé du texte de Fefferman. Ce passage reste à établir pour la correspondance complète
avec l'énoncé Clay. Le dépôt OpenAI n'invoque pas le théorème de Seeley.

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
