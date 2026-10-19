import NavierStokes.ComparatorSolution

/-!
# Audit indépendant — régularité au bord `t = 0`

Auteur de l'audit : Dominic Gravel (ORCID 0009-0004-2819-2902), avec l'aide de Claude.

Question : la définition Lean `ContDiffOn ℝ ∞ (↿v) (univ ×ˢ Ici 0)` exige-t-elle
plus, autant ou moins que « lisse par extension au-delà de t = 0 » ?

L'alternative (C) est un énoncé de NON-existence. Il suffit donc du sens
« lisse par extension ⇒ ContDiffOn sur le demi-espace » : toute solution lisse
au sens de l'extension est aussi une solution au sens Lean, donc l'exclure en Lean
l'exclut aussi au sens de l'extension. Le théorème d'extension de Seeley
(sens réciproque) n'est pas requis, et ce fichier n'en fait pas usage.

La structure `ExtensionSolution` ne contient PAS la définition d'OpenAI : elle énonce
chaque condition séparément, et sa régularité est exprimée uniquement par
l'existence d'extensions lisses. Le passage à la définition d'OpenAI (`toLean`)
doit donc réellement établir `velocity_smooth` et `pressure_smooth`.
-/

open ContDiff Set InnerProductSpace MeasureTheory Function
open scoped Laplacian

namespace Audit

local notation "ℝ³" => EuclideanSpace ℝ (Fin 3)

/-- Le demi-espace fermé admet des dérivées uniques (convexe, intérieur non vide) :
les dérivées `fderivWithin` y sont bien définies jusqu'au bord. -/
theorem uniqueDiffOn_halfspace :
    UniqueDiffOn ℝ ((univ : Set ℝ³) ×ˢ Ici (0 : ℝ)) :=
  uniqueDiffOn_univ.prod (uniqueDiffOn_Ici 0)

/-- Une fonction lisse sur tout `ℝ³ × ℝ` est lisse au sens Lean sur le demi-espace. -/
theorem contDiffOn_of_extension {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (g : ℝ³ × ℝ → E) (hg : ContDiff ℝ ∞ g) :
    ContDiffOn ℝ ∞ g ((univ : Set ℝ³) ×ˢ Ici (0 : ℝ)) :=
  hg.contDiffOn

/-- Si un champ coïncide sur le demi-espace avec une extension lisse, il est lisse
au sens Lean sur le demi-espace. -/
theorem smooth_field_of_extension {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (w : ℝ³ → ℝ → E)
    (h : ∃ W : ℝ³ × ℝ → E, ContDiff ℝ ∞ W ∧ EqOn W (↿w) ((univ : Set ℝ³) ×ˢ Ici 0)) :
    ContDiffOn ℝ ∞ (↿w) ((univ : Set ℝ³) ×ˢ Ici (0 : ℝ)) := by
  obtain ⟨W, hW, hEq⟩ := h
  exact (contDiffOn_of_extension W hW).congr (fun x hx => (hEq hx).symm)

/-- Solution sur ℝ³ au sens « lisse par extension ».
Équations (1), (2), (3) et énergie (7) énoncées séparément ; régularité (6) exprimée
seulement par des extensions lisses au-delà de `t = 0`. -/
structure ExtensionSolution (nu : ℝ) (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³)
    (v : ℝ³ → ℝ → ℝ³) (p : ℝ³ → ℝ → ℝ) : Prop where
  navier_stokes : ∀ x, ∀ t ≥ 0,
    derivWithin (v x ·) (Set.Ici 0) t + fderiv ℝ (v · t) x (v x t) =
      nu • Δ (v · t) x - gradient (p · t) x + f x t
  div_free : ∀ x, ∀ t ≥ 0, NavierStokes.Comparator.divergence (v · t) x = 0
  initial_condition : ∀ x, v x 0 = u₀ x
  velocity_ext : ∃ V : ℝ³ × ℝ → ℝ³, ContDiff ℝ ∞ V ∧ EqOn V (↿v) (univ ×ˢ Ici 0)
  pressure_ext : ∃ P : ℝ³ × ℝ → ℝ, ContDiff ℝ ∞ P ∧ EqOn P (↿p) (univ ×ˢ Ici 0)
  integrable : ∀ t ≥ 0, MemLp (‖v · t‖) 2
  globally_bounded_energy : ∃ E, ∀ t ≥ 0, (∫ x : ℝ³, ‖v x t‖ ^ 2) < E

/-- Toute solution lisse par extension est une solution au sens de la définition
d'OpenAI. Les deux champs de régularité sont établis par le lemme de bord. -/
theorem ExtensionSolution.toLean {nu : ℝ} {u₀ : ℝ³ → ℝ³} {f : ℝ³ → ℝ → ℝ³}
    {v : ℝ³ → ℝ → ℝ³} {p : ℝ³ → ℝ → ℝ} (h : ExtensionSolution nu u₀ f v p) :
    NavierStokes.Comparator.NavierStokesExistenceAndSmoothnessRn nu u₀ f v p where
  navier_stokes := h.navier_stokes
  div_free := h.div_free
  initial_condition := h.initial_condition
  velocity_smooth := smooth_field_of_extension v h.velocity_ext
  pressure_smooth := smooth_field_of_extension p h.pressure_ext
  integrable := h.integrable
  globally_bounded_energy := h.globally_bounded_energy

/-- L'alternative (C) prouvée par OpenAI exclut aussi les solutions lisses par
extension. Aucun appel à Seeley, aucun nouvel axiome. -/
theorem breakdown_R3_extension_version (nu : ℝ) (hnu : nu > 0) :
    ∃ (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³),
      NavierStokes.Comparator.InitialVelocityConditionDecay u₀ ∧
      NavierStokes.Comparator.ForceConditionDecay f ∧
      ¬ (∃ v p, ExtensionSolution nu u₀ f v p) := by
  obtain ⟨u₀, f, hu, hf, hno⟩ :=
    NavierStokes.Comparator.navier_stokes_breakdown_R3 nu hnu
  exact ⟨u₀, f, hu, hf, fun ⟨v, p, h⟩ => hno ⟨v, p, h.toLean⟩⟩

end Audit

-- Axiomes : seuls propext, Classical.choice et Quot.sound sont acceptés.
#print axioms NavierStokes.Comparator.navier_stokes_breakdown_R3
#print axioms NavierStokes.Comparator.navier_stokes_breakdown_periodic
#print axioms Audit.uniqueDiffOn_halfspace
#print axioms Audit.contDiffOn_of_extension
#print axioms Audit.smooth_field_of_extension
#print axioms Audit.ExtensionSolution.toLean
#print axioms Audit.breakdown_R3_extension_version
