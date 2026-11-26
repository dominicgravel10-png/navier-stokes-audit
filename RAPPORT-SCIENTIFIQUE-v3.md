# Rapport scientifique v3 — audit formel Navier–Stokes

**Date de veille : 26 novembre 2026**  
**Statut : audit logiciel en préparation; certification Lean v3 non encore exécutée.**  
**Confidentialité : recherche privée.**

## Question et limites

Ce travail vérifie si les résultats Lean du dépôt OpenAI au commit `f9e8bc5b38b6e212696e8a30e3e91517af887bbd` compilent, si le transfert des alternatives formelles (C) et (D) depuis DeepMind est fidèle au texte source, et si la fermeture des dépendances des théorèmes examinés n’utilise que `propext`, `Classical.choice` et `Quot.sound`. Il distingue ces faits de la correspondance entre l’énoncé Lean et le problème formulé en langage naturel par Clay, et de l’exactitude de la preuve rédigée.

Le travail ne permet pas de conclure que la preuve est acceptée par le Clay Mathematics Institute ou que le prix a été attribué. Le Clay a publié un avis prudent le 11 septembre 2026 et dit que son processus d’évaluation est délibérément non précipité.

## État de l’art et balayage daté

Requêtes exécutées le 26 novembre 2026 :

- `site:openai.com Navier-Stokes Millennium Prize Problem OpenAI September 2026`
- `site:claymath.org Navier-Stokes announcement OpenAI September 2026`
- `arXiv Navier-Stokes lost in translation 2610.08144 Bastounis Circelli Hansen`
- `Alpöge Buckmaster Navier-Stokes blowup November 2026 arXiv 2611.02204`
- `github OpenAI NavierStokesAndEuler ComparatorChallenges NavierStokes.json nanoda`
- `github.com/tristanbuckmaster/navier-stokes README Lean certificate not released 2026`
- recherches ciblées sur les instructions officielles d’installation de Comparator, nanoda et lean4export.

Sources primaires consultées :

