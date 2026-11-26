# Examen indépendant de l’exécution GitHub Actions #15

Run `45803959668`, job `139854171849`, terminé avec `success` le 26 novembre 2026. Le digest GitHub de l’artefact est `sha256:8bf4d7fb9ce9adf1f44c4486ffecbcb7a1001c0499990524dbc3916092e3b942`; il concorde avec le ZIP conservé ici.

## Contrôles reproduits

- Le statut des sept étapes est `success`.
- Le certificat indique `CERTIFIÉ` pour le contrôle Lean principal et `À VALIDER HUMAINEMENT` pour le Verdict 2.
- `axioms.json` contient exactement les neuf théorèmes principaux attendus; `axioms-complet.json` contient exactement ces neuf théorèmes plus les onze théorèmes classiques attendus. Les deux rapports n’utilisent que `propext`, `Classical.choice` et `Quot.sound`; `sorry=false` et `erreurs_lean=0`.
- Toutes les empreintes indiquées dans `certificat.json` ont été recalculées et concordent avec les fichiers extraits.
- Les 22 entrées de `sources.sha256` ont été rehachées à partir du contenu servi par GitHub aux révisions consignées dans `commits.txt`; 22/22 concordent.
- Le générateur `make_reference.py`, dont le SHA-256 est lié au manifeste, régénère `Reference.lean` identique à la pièce de CI, octet pour octet. Son SHA-256 est `12a8854400a87c6ff55b4ed67b1266db0cfea94045d6bdbe79f7f63c096df77b`.

## Portée et réserves

L’audit testé est le commit de fusion `bcd68a5121f2b90697c73d958e6251f6fa150758`, correspondant à la révision précédente de la PR. Le run #15 précède les correctifs v3 : il ne comprend ni les tests négatifs permanents v3, ni les pièces d’installation épinglée v3. Il n’exécute pas nanoda. Les journaux identifient les actions `checkout@v4` et `upload-artifact@v4`; la v3 locale prépare leur épinglage par SHA. Ce run ne valide donc pas les scripts v3 préparés dans ce dossier.

Le Verdict 2 reste ouvert : correspondance clause par clause avec l’énoncé de Clay, pont Seeley vers la régularité sur le demi-espace, condition d’énergie, périodicité de pression dans (D), et concordance entre preuve écrite et preuve Lean.
