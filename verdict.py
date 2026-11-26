#!/usr/bin/env python3
"""Verdict conservateur v3 : rapports stricts, sources vérifiées, preuves liées au run."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_validation import (
    CLASSICAL_THEOREMS,
    COMPLEMENTS,
    EXPECTED_DEEPMIND,
    EXPECTED_LEAN_COMMIT,
    EXPECTED_LEAN_VERSION,
    EXPECTED_OPENAI,
    MAIN_THEOREMS,
    STATUS_KEYS,
    VALID_STATUSES,
    git_head,
    load_json,
    parse_source_paths,
    sha256_file,
    tracked_audit_files,
    validate_axioms_report,
    validate_autotest_report,
    validate_commit_record,
    validate_github_context,
    validate_installer_evidence,
    validate_reference_diff_report,
    validate_reference_exact_report,
    verify_manifest,
)


def load_statuses(logs: Path) -> tuple[dict[str, str], list[str]]:
    path = logs / "status.env"
    errors = []
    values: dict[str, str] = {}
    if not path.is_file():
        return {key: "skipped" for key in STATUS_KEYS}, ["status.env absent"]
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or "=" not in line:
            errors.append(f"ligne {line_no} invalide dans status.env")
            continue
        key, value = line.split("=", 1)
        if key not in STATUS_KEYS or key in values or value not in VALID_STATUSES:
            errors.append(f"clé ou statut invalide dans status.env : {key}={value}")
            continue
        values[key] = value
    if set(values) != set(STATUS_KEYS):
        errors.append(f"status.env ne contient pas exactement les {len(STATUS_KEYS)} statuts attendus")
    for key in STATUS_KEYS:
        if os.environ.get(key) != values.get(key):
            errors.append(f"statut exporté différent de status.env : {key}")
    return {key: values.get(key, "skipped") for key in STATUS_KEYS}, errors


def require_file(logs: Path, name: str, errors: list[str], nonempty: bool = True) -> Path | None:
    path = logs / name
    if not path.is_file():
        errors.append(f"pièce absente : {name}")
        return None
    if nonempty and path.stat().st_size == 0:
        errors.append(f"pièce vide : {name}")
        return None
    return path


def parse_commits(path: Path, root: Path, env: dict[str, str], errors: list[str]) -> dict[str, str]:
    try:
        actual = {
            "OPENAI": git_head(root / "openai-src"),
            "DEEPMIND": git_head(root / "deepmind"),
            "AUDIT": git_head(root / "audit"),
        }
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        errors.append(f"révisions Git réelles introuvables : {type(exc).__name__}")
        return {}
    try:
        errors.extend(validate_commit_record(path.read_text(encoding="utf-8"), actual, env.get("GITHUB_SHA", "")))
    except OSError:
        errors.append("commits.txt illisible")
    if actual["OPENAI"] != EXPECTED_OPENAI or actual["DEEPMIND"] != EXPECTED_DEEPMIND:
        errors.append("les dépôts externes ne sont pas aux commits verrouillés")
    clean = subprocess.run(["git", "-C", str(root / "audit"), "status", "--porcelain", "--untracked-files=all"],
                           capture_output=True, text=True)
    if clean.returncode != 0 or clean.stdout.strip():
        errors.append("le checkout d'audit n'est pas propre")
    return actual


def check_required_main_files(logs: Path, errors: list[str]) -> None:
    required = (
        "commits.txt", "status.env", "lean-version.txt", "lean-build.log", "cache.log",
        "source-paths.txt", "reference-generate.log", "reference.log", "bridge.log",
        "axioms.log", "axioms.json", "reference.diff", "Reference.lean",
        "reference-diff.log", "reference-diff.json", "reference-exact.log",
        "reference-exact.json", "reference-diff-autotest.log",
        "reference-diff-autotest.json", "sources.sha256", "extraits-enonce.txt", "lemme-8-6.txt",
        "contradictory-tests.log", "elan-source.txt", "elan-init.sh", "elan-init.sha256", "elan-install.log",
    )
    for name in required:
        require_file(logs, name, errors)
    try:
        errors.extend(validate_installer_evidence(
            (logs / "elan-source.txt").read_text(encoding="ascii"),
            (logs / "elan-init.sh").read_bytes(),
            (logs / "elan-init.sha256").read_text(encoding="ascii"),
            (logs / "elan-install.log").read_text(encoding="utf-8", errors="replace"),
        ))
    except OSError:
        errors.append("pièces d'installation elan illisibles")


def verify_lean_build(root: Path, logs: Path, errors: list[str]) -> None:
    try:
        toolchain = (root / "openai-src/lean-toolchain").read_text(encoding="utf-8").strip()
        if toolchain != f"leanprover/lean4:v{EXPECTED_LEAN_VERSION}":
            errors.append("lean-toolchain ne correspond pas à la version attendue")
        version = (logs / "lean-version.txt").read_text(encoding="utf-8", errors="replace")
        if not re.search(rf"Lean \(version {re.escape(EXPECTED_LEAN_VERSION)},[^\n]*commit {EXPECTED_LEAN_COMMIT}", version):
            errors.append("lean-version.txt n'atteste pas la version et le commit Lean attendus")
        build = (logs / "lean-build.log").read_text(encoding="utf-8", errors="replace")
        if not re.search(r"Build completed successfully(?: \([0-9,]+ jobs?\))?\.", build):
            errors.append("lean-build.log n'atteste pas la fin réussie de lake build")
        if re.search(r"\berror:", build):
            errors.append("lean-build.log contient une erreur Lean")
        replay = subprocess.run(["lake", "build"], cwd=root / "openai-src", stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, check=False)
        if replay.returncode != 0:
            errors.append("rejeu local de lake build en échec")
    except OSError:
        errors.append("journaux ou toolchain de compilation illisibles")


def replay_lean_log(root: Path, logs: Path, command: list[str], saved_name: str, errors: list[str]) -> None:
    try:
        replay = subprocess.run(command, cwd=root / "openai-src", stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, check=False)
        if replay.returncode != 0:
            errors.append(f"rejeu Lean en échec : {saved_name}")
        if replay.stdout != (logs / saved_name).read_bytes():
            errors.append(f"journal Lean différent du rejeu : {saved_name}")
    except OSError as exc:
        errors.append(f"rejeu Lean impossible pour {saved_name} : {type(exc).__name__}")


def run_reference_rechecks(root: Path, logs: Path, source_paths: dict[str, str], errors: list[str]) -> None:
    """Régénère et recontrôle le fichier transmis; ne fait pas confiance aux JSON seuls."""
    audit = root / "audit"
    openai = root / "openai-src"
    missing = [k for k in ("NavierStokes", "Euclidean", "3d") if k not in source_paths]
    if missing:
        errors.append("rejeu du transfert impossible : chemins sources absents ("
                      + ", ".join(missing) + ")")
        return
    rel_ns = source_paths["NavierStokes"]
    rel_eucl = source_paths["Euclidean"]
    rel_3d = source_paths["3d"]
    # Les chemins enregistrés sont relatifs à la racine du workspace, comme dans le manifeste.
    cli_ns = "../" + rel_ns
    cli_eucl = "../" + rel_eucl
    cli_3d = "../" + rel_3d
    generated_live = openai / "AuditRef/Reference.lean"
    saved_reference = logs / "Reference.lean"
    try:
        if generated_live.read_bytes() != saved_reference.read_bytes():
            errors.append("Reference.lean conservé diffère du fichier réellement compilé")
        with tempfile.TemporaryDirectory(prefix="ns-audit-v3-") as tmp_dir:
            tmp = Path(tmp_dir)
            regenerated = tmp / "Reference.lean"
            cmd = [sys.executable, "-I", str(audit / "make_reference.py"), cli_ns, cli_eucl, cli_3d, str(regenerated)]
            gen = subprocess.run(cmd, cwd=openai, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if gen.returncode != 0 or not regenerated.is_file():
                errors.append("make_reference.py n'a pas régénéré l'énoncé")
                return
            if regenerated.read_bytes() != saved_reference.read_bytes():
                errors.append("Reference.lean n'est pas reproductible à partir de la source DeepMind")
            if "Écrit :" not in gen.stdout:
                errors.append("journal de génération ne contient pas sa preuve de sortie")
            if "Écrit :" not in (logs / "reference-generate.log").read_text(encoding="utf-8", errors="replace"):
                errors.append("reference-generate.log ne confirme pas la génération")
            # Rejoue les deux contrôles avec les mêmes chemins que le workflow, puis compare les objets JSON.
            diff_out = tmp / "reference-diff.json"
            exact_out = tmp / "reference-exact.json"
            diff_cmd = [sys.executable, "-I", str(audit / "check_reference_diff.py"), cli_ns, cli_eucl, cli_3d,
                        "AuditRef/Reference.lean", str(diff_out)]
            exact_cmd = [sys.executable, "-I", str(audit / "check_reference_exact.py"), cli_ns,
                         "AuditRef/Reference.lean", cli_eucl, cli_3d, str(exact_out)]
            diff = subprocess.run(diff_cmd, cwd=openai, capture_output=True, text=True, encoding="utf-8", errors="replace")
            exact = subprocess.run(exact_cmd, cwd=openai, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if diff.returncode != 0 or exact.returncode != 0:
                errors.append("rejeu d'un contrôleur de transfert en échec")
            diff_report = load_json(diff_out) if diff_out.is_file() else None
            exact_report = load_json(exact_out) if exact_out.is_file() else None
            errors.extend(validate_reference_diff_report(diff_report))
            errors.extend(validate_reference_exact_report(exact_report))
            if diff_report != load_json(logs / "reference-diff.json"):
                errors.append("reference-diff.json ne correspond pas au rejeu indépendant")
            if exact_report != load_json(logs / "reference-exact.json"):
                errors.append("reference-exact.json ne correspond pas au rejeu exact")
            if diff.stdout.encode("utf-8") != (logs / "reference-diff.log").read_bytes():
                errors.append("reference-diff.log ne correspond pas au rejeu")
            if exact.stdout.encode("utf-8") != (logs / "reference-exact.log").read_bytes():
                errors.append("reference-exact.log ne correspond pas au rejeu")
            # Rejoue les dix falsifications et vérifie le rapport exhaustif.
            selftest_report = tmp / "reference-diff-autotest.json"
            selftest_cmd = [sys.executable, "-I", str(audit / "test_reference_diff.py"),
                            str(audit / "check_reference_diff.py"), cli_ns, cli_eucl, cli_3d,
                            "AuditRef/Reference.lean", str(selftest_report)]
            selftest = subprocess.run(selftest_cmd, cwd=openai, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if selftest.returncode != 0 or not selftest_report.is_file():
                errors.append("autotest des dix falsifications en échec")
            else:
                report = load_json(selftest_report)
                errors.extend(validate_autotest_report(report))
                if report != load_json(logs / "reference-diff-autotest.json"):
                    errors.append("rapport d'autotest conservé différent du rejeu")
            if (selftest.stdout + selftest.stderr).encode("utf-8") != (logs / "reference-diff-autotest.log").read_bytes():
                errors.append("reference-diff-autotest.log ne correspond pas au rejeu")
            # Diff reproduit avec les chemins relatifs de la CI.
            diff_cmd = ["diff", "-u", cli_ns, "AuditRef/Reference.lean"]
            diff_proc = subprocess.run(diff_cmd, cwd=openai, capture_output=True)
            if diff_proc.returncode not in (0, 1) or diff_proc.stdout != (logs / "reference.diff").read_bytes():
                errors.append("reference.diff ne correspond pas au diff réel de la CI")
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        errors.append(f"rejeu du transfert impossible : {type(exc).__name__}")


def verify_axiom_files(logs: Path, root: Path, complement: str | None, errors: list[str]) -> None:
    """Recalcule un rapport d'axiomes à partir des journaux Lean et le compare au rapport sauvé.
    `complement` vaut None (verdict 1) ou une clé de COMPLEMENTS ; `True`/`False` restent acceptés."""
    if complement is True:
        complement = "CLASSICAL"
    elif complement is False:
        complement = None
    main_logs = [logs / "reference.log", logs / "bridge.log"]
    if complement:
        _, lean_log, report_name, report_log, _ = COMPLEMENTS[complement]
        main_logs.append(logs / lean_log)
        output, log_name = logs / report_name, report_log
    else:
        output, log_name = logs / "axioms.json", "axioms.log"
    try:
        from audit_validation import expected_theorems, make_axioms_report, validate_axioms_report
        report = make_axioms_report(main_logs, complement=complement)
        errors.extend(validate_axioms_report(report, expected_theorems(complement)))
        saved = load_json(output)
        if saved != report:
            errors.append(f"{output.name} ne concorde pas avec les journaux Lean relus")
        log_text = (logs / log_name).read_text(encoding="utf-8", errors="replace")
        if json.loads(log_text) != report:
            errors.append(f"{log_name} ne concorde pas avec le rapport JSON recalculé")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"validation des axiomes impossible : {type(exc).__name__}")


def verify_human_extracts(logs: Path, errors: list[str]) -> None:
    try:
        excerpts = (logs / "extraits-enonce.txt").read_text(encoding="utf-8", errors="replace")
        required_excerpt = (
            "=== Energie (condition 7 de Fefferman) ===",
            "globally_bounded_energy",
            "=== Periodicite de la pression (alternative D seulement) ===",
            "isOnePeriodic_pressure",
        )
        if any(piece not in excerpts for piece in required_excerpt):
            errors.append("extraits-enonce.txt incomplet ou sans les clauses Lean attendues")
        proof_excerpt = (logs / "lemme-8-6.txt").read_text(encoding="utf-8", errors="replace")
        required_proof = ("Lemme 8.6 / eq. (8.19)", "norm_derivativeWord_inverse_le", "PressureFlux")
        if any(piece not in proof_excerpt for piece in required_proof):
            errors.append("lemme-8-6.txt incomplet ou sans les références attendues")
        if re.search(r"No such file|grep: .*error|Traceback|\bfake\b|\bfixture\b", excerpts + proof_excerpt, re.I):
            errors.append("extraits humains contiennent une erreur ou un contenu de test")
    except OSError:
        errors.append("extraits humains illisibles")


def verify_negative_tests(root: Path, logs: Path, errors: list[str]) -> None:
    try:
        test_log = logs / "contradictory-tests.log"
        saved = test_log.read_bytes()
        # Nombre attendu calculé depuis les sources des tests (méthodes test_*), et non figé :
        # ajouter un test ne casse pas la vérification, en retirer un est détecté.
        expected = sum(
            len(re.findall(r"^\s+def test_\w+\(", p.read_text(encoding="utf-8"), flags=re.M))
            for p in sorted((root / "audit" / "tests").glob("test_*.py"))
        )
        if expected == 0 or f"Ran {expected} tests".encode() not in saved or not saved.rstrip().endswith(b"OK"):
            errors.append(f"contradictory-tests.log n'atteste pas le succès des {expected} tests attendus")
        replay = subprocess.run(
            [sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=root / "audit", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
        )
        if replay.returncode != 0:
            errors.append("rejeu des tests contradictoires en échec")
        normalize = lambda b: re.sub(rb"Ran ([0-9]+) tests? in [0-9.]+s", rb"Ran \1 tests in <TIME>", b)
        if normalize(replay.stdout) != normalize(saved):
            errors.append("contradictory-tests.log diffère du rejeu indépendant")
    except OSError as exc:
        errors.append(f"tests contradictoires illisibles ou non rejouables : {type(exc).__name__}")


def verify_main_evidence(logs: Path, root: Path, env: dict[str, str], errors: list[str]) -> dict[str, str]:
    check_required_main_files(logs, errors)
    actual = {}
    commits = logs / "commits.txt"
    if commits.is_file():
        actual = parse_commits(commits, root, env, errors)
    errors.extend(validate_github_context(env, actual))
    verify_lean_build(root, logs, errors)
    try:
        path_map, path_errors = parse_source_paths((logs / "source-paths.txt").read_text(encoding="utf-8"))
        errors.extend(path_errors)
        for key, rel in path_map.items():
            if not (root / rel).is_file():
                errors.append(f"source DeepMind absente : {rel}")
        audit_files = tracked_audit_files(root / "audit")
        manifest = (logs / "sources.sha256").read_text(encoding="utf-8")
        expected_paths = set(path_map.values())
        errors.extend(verify_manifest(root, manifest, audit_files, expected_paths))
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        errors.append(f"manifeste ou inventaire Git invalide : {type(exc).__name__}")
        path_map = {}
    run_reference_rechecks(root, logs, path_map, errors)
    verify_human_extracts(logs, errors)
    verify_negative_tests(root, logs, errors)
    replay_lean_log(root, logs, ["lake", "env", "lean", "AuditRef/Reference.lean"], "reference.log", errors)
    replay_lean_log(root, logs, ["lake", "env", "lean", "../audit/BoundaryBridge.lean"], "bridge.log", errors)
    verify_axiom_files(logs, root, None, errors)
    return actual


COMPLEMENT_LABELS = {
    "CLASSICAL": "pont classique (C) et (D) et 5 maillons de la chaîne d'OpenAI",
    "WITNESS": "témoin explicite de (C) : u° = 0, force lisse sur ℝ × ℝ³, support compact dans {t > 0}",
    "ENERGY": "condition (7) en intégrale étendue ⇒ champs d'énergie d'OpenAI",
}


def verify_complement(logs: Path, root: Path, key: str, status: str) -> tuple[str, list[str]]:
    """Vérifie un complément sans effet sur le verdict 1 : journaux présents, rejeu Lean,
    rapport d'axiomes recalculé et identique au rapport sauvé."""
    lean_file, lean_log, report_name, report_log, _ = COMPLEMENTS[key]
    if status == "skipped":
        return "NON EXÉCUTÉ", []
    if status == "failed":
        return f"ÉCHEC — {lean_file} non certifié", []
    if status != "success":
        return "PREUVES INSUFFISANTES — statut invalide", [f"statut {key} invalide"]
    errors: list[str] = []
    for name in (lean_log, report_name, report_log):
        require_file(logs, name, errors)
    if not errors:
        verify_axiom_files(logs, root, key, errors)
        replay_lean_log(root, logs, ["lake", "env", "lean", f"../audit/{lean_file}"], lean_log, errors)
        text = (logs / lean_log).read_text(encoding="utf-8", errors="replace")
        if re.search(r"\berror:", text) or "sorryAx" in text:
            errors.append(f"{lean_log} contient une erreur ou sorryAx")
    if errors:
        return f"PREUVES INSUFFISANTES — {lean_file} non validé", errors
    return f"CERTIFIÉ COMME COMPLÉMENT — {COMPLEMENT_LABELS[key]}", []


