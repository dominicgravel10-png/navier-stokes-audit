# Audit contradictoire Navier–Stokes — v3

**Statut : préparation locale; aucune certification v3.** La PR #1 doit rester en brouillon. Le Verdict 2 reste ouvert et ne peut être validé par ce workflow.

## Références fixées

- Archive v2 préservée : `../historique/navier-stokes-audit-v2-corrige.zip`, SHA-256 `aed6c3df629e547e6ff82c9dd5dc935e8d86556fd28566831395adae33b200bb`.
- Sources OpenAI : `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`.
- Énoncé DeepMind : `8bf45ed70d48b2b2a501de9c00b26bfa38c573ee`.
- Lean : `4.34.0-rc2`, commit `6a10ac8c22beadecabdbb0919c2b50214762f91d`.
- Exécution historique #13 : attestations JSON et empreintes conservées sous `preuves/execution-13/`; les autres journaux d’origine ne sont plus disponibles dans l’archive historique.

## Défaut v2 reproduit

Avant toute modification v3, l’archive de référence a donné code de sortie `0` et `CERTIFIÉ` face aux rapports `{"ok":true}`, justificatifs `fake`, au manifeste invalide et au commit d’audit composé de quarante zéros. La reproduction et sa sortie sont dans `preuves/contre-exemple-v2/`.

## Contrôles v3

- Les rapports doivent respecter des schémas exacts, contenir la liste exhaustive des théorèmes attendus et ne dépendre que de `propext`, `Classical.choice` et `Quot.sound`.
- Les journaux de compilation et de transfert sont obligatoires et rejoués; les rapports de transfert sont recalculés depuis les sources fixées.
- Le manifeste doit énumérer exactement les sources attendues, sans doublon ni chemin hors espace; chaque SHA-256 est recalculé.
- Le commit d’audit inscrit au certificat doit égaler le commit du checkout réellement exécuté (`GITHUB_SHA`). Les commits OpenAI et DeepMind sont épinglés.
- Les actions GitHub sont appelées par SHA complet; le script d’installation elan est téléchargé depuis un commit fixe, conservé, et son empreinte est contrôlée.
- La certification de `ClassicalBoundary.lean` et de ses onze théorèmes est séparée du verdict Lean principal.
- Les tests négatifs vérifient le faux positif v2, les rapports tronqués, les SHA incorrects, les commits fictifs, les listes de théorèmes modifiées et les axiomes non autorisés.
- L’archive historique v2 et les preuves #13 sont conservées sans modification.

## Ce que le certificat ne tranchera pas

La machine vérifie des énoncés Lean, pas leur équivalence complète au texte naturel de Clay ni la fidélité de la preuve écrite au terme Lean. Le rapport humain et les obligations ouvertes sont dans [`VERDICT-2.md`](VERDICT-2.md); leur état scientifique et la veille bibliographique sont dans [`RAPPORT-SCIENTIFIQUE-v3.md`](RAPPORT-SCIENTIFIQUE-v3.md).

Un `CERTIFIÉ` ultérieur signifiera seulement que les contrôles formels et leurs pièces ont été confirmés pour l’exécution précisément identifiée. Il ne fermera pas le Verdict 2.

## Exécution historique #15 examinée

Le run GitHub Actions #15 est terminé avec succès. Son artefact a été conservé sous `preuves/execution-15/`; son SHA-256 est `8bf4d7fb9ce9adf1f44c4486ffecbcb7a1001c0499990524dbc3916092e3b942`. La certification affichée concerne le commit d’audit de fusion `bcd68a5121f2b90697c73d958e6251f6fa150758`, pas les fichiers v3 préparés ici. L’examen indépendant est consigné dans `preuves/execution-15/examen-independant.md`.

Les neuf théorèmes du verdict principal et les vingt du rapport complémentaire ont les noms attendus et utilisent seulement les axiomes standards. Les empreintes de tous les fichiers de l’artefact concordent, les 22 entrées du manifeste source ont été rehachées à partir des commits Git épinglés, et `Reference.lean` a été régénéré octet pour octet. Le Verdict 2 demeure « À VALIDER HUMAINEMENT ».

Ce run précède les corrections v3 : il n’atteste donc ni les tests contradictoires permanents, ni l’installation épinglée, ni les nouveaux contrôles anti-faux-positif. Aucune certification v3 n’est affirmée. La PR #1 demeure en brouillon.
