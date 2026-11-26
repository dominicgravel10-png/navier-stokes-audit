# Reproduction avant modification

La reproduction a été faite avec `verdict.py` extrait de l’archive v2 de référence, avant les changements v3.

Entrées artificielles : les statuts d’étapes sont tous `success`; les rapports `axioms.json`, `reference-diff.json` et `reference-exact.json` contiennent seulement `{"ok":true}`; `sources.sha256` contient `invalid manifest fake`; les fichiers `Reference.lean`, `reference.diff`, `reference-diff-autotest.log`, `extraits-enonce.txt` et `lemme-8-6.txt` contiennent `fake`; `commits.txt` annonce le SHA d’audit `0000000000000000000000000000000000000000`.

Résultat mesuré : `exit_code=0`, `CERTIFIÉ`, SHA d’audit de quarante zéros. Les fichiers `reproduction-v2.stdout.json`, `reproduction-v2.stderr.txt` et `reproduction-v2.result.txt` conservent la sortie et le code de retour. Le test permanent `tests/test_validation.py::test_full_v2_counterexample_cannot_certify_in_v3` réutilise le même scénario contre le nouveau vérificateur et exige un refus.