1. OpenAI, [annonce officielle](https://openai.com/index/navier-stokes-solution/), 8 septembre, mise à jour du 10 septembre 2026. L’annonce affirme que le modèle établit l’alternative (C) et aussi (D); elle décrit un écoulement avec force lisse depuis le repos.
2. Clay Mathematics Institute, [annonce du 11 septembre](https://www.claymath.org/news/navier-stokes-announcement/). Le Clay parle d’un problème « apparemment » réglé et dit que l’examen des demandes de prix suit un processus délibérément lent.
3. A. Bastounis, F. Circelli et A. C. Hansen, [arXiv:2610.08144](https://arxiv.org/abs/2610.08144), déposé le 6 octobre 2026. Les auteurs contestent la fidélité entre la preuve écrite et sa formalisation; cela ne constitue pas une réfutation du théorème Lean vérifié.
4. L. Alpöge et T. Buckmaster, [dépôt de la prépublication et du code Lean](https://github.com/tristanbuckmaster/navier-stokes), 20 novembre 2026. Cette revendication porte sur un blow-up sans force, donc une portée mathématique distincte et plus large. Le README du dépôt précise que le certificat numérique annoncé n’est pas présent et que le paquet avec son patch du 20 novembre n’a pas été reconstruit. Il s’agit d’une revendication à examiner, pas d’un résultat validé par cet audit.
5. OpenAI, [configuration Comparator](https://github.com/openai/NavierStokesAndEuler/blob/f9e8bc5b38b6e212696e8a30e3e91517af887bbd/ComparatorChallenges/NavierStokes.json) et [instructions d’exécution](https://github.com/openai/NavierStokesAndEuler/tree/f9e8bc5b38b6e212696e8a30e3e91517af887bbd/ComparatorChallenges). La configuration active `nanoda`, compare deux théorèmes précis et n’autorise que les trois axiomes standards.
6. M. Ray, [reconstruction indépendante publique](https://github.com/rayman813/navierstokes-lean-independent-rebuild), datée du 10 septembre 2026 : elle rapporte un rebuild de la révision OpenAI `f9e8bc5`, puis un passage neuf par Comparator où Lean et nanoda acceptent les deux théorèmes Navier–Stokes. Le manifeste public SHA256SUMS donne `5189105116c3b546e5bf9c2339cfa8fe1034f6df8a6ca1f7b17032899420975b` pour `logs/cmp_fresh_NavierStokes.log` et `39734d5df2e9a92e4c83558bf44fc4f7c1af44de24d7697f77382fd07de69514` pour le passage précompilé. La publication décrit nanoda v0.4.17 et landrun construits depuis la branche `main` à l’exécution : c’est une vérification indépendante utile, mais ces deux outils ne sont pas épinglés à des commits immuables. Cette corroboration est externe; elle n’est ni attachée au run v3 ni une vérification du texte Clay.
7. Une vérification additionnelle du dépôt Alpöge–Buckmaster a repéré l’[issue #3](https://github.com/tristanbuckmaster/navier-stokes/issues/3), ouverte le 20 novembre 2026 : son auteur propose un contre-exemple analytique à un terme de l’inégalité (B.20), fondé sur un terme de bord axisymétrique, et demande l’accès au certificat numérique. C’est une objection technique publique à examiner avec les auteurs; elle n’est pas une réfutation revue par les pairs ni une vérification indépendante complète de leur résultat. Elle renforce la nécessité de ne pas traiter le paquet annoncé comme certifié en l’absence des données et d’un rejeu.

Limites de couverture : balayage ciblé des annonces, dépôts et prépublications directement liés; il ne constitue pas une recherche bibliographique exhaustive. Le texte complet de la prépublication critique et du travail de Buckmaster–Alpöge n’est pas certifié par le présent audit. Toute évolution de ces dépôts peut modifier l’état du dossier.

## Reproduction du défaut et correction proposée

Le test de contre-exemple exécuté avant les modifications, sur l’archive v2 dont le SHA-256 de référence est conservé, a retourné code `0` et verdict `CERTIFIÉ` avec trois rapports ne contenant que `{"ok":true}`, des fichiers `fake`, le manifeste `invalid manifest fake`, et un SHA d’audit de quarante zéros. La sortie exacte est archivée sous `preuves/contre-exemple-v2/`.

La v3 durcit le verdict par validation de schémas et de valeurs, rejeu des rapports contre les entrées et les journaux, vérification cryptographique et exhaustive du manifeste, contrôle des références Git effectivement extraites, contrôle distinct des théorèmes du pont classique et tests négatifs permanents. Les contrôles locaux Python passent.

L’exécution #15 de la révision précédente est maintenant terminée et examinée. Elle affiche le verdict Lean principal « CERTIFIÉ », les sept statuts en succès, les neuf théorèmes principaux et les vingt théorèmes du rapport complémentaire, sans `sorry`, erreur Lean ni axiome hors de `propext`, `Classical.choice`, `Quot.sound`. Le ZIP de l’artefact correspond au digest publié par GitHub; chaque empreinte portée dans le certificat a été recalculée; les 22 entrées de `sources.sha256` concordent avec les fichiers des trois commits épinglés; la génération de `Reference.lean` a été répétée et donne le même fichier octet pour octet.

La v3 fixe également les actions GitHub par SHA complet et télécharge le script elan depuis un commit immuable, en conservant le script, son empreinte et le journal d’installation.

Cette exécution #15 a testé le commit de fusion `bcd68a5121f2b90697c73d958e6251f6fa150758`, avant les corrections v3. Son résultat n’est pas une certification des scripts v3. Le run ne contenait pas les tests négatifs permanents, ni les éléments d’installation épinglée, et ne lançait pas nanoda. Le Verdict 2 reste ouvert. Les détails et les limites sont dans `preuves/execution-15/examen-independant.md`.

## Vérification indépendante du noyau

Le contrôle est compatible : la configuration du commit OpenAI active `nanoda`, et la documentation Comparator décrit la commande d’exécution avec `landrun`, `lean4export` et `nanoda_bin`. La reconstruction publique de Ray rapporte déjà une acceptation par le noyau Lean et nanoda pour les deux théorèmes Navier–Stokes au même commit OpenAI. Cette preuve externe ne remplace pas une exécution attachée à notre manifeste v3. Les outils et leurs versions devront être épinglés avant de déclarer un contrôle v3 reproductible.

## Conclusion provisoire

Le défaut de faux positif est réel et reproduit. Les nouveaux tests Python rejettent l’échantillon artificiel et valident la cohérence des deux fichiers archivés de l’exécution #13. Le run #15 précédent est maintenant archivé et ses pièces examinées; elles renforcent le constat sur cette révision, sans valider la v3. Aucun verdict 2 n’est fermé. Aucun statut de certification Lean v3 ne peut être donné avant le lancement contrôlé et le succès d’une nouvelle exécution de la v3.
