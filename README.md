# Audit contradictoire Navier–Stokes — v3 (fusion)

Auteur : Dominic Gravel — ORCID [0009-0004-2819-2902](https://orcid.org/0009-0004-2819-2902).
Rédigé avec l'assistance de Claude (Anthropic) et d'un second assistant pour le contre-audit.


**Statut : préparation locale; aucune certification v3.** La PR #1 doit rester en brouillon. Le Verdict 2 reste ouvert et ne peut être validé par ce workflow.

## Références fixées

- Archive v2 préservée : `../historique/navier-stokes-audit-v2-corrige.zip`, SHA-256 `aed6c3df629e547e6ff82c9dd5dc935e8d86556fd28566831395adae33b200bb`.
- Sources OpenAI : `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`.
- Énoncé DeepMind : `8bf45ed70d48b2b2a501de9c00b26bfa38c573ee`.
- Lean : `4.34.0-rc2`, commit `6a10ac8c22beadecabdbb0919c2b50214762f91d`.
- Exécution historique #13 : attestations JSON et empreintes conservées sous `preuves/execution-13/`; les autres journaux d’origine ne sont plus disponibles dans l’archive historique.

## Résultat acquis : exécution #13 du 7 novembre 2026

Verdict 1 **CERTIFIÉ** ([run 42338240579](https://github.com/dominicgravel10-png/navier-stokes-audit/actions/runs/42338240579)) :
compilation complète, transfert DeepMind (C) et (D), pont (C), 9 théorèmes limités à `propext`,
`Classical.choice`, `Quot.sound`. `certificat.json` SHA-256 `747dac87…1e8f`, `axioms.json`
`6b51cd7c…ef4`. Verdict 2 : À VALIDER HUMAINEMENT. Ce résultat porte sur le code de #13 seulement.

## Défaut v2 reproduit

Avant toute modification v3, l’archive de référence a donné code de sortie `0` et `CERTIFIÉ` face aux rapports `{"ok":true}`, justificatifs `fake`, au manifeste invalide et au commit d’audit composé de quarante zéros. La reproduction et sa sortie sont dans `preuves/contre-exemple-v2/`.

## Contrôles v3

- Les rapports doivent respecter des schémas exacts, contenir la liste exhaustive des théorèmes attendus et ne dépendre que de `propext`, `Classical.choice` et `Quot.sound`.
- Les journaux de compilation et de transfert sont obligatoires et rejoués; les rapports de transfert sont recalculés depuis les sources fixées.
- Le manifeste doit énumérer exactement les sources attendues, sans doublon ni chemin hors espace; chaque SHA-256 est recalculé.
- Le commit d’audit inscrit au certificat doit égaler le commit du checkout réellement exécuté (`GITHUB_SHA`). Les commits OpenAI et DeepMind sont épinglés.
- Les actions GitHub sont appelées par SHA complet; le script d’installation elan est téléchargé depuis un commit fixe, conservé, et son empreinte est contrôlée.
- Les compléments sont certifiés séparément, sans effet sur le verdict Lean principal :
  `ClassicalBoundary.lean` (pont classique (C) et (D), onze théorèmes), `ForceWitness.lean`
  (témoin explicite de (C) : u° = 0, force lisse sur tout ℝ × ℝ³, support compact dans {t > 0}),
  `EnergyBridge.lean` (condition (7) en intégrale étendue ⇒ champs d'énergie d'OpenAI).
- Une étape non exécutée est `skipped`, jamais `failed` ; la génération de la référence est une
  étape distincte (`GENERATION`). Les verdicts d'échec ne portent que sur des étapes exécutées.
- Les tests négatifs vérifient le faux positif v2, les rapports tronqués, les SHA incorrects, les commits fictifs, les listes de théorèmes modifiées et les axiomes non autorisés.
- L’archive historique v2 et les preuves #13 sont conservées sans modification.

## Fusion des deux v3 (26 novembre 2026)

Base : la v3 du contre-audit (vérificateur `audit_validation.py`, schémas stricts, rejeu).
Ajouts de la v3 de Claude : `ForceWitness.lean`, `EnergyBridge.lean`, statuts `GENERATION`,
`WITNESS`, `ENERGY`, table générique `COMPLEMENTS`, analyse clause par clause de `VERDICT-2.md`.
Défauts corrigés pendant la fusion :
- `verdict.py` plantait (`KeyError`) sur des pièces fabriquées avec un `status.env` complet, sans
  écrire de certificat ; il écrit désormais toujours un certificat de refus ;
- le nombre de tests attendu était figé à douze ; il est calculé depuis les sources des tests ;
- le test du faux positif v2 passait sans `status.env` : il fournit maintenant des statuts
  complets, pour que le refus vienne des pièces elles-mêmes.
Tests locaux : 22 sur 22. Simulation du workflow avec de faux outils Lean : statuts et
compléments conformes ; aucune compilation Lean réelle n'a été faite hors CI.

## Ce que le certificat ne tranchera pas

La machine vérifie des énoncés Lean, pas leur équivalence complète au texte naturel de Clay ni la fidélité de la preuve écrite au terme Lean. Le rapport humain et les obligations ouvertes sont dans [`VERDICT-2.md`](VERDICT-2.md); leur état scientifique et la veille bibliographique sont dans [`RAPPORT-SCIENTIFIQUE-v3.md`](RAPPORT-SCIENTIFIQUE-v3.md).

Un `CERTIFIÉ` ultérieur signifiera seulement que les contrôles formels et leurs pièces ont été confirmés pour l’exécution précisément identifiée. Il ne fermera pas le Verdict 2.

## Exécution historique #15 examinée

Le run GitHub Actions #15 est terminé avec succès. Son artefact a été conservé sous `preuves/execution-15/`; son SHA-256 est `8bf4d7fb9ce9adf1f44c4486ffecbcb7a1001c0499990524dbc3916092e3b942`. La certification affichée concerne le commit d’audit de fusion `bcd68a5121f2b90697c73d958e6251f6fa150758`, pas les fichiers v3 préparés ici. L’examen indépendant est consigné dans `preuves/execution-15/examen-independant.md`.

Les neuf théorèmes du verdict principal et les vingt du rapport complémentaire ont les noms attendus et utilisent seulement les axiomes standards. Les empreintes de tous les fichiers de l’artefact concordent, les 22 entrées du manifeste source ont été rehachées à partir des commits Git épinglés, et `Reference.lean` a été régénéré octet pour octet. Le Verdict 2 demeure « À VALIDER HUMAINEMENT ».

Deux constats complémentaires (Claude, 26 novembre) :
- `Reference.lean` de #15 a pour SHA-256 `12a88544…f77b`, identique à la régénération faite
  indépendamment hors CI le matin même à partir de DeepMind `8bf45ed` : deux chaînes distinctes
  aboutissent au même fichier ;
- la copie de `journaux/lean-build.log` versée au commit `804fa69` était corrompue (contenu
  binaire, empreinte non conforme à `SHA256SUMS`) ; elle est remplacée par la copie de
  l'artefact GitHub, dont l'empreinte `aa35ea96…3ede` concorde avec le certificat
  (2 668 lignes, « Build completed successfully (11424 jobs) »).
Ce run est aussi la première compilation réelle de `ClassicalBoundary.lean` : ses 11 théorèmes
n'utilisent que les trois axiomes standard.

Ce run précède les corrections v3 : il n’atteste donc ni les tests contradictoires permanents, ni l’installation épinglée, ni les nouveaux contrôles anti-faux-positif. Aucune certification v3 n’est affirmée. La PR #1 demeure en brouillon.
