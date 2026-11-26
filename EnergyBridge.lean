import NavierStokes.ComparatorSolution

/-!
# Audit v3 — condition d'énergie (7) de Fefferman, sans ambiguïté d'intégrale

Auteur de l'audit : Dominic Gravel (ORCID 0009-0004-2819-2902), avec l'aide de Claude.

Fefferman, (7) : `∫ |u(x,t)|² dx < C` pour tout `t ≥ 0`.
OpenAI exige deux champs : `integrable : ∀ t ≥ 0, MemLp (‖v · t‖) 2` et
`globally_bounded_energy : ∃ E, ∀ t ≥ 0, ∫ x, ‖v x t‖ ^ 2 < E`, où `∫` est l'intégrale de
Bochner, qui vaut 0 pour une fonction non intégrable.

Ici, (7) est écrite avec l'intégrale de Lebesgue étendue `∫⁻` (à valeurs dans `[0, ∞]`),
qui ne prend aucune valeur conventionnelle : « l'énergie est finie et bornée par C » y a son
sens littéral. On démontre qu'elle entraîne les deux champs d'OpenAI. La seule hypothèse
supplémentaire est la continuité en espace à chaque instant, conséquence de (6).
-/

open MeasureTheory

namespace AuditEnergy

local notation "ℝ³" => EuclideanSpace ℝ (Fin 3)

/-- La condition (7), écrite avec l'intégrale étendue, entraîne les deux champs d'énergie
de la définition d'OpenAI. -/
theorem energy_bridge (v : ℝ³ → ℝ → ℝ³) (hcont : ∀ t ≥ 0, Continuous (fun x => v x t))
    (C : ℝ) (henergy : ∀ t ≥ 0, (∫⁻ x, ENNReal.ofReal (‖v x t‖ ^ 2)) < ENNReal.ofReal C) :
    (∀ t ≥ 0, MemLp (fun x => ‖v x t‖) 2) ∧
      (∃ E, ∀ t ≥ 0, (∫ x : ℝ³, ‖v x t‖ ^ 2) < E) := by
  have hnn : ∀ t : ℝ, (0 : ℝ³ → ℝ) ≤ᵐ[volume] (fun x => ‖v x t‖ ^ 2) :=
    fun t => ae_of_all _ (fun x => sq_nonneg ‖v x t‖)
  have hmeas : ∀ t ≥ 0, AEStronglyMeasurable (fun x => ‖v x t‖ ^ 2) volume :=
    fun t ht => ((hcont t ht).norm.pow 2).aestronglyMeasurable
  have hint : ∀ t ≥ 0, Integrable (fun x => ‖v x t‖ ^ 2) volume := fun t ht =>
    ⟨hmeas t ht,
      (hasFiniteIntegral_iff_ofReal (hnn t)).2 ((henergy t ht).trans ENNReal.ofReal_lt_top)⟩
  refine ⟨fun t ht => ?_, ⟨C, fun t ht => ?_⟩⟩
  · have hnorm : AEStronglyMeasurable (fun x => ‖v x t‖) volume :=
      (hcont t ht).norm.aestronglyMeasurable
    rw [memLp_two_iff_integrable_sq_norm hnorm]
    simpa only [norm_norm] using hint t ht
  · rw [integral_eq_lintegral_of_nonneg_ae (hnn t) (hmeas t ht)]
    exact ENNReal.toReal_lt_of_lt_ofReal (henergy t ht)

end AuditEnergy

-- Axiomes : seuls propext, Classical.choice et Quot.sound sont acceptés.
#print axioms AuditEnergy.energy_bridge
