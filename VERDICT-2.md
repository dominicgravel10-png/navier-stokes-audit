# Verdict 2 — Correspondance entre l'énoncé Lean et le texte Clay (Fefferman)

**Statut : À VALIDER HUMAINEMENT.** Projet de note pour validation humaine : ce document ne valide
rien par lui-même, ne constitue ni une validation finale ni une attribution du prix, et le verdict
automatique ne peut pas fermer ces obligations.
Auteur de l'audit : Dominic Gravel (ORCID 0009-0004-2819-2902), analyse rédigée avec l'aide de Claude ;
version fusionnée avec le contre-audit v3 du 26 novembre 2026.

Le verdict 1 (machine) établit que le théorème d'OpenAI démontre l'énoncé **DeepMind** des
alternatives (C) et (D) (`formal-conjectures` @ `8bf45ed`), sans axiome hors standard.
Le verdict 2 porte sur l'étape que la machine ne peut pas faire : cet énoncé Lean dit-il
la même chose que le texte de Fefferman ?

Texte de référence : C. L. Fefferman, *Existence and smoothness of the Navier–Stokes equation*,
Clay Mathematics Institute, avec ses errata
(https://www.claymath.org/wp-content/uploads/2022/06/navierstokes.pdf).
Définitions Lean citées : `NavierStokes/ComparatorDefinitions.lean` d'OpenAI @ `f9e8bc5`,
identiques à celles de DeepMind (vérifié par le transfert champ par champ de l'exécution #13).

## 0. Obligations ouvertes (tableau de suivi)

| Obligation | État | Pièce à examiner |
|---|---|---|
| Définition exacte de `C∞(R³ × [0,∞))` et relation au prolongement lisse utilisé dans le pont | Côté données : réglée pour le témoin (`ForceWitness.lean`, à certifier) ; côté solutions : ouverte (`HalfSpaceSmooth.lean` à écrire) | Définition Clay, `ClassicalBoundary.lean`, lemme d’extension pertinent |
| Dérivées en temps à `t=0` : dérivée unilatérale dans l’énoncé contre dérivée classique Lean | Ouverte | Définition Clay et clauses Lean de l’équation |
| Condition d’énergie (7), y compris l’intégrabilité `L²` et la borne uniforme | Formalisée en v3 (`EnergyBridge.lean`), à certifier par CI | `extraits-enonce.txt`, structure `NavierStokesExistenceAndSmoothnessRn` |
| Périodicité de la pression dans l’alternative (D), au regard de l’erratum Clay | Ouverte | `extraits-enonce.txt`, énoncé officiel et erratum |
| Fidélité complète des domaines, données initiales, force, divergence, régularité et périodicité | Ouverte | Comparaison Clay–DeepMind–OpenAI, ligne par ligne |
| Correspondance entre preuve écrite et preuve Lean, notamment lemme 8.6 / équation (8.19) | Hors certification de cette archive | `lemme-8-6.txt`, prépublication critique et versions originales |


## 1. Ce qu'il faut démontrer, et dans quel sens

(C) et (D) disent : **il existe** des données (u°, f) admissibles **pour lesquelles aucune**
solution admissible n'existe. Pour que « (C) Lean ⇒ (C) Clay », il faut deux implications de
sens opposés :

- **Données (sens Lean ⇒ Clay)** : les données fournies par Lean satisfont les exigences de Clay.
  Les conditions Lean sur les données doivent être **au moins aussi fortes** que celles de Clay.
- **Solutions (sens Clay ⇒ Lean)** : toute solution au sens de Clay est une solution au sens Lean,
  de sorte que l'exclusion Lean l'exclut aussi. La notion Lean de solution doit être
  **au plus aussi exigeante** que celle de Clay.

## 2. Alternative (C) — ℝ³, clause par clause

### 2a. Données (Lean ⇒ Clay)

| Clay | Lean (`InitialVelocityConditionDecay`, `ForceConditionDecay`) | Jugement proposé |
|---|---|---|
| u° lisse, de divergence nulle | `smooth : ContDiff ℝ ∞ u₀`, `div_free : ∀ x, ∇⬝ u₀ x = 0` | Conforme |
| (4) `\|∂ₓ^α u°(x)\| ≤ C_{αK} (1+\|x\|)^{-K}` pour tous α, K | `‖iteratedFDeriv ℝ m u₀ x‖ ≤ C/(1+‖x‖)^K` pour tous m, K | Conforme : `∂^α u°(x)` est la dérivée itérée d'ordre \|α\| appliquée à des vecteurs unitaires, donc majorée par sa norme |
| f lisse sur ℝ³ × [0, ∞) | `ContDiffOn ℝ ∞ (↿f) (univ ×ˢ Ici 0)` | Voir point A (§4) |
| (5) `\|∂ₓ^α ∂ₜ^m f\| ≤ C (1+\|x\|+t)^{-K}` sur ℝ³ × [0, ∞) | `‖iteratedFDerivWithin ℝ m (↿f) (univ ×ˢ Ici 0) (x,t)‖ ≤ C/(1+‖x‖+t)^K`, t ≥ 0 | Conforme : la dérivée itérée en (x, t) contrôle toutes les dérivées mixtes ; dérivées relatives au demi-espace, unilatérales en t = 0 |
| ν > 0, n = 3 | `hnu : nu > 0`, `ℝ³ = EuclideanSpace ℝ (Fin 3)` | Conforme |

**Témoin effectif d'OpenAI** (lu dans les sources, `R3/ComparatorBridge.lean`,
`comparator_of_breakdown`) : u° = 0, et la force est `toComparator f` avec
`ContDiff ℝ ∞ f` sur **tout** l'espace-temps et un support compact contenu dans {t > 0}.
Le support est bien contenu dans {t > 0} : `CompactPositiveTimeSupport f` est défini comme
`HasCompactSupport f ∧ tsupport f ⊆ positiveTimeDomain`, avec `positiveTimeDomain = Ioi 0 ×ˢ univ`
(`R3/ProblemStatement.lean`). Les données satisfont donc (4) et (5) quelle que soit la lecture
retenue pour « lisse sur ℝ³ × [0, ∞) ».
**v3 :** `ForceWitness.lean` démontre (C) avec ce témoin explicite, sans rien supposer de plus
(`AuditWitness.witness_R3`). À certifier par une exécution CI.

### 2b. Solutions (Clay ⇒ Lean)

| Clay | Lean (`NavierStokesExistenceAndSmoothnessRn`) | Jugement proposé |
|---|---|---|
| (1) `∂ₜuᵢ + Σⱼ uⱼ ∂ⱼuᵢ = νΔuᵢ − ∂ᵢp + fᵢ`, x ∈ ℝ³, t ≥ 0 | `derivWithin (v x ·) (Ici 0) t + fderiv ℝ (v · t) x (v x t) = ν • Δ (v · t) x − gradient (p · t) x + f x t`, t ≥ 0 | Conforme : `fderiv (v·t) x (v x t) = (v·∇)v`, `Δ` et `gradient` de Mathlib sont les opérateurs euclidiens usuels ; pour t > 0, `derivWithin` sur `Ici 0` est la dérivée ordinaire ; en t = 0, voir point C |
| (2) div u = 0, t ≥ 0 | `div_free` (trace de la jacobienne), t ≥ 0 | Conforme pour des champs lisses |
| (3) u(x, 0) = u°(x) | `initial_condition` | Conforme |
| (6) p, u ∈ C^∞(ℝ³ × [0, ∞)) | `velocity_smooth`, `pressure_smooth` : `ContDiffOn ℝ ∞` sur `univ ×ˢ Ici 0` | Voir point A |
| (7) `∫ \|u(x,t)\|² dx < C` pour tout t ≥ 0 | `integrable : MemLp (‖v · t‖) 2` et `globally_bounded_energy : ∃ E, ∀ t ≥ 0, ∫ ‖v x t‖² < E` | Conforme : (7) impose une intégrale finie, donc u(·, t) ∈ L² (mesurable car continue) ; `integrable` est explicite parce que l'intégrale de Bochner vaut 0 pour une fonction non intégrable. **v3 :** `EnergyBridge.lean` démontre l'implication à partir de (7) écrite avec l'intégrale étendue `∫⁻`, sans valeur conventionnelle (à certifier par CI) |
| — | aucune autre exigence (pas de décroissance de p, pas d'unicité) | Favorable : moins d'exigences rend l'exclusion plus forte |

## 3. Alternative (D) — ℝ³/ℤ³, clause par clause

| Clay | Lean | Jugement proposé |
|---|---|---|
| u° lisse, de divergence nulle sur ℝ³ ; (8) u°(x+eⱼ) = u°(x) | `InitialVelocityConditionPeriodic` : `smooth`, `div_free`, `isOnePeriodic` (translation par `EuclideanSpace.single i 1`) | Conforme |
| (8) f(x+eⱼ, t) = f(x, t) | `ForceConditionPeriodic.isOnePeriodic : ∀ t ≥ 0, IsOnePeriodic (f · t)` | Conforme sur t ≥ 0, seul domaine considéré |
| (9) `\|∂ₓ^α ∂ₜ^m f\| ≤ C (1+\|t\|)^{-K}` | `‖iteratedFDerivWithin … (x,t)‖ ≤ C/(1+t)^K`, t ≥ 0 | Conforme |
| (1), (2), (3) | comme pour (C) | Conforme (points A et C) |
| (10) u(x, t) = u(x+eⱼ, t) | `isOnePeriodic_velocity` | Conforme |
| (11) p, u ∈ C^∞ | `velocity_smooth`, `pressure_smooth` | Voir point A |
| Errata : p(x+eⱼ, t) = p(x, t) | `isOnePeriodic_pressure` | Voir point B |
| (pas de condition d'énergie pour (D)) | aucune | Conforme |

## 4. Points qui demandent un jugement humain

**A. Sens de « C^∞(ℝ³ × [0, ∞)) » et théorème de Seeley.** Le texte ne définit pas la
régularité sur le demi-espace fermé. Deux lectures usuelles :
(i) toutes les dérivées existent à l'intérieur et se prolongent continûment jusqu'au bord ;
(ii) restriction d'une fonction lisse sur ℝ³ × ℝ. Le théorème d'extension de Seeley les rend
équivalentes.
- *Solutions (Clay ⇒ Lean).* Lecture (ii) : démontré en Lean (`BoundaryBridge.lean`, certifié
  par #13 ; `ClassicalBoundary.lean`, compilé pour la première fois par l'exécution #15 du 26 novembre 2026, 11 théorèmes aux axiomes standard). Lecture (i) : les dérivées relatives de Mathlib
  sur un convexe d'intérieur non vide coïncident avec ces prolongements continus, ce qui donne
  `ContDiffOn` **sans** Seeley. Argument (confirmé par le contre-audit du 26 novembre) : si A est
  le prolongement continu de la dérivée intérieure, la convexité donne
  `F(y) − F(x) − A(x)(y − x) = ∫₀¹ [A(x + s(y − x)) − A(x)](y − x) ds = o(‖y − x‖)`,
  l'identité au bord s'obtenant par passage à la limite depuis l'intérieur ; on itère sur les
  dérivées successives. Non formalisé (objectif `HalfSpaceSmooth.lean`).
- *Données (Lean ⇒ Clay).* Lecture (i) : immédiate. Lecture (ii) : demande Seeley pour l'énoncé
  général, mais pas pour le témoin d'OpenAI, lisse sur tout l'espace-temps (§2a, `ForceWitness.lean`).

**B. Pression périodique dans (D).** L'énoncé Lean exige la périodicité de p, conformément aux
errata. Sans les errata, la notion Lean de solution serait plus exigeante que celle du texte
original, et (D) Lean exclurait moins de solutions. La validité de (D) repose donc sur
l'acceptation des errata comme partie de l'énoncé officiel.

La différence est substantielle (exemple du contre-audit, vérifié à la main) : u(x, t) = t e₁,
p(x, t) = −x₁, f = 0, u° = 0. Alors ∂ₜu = e₁, (u·∇)u = 0, Δu = 0, −∇p = e₁ : (1), (2), (3) sont
satisfaites, la vitesse est périodique, la pression ne l'est pas. Sans l'erratum, ce couple est
une solution admissible de (D) ; avec l'erratum, il ne l'est pas. Cela ne réfute pas (D) : cela
montre que l'erratum change la classe des solutions. D'où la priorité donnée à (C), qui n'en dépend pas.

**C. Dérivée temporelle en t = 0.** L'équation (1) est imposée en t = 0 avec la dérivée
unilatérale à droite. Pour une solution lisse au sens (i) ou (ii), elle coïncide avec la
dérivée relative `derivWithin (Ici 0)` : formalisé pour la lecture (ii) dans
`ClassicalBoundary.lean` (`derivWithin_Ici_eq_deriv`), non formalisé pour la lecture (i).

## 5. Hors de ce verdict

- Fidélité de la preuve écrite d'OpenAI à sa preuve Lean (lemme 8.6 / éq. 8.19, critique de
  Bastounis–Circelli–Hansen) : sans effet sur la validité du théorème Lean, mais hors de ce document.
- Relecture du noyau par un vérificateur indépendant.

## 6. Relectures

- **Contre-audit du 26 novembre 2026** : logique des implications validée ; concordance clause
  par clause confirmée (sous réserve du bord pour (5), (6), (9), (11)) ; erratum confirmé et
  rendu substantiel par un contre-exemple ; propriétés du témoin confirmées dans la source ;
  recommande de prioriser (C) et de formaliser A et C sans Seeley. Ne signe pas encore.

## 7. Conclusion proposée (à confirmer par un relecteur humain)

Clause par clause, l'énoncé Lean de (C) correspond au texte Clay : ses conditions sur les données
sont au moins aussi fortes, et sa notion de solution au plus aussi exigeante. Restent trois
points d'interprétation : A, la régularité au bord, sans conséquence pour le témoin effectif ;
B, les errata, pour (D) seulement ; C, la dérivée en t = 0. Aucun écart de fond n'a été relevé.

### Grille de signature du relecteur

| Point | Accord | Désaccord | Remarque |
|---|---|---|---|
| Données (C), §2a | ☐ | ☐ | |
| Solutions (C), §2b | ☐ | ☐ | |
| Clauses (D), §3 | ☐ | ☐ | |
| A — régularité au bord / Seeley | ☐ | ☐ | |
| B — errata, pression périodique | ☐ | ☐ | |
| C — dérivée en t = 0 | ☐ | ☐ | |

Relecteur : ____________________  Date : ____________

## 8. Règle de conclusion

Un futur `CERTIFIÉ` dans `certificat.json` concerne uniquement la chaîne informatique et formelle explicitement contrôlée. Il ne valide pas ce document. Le verdict 2 restera « À VALIDER HUMAINEMENT » jusqu’à ce qu’une revue mathématique indépendante documente chaque obligation, ses sources, les hypothèses exactes et les éventuels écarts.

## 9. Références de départ

- Clay Mathematics Institute, [Navier-Stokes Announcement](https://www.claymath.org/news/navier-stokes-announcement/), 11 septembre 2026; le Clay indique que le problème « appears » réglé et que son processus d’évaluation est délibérément non précipité.
- Clay Mathematics Institute, [description officielle du problème](https://www.claymath.org/millennium/navier-stokes-equation/).
- OpenAI, [On the Navier–Stokes Millennium Prize Problem](https://openai.com/index/navier-stokes-solution/), 8 septembre 2026, mise à jour le 10 septembre; annonce une preuve pour (C) et (D).
- Bastounis, Circelli et Hansen, [Navier-Stokes lost in translation](https://arxiv.org/abs/2610.08144), prépublication du 6 octobre 2026; elle conteste la correspondance entre l’argument écrit et la formalisation Lean, sans établir que le théorème Lean est faux.
- Buckmaster et Alpöge, [Finite-time blow-up for the Navier–Stokes equations](https://github.com/tristanbuckmaster/navier-stokes), dépôt rendu public le 20 novembre 2026; nouvelle revendication non forcée dont le dépôt signale que le certificat numérique n’est pas inclus et que la version patchée n’a pas été reconstruite.
