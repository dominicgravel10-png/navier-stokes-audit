# Preuves de l'exécution #13 — audit Navier–Stokes

Archive des pièces de l'exécution GitHub Actions #13 du workflow « Audit Navier-Stokes — quatre controles »,
copiées depuis l'artefact `audit-quatre-etapes` avant son expiration (5 février 2027).

| Élément | Valeur |
|---|---|
| Exécution | https://github.com/dominicgravel10-png/navier-stokes-audit/actions/runs/42338240579 |
| Date (UTC) | 2026-11-07T06:13:38+00:00 |
| Déclencheur | pull request #1 (commit de fusion de test) |
| Commit audité (fusion de test) | `492c9a112c881bcfd5e82e0ec9960a2218566a2f` (tête `6f65703`, base `6d74dd2`) |
| OpenAI | `openai/NavierStokesAndEuler` @ `f9e8bc5b38b6e212696e8a30e3e91517af887bbd` |
| DeepMind | `google-deepmind/formal-conjectures` @ `8bf45ed70d48b2b2a501de9c00b26bfa38c573ee` |
| Lean | 4.34.0-rc2 (commit `6a10ac8c22beadecabdbb0919c2b50214762f91d`) |

## Verdicts

- **Verdict 1 — certification Lean : CERTIFIÉ.** Compilation complète d'OpenAI, transfert champ par champ de
  l'énoncé DeepMind original pour (C) et (D), pont de régularité au bord pour (C), et `#print axioms` sur
  9 théorèmes : tous limités à `propext`, `Classical.choice`, `Quot.sound` ; aucun `sorry`, aucune erreur Lean.
- **Verdict 2 — correspondance avec le texte Clay (Fefferman) : À VALIDER HUMAINEMENT.**

## Hors portée de ce certificat

- Correspondance entre la preuve écrite d'OpenAI et sa preuve Lean (dont lemme 8.6 / éq. 8.19).
- Relecture du noyau par un vérificateur indépendant.
- Pont de régularité pour (D) et pont en dérivées classiques : ajoutés après #13, à certifier par une nouvelle exécution.

## Note de lecture

Les deux « avertissements indicatifs » du certificat renvoient à `definitions.json` et `contournement.txt`,
qui n'existent pas : ces contrôles textuels n'ont pas été exécutés (`skipped`). Le `verdict.py` de #13
affichait à tort « différences » pour un contrôle non exécuté. Corrigé après #13 ; sans effet sur le verdict 1.

## Vérifier

    sha256sum -c SHA256SUMS

L'empreinte de `axioms.json` est aussi inscrite dans `certificat.json` (`empreintes_sha256`).
Les autres journaux de l'artefact (bridge.log, reference.log, lean-build.log…) n'ont pas été conservés ;
seules leurs empreintes subsistent dans le certificat.
