import NavierStokes.ComparatorSolution

/-!
# Audit indépendant — pont classique pour (C) et (D)

Auteur de l'audit : Dominic Gravel (ORCID 0009-0004-2819-2902), avec l'aide de Claude.

`BoundaryBridge.lean` (certifié par l'exécution #13) établit la régularité par extension,
mais son équation garde la dérivée temporelle unilatérale `derivWithin … (Ici 0)` de la
formalisation d'OpenAI, et il ne couvre que (C).

Ce fichier formule une solution **classique** : le champ de vitesse `V` et la pression `P`
sont des fonctions lisses sur tout `ℝ³ × ℝ` (régularité au sens de l'extension), et
l'équation (1) n'emploie que des dérivées classiques bilatérales : `deriv` en temps,
`fderiv`, `Δ`, `gradient` en espace. Aucune dérivée relative à un ensemble n'y figure.

On démontre que toute solution classique est une solution au sens d'OpenAI ; le seul
point non trivial est l'égalité `derivWithin (Ici 0) = deriv` pour une fonction
dérivable, qui exige l'unicité des dérivées sur `[0, ∞)` jusqu'au bord `t = 0`.
Les alternatives (C) et (D) d'OpenAI excluent donc aussi les solutions classiques.

Portée : le sens « lisse jusqu'au bord ⇒ prolongeable en fonction lisse » (Seeley)
n'est pas formalisé ici ; il n'intervient que pour identifier ces solutions classiques
aux solutions C^∞(ℝ³ × [0, ∞)) du texte de Fefferman, ce qui relève du verdict humain.
-/

open ContDiff Set InnerProductSpace MeasureTheory Function
open scoped Laplacian

namespace AuditClassical

local notation "ℝ³" => EuclideanSpace ℝ (Fin 3)

/-- Une tranche temporelle `s ↦ W (x, s)` d'une fonction lisse sur `ℝ³ × ℝ` est dérivable. -/
theorem differentiable_time_slice {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (W : ℝ³ × ℝ → E) (hW : ContDiff ℝ ∞ W) (x : ℝ³) :
    Differentiable ℝ (fun s : ℝ => W (x, s)) := by
  have hpair : ContDiff ℝ ∞ (fun s : ℝ => ((x, s) : ℝ³ × ℝ)) :=
    contDiff_const.prodMk contDiff_id
  have hslice : ContDiff ℝ ∞ (fun s : ℝ => W (x, s)) := hW.comp hpair
  exact hslice.differentiable (by simp)

/-- Pour `t ≥ 0`, la dérivée unilatérale sur `[0, ∞)` utilisée par OpenAI coïncide avec
la dérivée classique, y compris au bord `t = 0`. -/
theorem derivWithin_Ici_eq_deriv {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (W : ℝ³ × ℝ → E) (hW : ContDiff ℝ ∞ W) (x : ℝ³) {t : ℝ} (ht : 0 ≤ t) :
    derivWithin (fun s : ℝ => W (x, s)) (Ici 0) t = deriv (fun s : ℝ => W (x, s)) t :=
  (differentiable_time_slice W hW x t).derivWithin (uniqueDiffOn_Ici 0 t (Set.mem_Ici.mpr ht))

/-! ## Alternative (C) : ℝ³ -/

/-- Solution classique sur ℝ³ : équations (1), (2), (3) avec dérivées classiques,
régularité (6) par fonctions lisses sur `ℝ³ × ℝ`, énergie (7). -/
structure ClassicalSolutionR3 (nu : ℝ) (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³)
    (V : ℝ³ × ℝ → ℝ³) (P : ℝ³ × ℝ → ℝ) : Prop where
  velocity_smooth : ContDiff ℝ ∞ V
  pressure_smooth : ContDiff ℝ ∞ P
  navier_stokes : ∀ x, ∀ t ≥ 0,
    deriv (fun s : ℝ => V (x, s)) t + fderiv ℝ (fun y => V (y, t)) x (V (x, t)) =
      nu • Δ (fun y => V (y, t)) x - gradient (fun y => P (y, t)) x + f x t
  div_free : ∀ x, ∀ t ≥ 0, NavierStokes.Comparator.divergence (fun y => V (y, t)) x = 0
  initial_condition : ∀ x, V (x, 0) = u₀ x
  integrable : ∀ t ≥ 0, MemLp (fun x => ‖V (x, t)‖) 2
  globally_bounded_energy : ∃ E, ∀ t ≥ 0, (∫ x : ℝ³, ‖V (x, t)‖ ^ 2) < E

/-- Toute solution classique sur ℝ³ est une solution au sens d'OpenAI. -/
theorem ClassicalSolutionR3.toLean {nu : ℝ} {u₀ : ℝ³ → ℝ³} {f : ℝ³ → ℝ → ℝ³}
    {V : ℝ³ × ℝ → ℝ³} {P : ℝ³ × ℝ → ℝ} (h : ClassicalSolutionR3 nu u₀ f V P) :
    NavierStokes.Comparator.NavierStokesExistenceAndSmoothnessRn nu u₀ f
      (fun x t => V (x, t)) (fun x t => P (x, t)) where
  navier_stokes := fun x t ht => by
    have heq := h.navier_stokes x t ht
    rw [← derivWithin_Ici_eq_deriv V h.velocity_smooth x ht] at heq
    exact heq
  div_free := h.div_free
  initial_condition := h.initial_condition
  velocity_smooth := h.velocity_smooth.contDiffOn.congr (fun _ _ => rfl)
  pressure_smooth := h.pressure_smooth.contDiffOn.congr (fun _ _ => rfl)
  integrable := h.integrable
  globally_bounded_energy := h.globally_bounded_energy

/-- L'alternative (C) d'OpenAI exclut les solutions classiques sur ℝ³. -/
theorem breakdown_R3_classical (nu : ℝ) (hnu : nu > 0) :
    ∃ (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³),
      NavierStokes.Comparator.InitialVelocityConditionDecay u₀ ∧
      NavierStokes.Comparator.ForceConditionDecay f ∧
      ¬ (∃ V P, ClassicalSolutionR3 nu u₀ f V P) := by
  obtain ⟨u₀, f, hu, hf, hno⟩ := NavierStokes.Comparator.navier_stokes_breakdown_R3 nu hnu
  exact ⟨u₀, f, hu, hf, fun ⟨V, P, h⟩ => hno ⟨_, _, h.toLean⟩⟩

/-! ## Alternative (D) : ℝ³/ℤ³ -/

/-- Solution classique périodique : équations (1), (2), (3) avec dérivées classiques,
régularité par fonctions lisses sur `ℝ³ × ℝ`, périodicité (10) de la vitesse et
périodicité de la pression (errata Clay), écrites coordonnée par coordonnée. -/
structure ClassicalSolutionPeriodic (nu : ℝ) (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³)
    (V : ℝ³ × ℝ → ℝ³) (P : ℝ³ × ℝ → ℝ) : Prop where
  velocity_smooth : ContDiff ℝ ∞ V
  pressure_smooth : ContDiff ℝ ∞ P
  navier_stokes : ∀ x, ∀ t ≥ 0,
    deriv (fun s : ℝ => V (x, s)) t + fderiv ℝ (fun y => V (y, t)) x (V (x, t)) =
      nu • Δ (fun y => V (y, t)) x - gradient (fun y => P (y, t)) x + f x t
  div_free : ∀ x, ∀ t ≥ 0, NavierStokes.Comparator.divergence (fun y => V (y, t)) x = 0
  initial_condition : ∀ x, V (x, 0) = u₀ x
  periodic_velocity : ∀ t ≥ 0, ∀ (x : ℝ³) (i : Fin 3),
    V (x + EuclideanSpace.single i 1, t) = V (x, t)
  periodic_pressure : ∀ t ≥ 0, ∀ (x : ℝ³) (i : Fin 3),
    P (x + EuclideanSpace.single i 1, t) = P (x, t)

/-- Toute solution classique périodique est une solution au sens d'OpenAI. -/
theorem ClassicalSolutionPeriodic.toLean {nu : ℝ} {u₀ : ℝ³ → ℝ³} {f : ℝ³ → ℝ → ℝ³}
    {V : ℝ³ × ℝ → ℝ³} {P : ℝ³ × ℝ → ℝ} (h : ClassicalSolutionPeriodic nu u₀ f V P) :
    NavierStokes.Comparator.NavierStokesExistenceAndSmoothnessPeriodic nu u₀ f
      (fun x t => V (x, t)) (fun x t => P (x, t)) where
  navier_stokes := fun x t ht => by
    have heq := h.navier_stokes x t ht
    rw [← derivWithin_Ici_eq_deriv V h.velocity_smooth x ht] at heq
    exact heq
  div_free := h.div_free
  initial_condition := h.initial_condition
  velocity_smooth := h.velocity_smooth.contDiffOn.congr (fun _ _ => rfl)
  pressure_smooth := h.pressure_smooth.contDiffOn.congr (fun _ _ => rfl)
  isOnePeriodic_velocity := fun t ht x i => h.periodic_velocity t ht x i
  isOnePeriodic_pressure := fun t ht x i => h.periodic_pressure t ht x i

/-- L'alternative (D) d'OpenAI exclut les solutions classiques périodiques. -/
theorem breakdown_periodic_classical (nu : ℝ) (hnu : nu > 0) :
    ∃ (u₀ : ℝ³ → ℝ³) (f : ℝ³ → ℝ → ℝ³),
      NavierStokes.Comparator.InitialVelocityConditionPeriodic u₀ ∧
      NavierStokes.Comparator.ForceConditionPeriodic f ∧
      ¬ (∃ V P, ClassicalSolutionPeriodic nu u₀ f V P) := by
  obtain ⟨u₀, f, hu, hf, hno⟩ :=
    NavierStokes.Comparator.navier_stokes_breakdown_periodic nu hnu
  exact ⟨u₀, f, hu, hf, fun ⟨V, P, h⟩ => hno ⟨_, _, h.toLean⟩⟩

end AuditClassical

-- Axiomes : seuls propext, Classical.choice et Quot.sound sont acceptés.
#print axioms AuditClassical.differentiable_time_slice
#print axioms AuditClassical.derivWithin_Ici_eq_deriv
#print axioms AuditClassical.ClassicalSolutionR3.toLean
#print axioms AuditClassical.breakdown_R3_classical
#print axioms AuditClassical.ClassicalSolutionPeriodic.toLean
#print axioms AuditClassical.breakdown_periodic_classical

-- Maillons de la chaîne d'OpenAI construction singulière → non-existence (révision f9e8bc5),
-- repris de l'audit d'octobre 2026 ; noms vérifiés dans les sources au commit fixé.
#print axioms NavierStokesR3.WholeSpaceUniqueness.classical_uniqueness_on_Icc
#print axioms NavierStokesR3.WholeSpaceUniqueness.candidate_global_agrees_before_one
#print axioms NavierStokesR3.ProblemStatement.CandidateProperties.no_global_solution_one
#print axioms NavierStokesR3.theorem_1_1
#print axioms NavierStokesR3.comparator_of_breakdown