def verify_classical(logs: Path, root: Path, status: str) -> tuple[str, list[str]]:
    """Compatibilité avec la v3 initiale : délègue à verify_complement."""
    verdict, errors = verify_complement(logs, root, "CLASSICAL", status)
    if verdict.startswith("CERTIFIÉ"):
        return "CERTIFIÉ COMME COMPLÉMENT RESTREINT — (C) et (D)", errors
    return verdict, errors


def classify_main(status: dict[str, str], errors: list[str], logs: Path, root: Path, env: dict[str, str]) -> tuple[str, str, dict[str, str]]:
    if status.get("BUILD") == "failed":
        return "ERREUR D'INFRASTRUCTURE", "lake build a été exécuté et a échoué", {}
    if status.get("BUILD") != "success":
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "compilation complète non exécutée ou statut invalide", {}
    if status.get("GENERATION") == "failed":
        return ("GÉNÉRATION DE LA RÉFÉRENCE IMPOSSIBLE",
                "sources DeepMind absentes ou ambiguës, ou make_reference.py en échec : technique, "
                "aucune conclusion (voir reference-generate.log)", {})
    if status.get("GENERATION") != "success":
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "génération de la référence ignorée ou statut invalide", {}
    if status.get("REFDIFF") == "failed":
        for filename in ("reference-diff.json", "reference-exact.json"):
            try:
                report = load_json(logs / filename)
                if not isinstance(report, dict) or report.get("schema_version") != 1 or report.get("ok") is not False:
                    continue
                expected_keys = (
                    {"schema_version", "ok", "problemes", "differences_autorisees", "source_sha256", "generated_sha256"}
                    if filename == "reference-diff.json"
                    else {"schema_version", "ok", "problemes", "source_sha256", "generated_sha256"}
                )
                hashes_ok = all(re.fullmatch(r"[0-9a-f]{64}", str(report.get(key, ""))) for key in ("source_sha256", "generated_sha256"))
                diff_shape_ok = filename != "reference-diff.json" or (isinstance(report.get("differences_autorisees"), list))
                if set(report) == expected_keys and isinstance(report.get("problemes"), list) and report["problemes"] and hashes_ok and diff_shape_ok:
                    return "TRANSFORMATION DE RÉFÉRENCE REJETÉE", f"un rapport valide signale une différence : {filename}", {}
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        return "CONTRÔLE DE TRANSFORMATION NON VALIDÉ", "un contrôleur ou son autotest a échoué sans différence établie", {}
    if status.get("REFDIFF") != "success":
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "contrôle de transformation ignoré ou statut invalide", {}
    if status.get("REFERENCE") == "failed":
        return "ÉCHEC DU TRANSFERT (CAUSE INDÉTERMINÉE)", "compilation Lean de Reference.lean exécutée et en échec", {}
    if status.get("REFERENCE") != "success":
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "transfert Lean ignoré ou statut invalide", {}
    if status.get("BRIDGE") == "failed":
        return "ERREUR DU LEMME D'AUDIT", "compilation du pont BoundaryBridge exécutée et en échec", {}
    if status.get("BRIDGE") != "success":
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "pont de régularité ignoré ou statut invalide", {}
    if status.get("AXIOMS") == "failed":
        return "CONTRÔLE DES AXIOMES NON VALIDÉ", "contrôle exécuté et en échec", {}
    if status.get("AXIOMS") != "success":
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "contrôle des axiomes ignoré ou statut invalide", {}
    errors.extend(load_statuses(logs)[1])
    actual = verify_main_evidence(logs, root, env, errors)
    if errors:
        return "PREUVES D'EXÉCUTION INSUFFISANTES", "; ".join(sorted(set(errors))), actual
    return "CERTIFIÉ", "journaux, sources, rapports et manifestes recalculés et cohérents", actual


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage : verdict.py DOSSIER_JOURNAUX")
    logs = Path(sys.argv[1]).resolve()
    root = logs.parent
    env = dict(os.environ)
    statuses, status_errors = load_statuses(logs)
    main_errors = list(status_errors)
    try:
        main_verdict, main_nature, actual = classify_main(statuses, main_errors, logs, root, env)
    except Exception as exc:  # garde-fou : un certificat de refus est toujours écrit
        main_verdict = "PREUVES D'EXÉCUTION INSUFFISANTES"
        main_nature = f"exception imprévue pendant la validation : {type(exc).__name__}"
        main_errors.append(main_nature)
        actual = {}
    if status_errors and main_verdict == "CERTIFIÉ":
        main_verdict = "PREUVES D'EXÉCUTION INSUFFISANTES"
        main_nature = "; ".join(status_errors)
    classical_verdict, classical_errors = verify_classical(logs, root, statuses.get("CLASSICAL", "skipped"))
    complements = {}
    for key in COMPLEMENTS:
        verdict_c, errors_c = verify_complement(logs, root, key, statuses.get(key, "skipped"))
        complements[key] = {
            "fichier": COMPLEMENTS[key][0],
            "objet": COMPLEMENT_LABELS[key],
            "verdict": verdict_c,
            "erreurs_validation": sorted(set(errors_c)),
        }

    run_id = env.get("GITHUB_RUN_ID", "")
    server = env.get("GITHUB_SERVER_URL", "")
    repository = env.get("GITHUB_REPOSITORY", "")
    cert = {
        "schema_version": 3,
        "verdict_1_certification_lean": {
            "verdict": main_verdict,
            "nature": main_nature,
            "etapes": statuses,
            "revisions_reelles": actual,
            "erreurs_validation": sorted(set(main_errors)),
        },
        "certification_pont_classique_separee": {
            "verdict": classical_verdict,
            "erreurs_validation": sorted(set(classical_errors)),
            "sans_effet_sur_verdict_1": True,
        },
        "certification_complements_separee": {
            "sans_effet_sur_verdict_1": True,
            "complements": complements,
        },
        "verdict_2_correspondance_clay": {
            "verdict": "À VALIDER HUMAINEMENT",
            "valide": False,
            "obligations_ouvertes": [
                "Correspondance exacte avec la définition C∞ sur le demi-espace et portée du prolongement de Seeley",
                "Lecture officielle des errata de périodicité de la pression pour (D)",
                "Identification de la dérivée unilatérale à t=0 dans l'interprétation de l'énoncé Clay",
                "Validation humaine clause par clause; aucun verdict automatique ne la remplace",
            ],
        },
        "commits": actual,
        "lean": (logs / "lean-version.txt").read_text(encoding="utf-8", errors="replace").strip()
        if (logs / "lean-version.txt").is_file() else None,
        "execution": {
            "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "github_run_id": run_id or None,
            "github_repository": repository or None,
            "github_sha": env.get("GITHUB_SHA"),
            "github_run": f"{server}/{repository}/actions/runs/{run_id}" if server and repository and run_id else None,
        },
        "empreintes_sha256": {
            p.name: sha256_file(p) for p in sorted(logs.iterdir()) if p.is_file() and p.name != "certificat.json"
        } if logs.is_dir() else {},
    }
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "certificat.json").write_text(json.dumps(cert, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(cert, ensure_ascii=False, indent=2))
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"# Verdict 1 — {main_verdict}\n\n{main_nature}\n\n")
            fh.write("# Compléments (sans effet sur le verdict 1)\n\n")
            for item in complements.values():
                fh.write(f"- {item['fichier']} — {item['verdict']}\n")
            fh.write("\n")
            fh.write("# Verdict 2 — À VALIDER HUMAINEMENT\n\n")
            for item in cert["verdict_2_correspondance_clay"]["obligations_ouvertes"]:
                fh.write(f"- {item}\n")
    return 0 if main_verdict == "CERTIFIÉ" else 1


if __name__ == "__main__":
    raise SystemExit(main())
