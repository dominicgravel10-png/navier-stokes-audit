import NavierStokes.ComparatorSolution

/-!
# Audit v3 — le témoin effectif de l'alternative (C), exposé formellement

Auteur de l'audit : Dominic Gravel (ORCID 0009-0004-2819-2902), avec l'aide de Claude.

L'énoncé (C) d'OpenAI ne garantit, pour la force, que `ForceConditionDecay` : régularité et
décroissance **relatives au demi-espace** `ℝ³ × [0, ∞)`. Le texte Clay ne précise pas le sens
de « lisse sur ℝ³ × [0, ∞) ». Ce fichier rend la question sans objet pour les données :
il démontre (C) avec un témoin explicite dont
  * la vitesse initiale est identiquement nulle ;
  * la force `F` est lisse sur **tout** `ℝ × ℝ³` (aucune extension, aucun Seeley) ;
  * la force est à support compact, contenu dans `{t > 0}`.
Les données satisfont donc (4) et (5) de Fefferman sous toute lecture de la régularité au bord.

Source : `NavierStokesR3.theorem_1_1` et `NavierStokesR3.comparator_of_breakdown`
(`NavierStokes/R3/Theorem.lean`, `NavierStokes/R3/ComparatorBridge.lean`, commit `f9e8bc5`).
-/

open Set ContDiff

namespace AuditWitness

local notation "ℝ³" => EuclideanSpace ℝ (Fin 3)

/-- (C) avec un témoin explicite : vitesse initiale nulle, force lisse sur tout l'espace-temps,
à support compact dans les temps strictement positifs. -/
theorem witness_R3 (nu : ℝ) (hnu : nu > 0) :
    ∃ F : ℝ × ℝ³ → ℝ³,
      ContDiff ℝ ∞ F ∧ HasCompactSupport F ∧
      tsupport F ⊆ Ioi (0 : ℝ) ×ˢ (univ : Set ℝ³) ∧
      NavierStokes.Comparator.InitialVelocityConditionDecay (fun _ : ℝ³ => (0 : ℝ³)) ∧
      NavierStokes.Comparator.ForceConditionDecay (fun (x : ℝ³) (t : ℝ) => F (t, x)) ∧
      ¬ (∃ v p, NavierStokes.Comparator.NavierStokesExistenceAndSmoothnessRn nu
          (fun _ : ℝ³ => (0 : ℝ³)) (fun (x : ℝ³) (t : ℝ) => F (t, x)) v p) := by
  obtain ⟨u, p, f, K, h, hglobal⟩ := NavierStokesR3.theorem_1_1 nu hnu
  refine ⟨f, h.force_smooth, h.force_support.1, h.force_support.2,
    NavierStokes.ComparatorBridge.zero_initial_condition_decay,
    NavierStokesR3.forceConditionDecay_of_compact h.force_smooth h.force_support.1, ?_⟩
  rintro ⟨v, q, hv⟩
  exact hglobal ⟨NavierStokesR3.globalSolutionOfComparator (f := f) hv⟩

end AuditWitness

-- Axiomes : seuls propext, Classical.choice et Quot.sound sont acceptés.
#print axioms AuditWitness.witness_R3
