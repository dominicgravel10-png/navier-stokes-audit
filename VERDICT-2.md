# Verdict 2 — correspondance avec le problème de Clay

**Statut : À VALIDER HUMAINEMENT.** Ce document rétablit la grille d’analyse du dossier antérieur; il ne constitue ni une validation finale ni une attribution du prix. Le verdict automatique v3 ne peut pas fermer ces obligations.

## Portée de l’énoncé Lean

Le dépôt OpenAI épingle les alternatives formelles (C) et (D), reprises de la formalisation DeepMind au commit `8bf45ed70d48b2b2a501de9c00b26bfa38c573ee`. Le transfert mécanique et la compilation prouvent, si le workflow correspondant est certifié, que le noyau Lean accepte les théorèmes contre ces énoncés formels. Cela ne suffit pas à établir la fidélité de la formalisation au texte de Fefferman.

Le pont `BoundaryBridge.lean` couvre la classe de solutions munies d’un prolongement lisse global au-delà de `t=0`. Il ne démontre pas l’équivalence de cette classe avec toutes les fonctions `C∞` sur le demi-espace fermé. L’extension de Seeley et les conventions de dérivées au bord doivent être reliées à la formulation officielle, clause par clause.

## Contrôles humains encore ouverts

| Obligation | État | Pièce à examiner |
|---|---|---|
| Définition exacte de `C∞(R³ × [0,∞))` et relation au prolongement lisse utilisé dans le pont | Ouverte | Définition Clay, `ClassicalBoundary.lean`, lemme d’extension pertinent |
| Dérivées en temps à `t=0` : dérivée unilatérale dans l’énoncé contre dérivée classique Lean | Ouverte | Définition Clay et clauses Lean de l’équation |
| Condition d’énergie (7), y compris l’intégrabilité `L²` et la borne uniforme | À vérifier indépendamment | `extraits-enonce.txt`, structure `NavierStokesExistenceAndSmoothnessRn` |
| Périodicité de la pression dans l’alternative (D), au regard de l’erratum Clay | Ouverte | `extraits-enonce.txt`, énoncé officiel et erratum |
| Fidélité complète des domaines, données initiales, force, divergence, régularité et périodicité | Ouverte | Comparaison Clay–DeepMind–OpenAI, ligne par ligne |
| Correspondance entre preuve écrite et preuve Lean, notamment lemme 8.6 / équation (8.19) | Hors certification de cette archive | `lemme-8-6.txt`, prépublication critique et versions originales |

## Règle de conclusion

Un futur `CERTIFIÉ` dans `certificat.json` concerne uniquement la chaîne informatique et formelle explicitement contrôlée. Il ne valide pas ce document. Le verdict 2 restera « À VALIDER HUMAINEMENT » jusqu’à ce qu’une revue mathématique indépendante documente chaque obligation, ses sources, les hypothèses exactes et les éventuels écarts.

## Références de départ

- Clay Mathematics Institute, [Navier-Stokes Announcement](https://www.claymath.org/news/navier-stokes-announcement/), 11 septembre 2026; le Clay indique que le problème « appears » réglé et que son processus d’évaluation est délibérément non précipité.
- Clay Mathematics Institute, [description officielle du problème](https://www.claymath.org/millennium/navier-stokes-equation/).
- OpenAI, [On the Navier–Stokes Millennium Prize Problem](https://openai.com/index/navier-stokes-solution/), 8 septembre 2026, mise à jour le 10 septembre; annonce une preuve pour (C) et (D).
- Bastounis, Circelli et Hansen, [Navier-Stokes lost in translation](https://arxiv.org/abs/2610.08144), prépublication du 6 octobre 2026; elle conteste la correspondance entre l’argument écrit et la formalisation Lean, sans établir que le théorème Lean est faux.
- Buckmaster et Alpöge, [Finite-time blow-up for the Navier–Stokes equations](https://github.com/tristanbuckmaster/navier-stokes), dépôt rendu public le 20 novembre 2026; nouvelle revendication non forcée dont le dépôt signale que le certificat numérique n’est pas inclus et que la version patchée n’a pas été reconstruite.
