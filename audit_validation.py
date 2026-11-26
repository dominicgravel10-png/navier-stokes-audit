#!/usr/bin/env python3
"""Contrôles stricts et sans effet de bord des pièces de l'audit Navier–Stokes v3."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

EXPECTED_OPENAI = "f9e8bc5b38b6e212696e8a30e3e91517af887bbd"
EXPECTED_DEEPMIND = "8bf45ed70d48b2b2a501de9c00b26bfa38c573ee"
EXPECTED_LEAN_VERSION = "4.34.0-rc2"
EXPECTED_LEAN_COMMIT = "6a10ac8c22beadecabdbb0919c2b50214762f91d"
EXPECTED_ELAN_SOURCE = "https://raw.githubusercontent.com/leanprover/elan/55dc2814ca42ace25f05ba4dd7a43a8c701a0549/elan-init.sh"
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
MAIN_THEOREMS = (
    "NavierStokes.Comparator.navier_stokes_breakdown_R3",
    "NavierStokes.Comparator.navier_stokes_breakdown_periodic",
    "Audit.uniqueDiffOn_halfspace",
    "Audit.contDiffOn_of_extension",
    "Audit.smooth_field_of_extension",
    "Audit.ExtensionSolution.toLean",
    "Audit.breakdown_R3_extension_version",
    "AuditRef.navier_stokes_breakdown_R3",
    "AuditRef.navier_stokes_breakdown_periodic",
)
CLASSICAL_THEOREMS = (
    "AuditClassical.differentiable_time_slice",
    "AuditClassical.derivWithin_Ici_eq_deriv",
    "AuditClassical.ClassicalSolutionR3.toLean",
    "AuditClassical.breakdown_R3_classical",
    "AuditClassical.ClassicalSolutionPeriodic.toLean",
    "AuditClassical.breakdown_periodic_classical",
    "NavierStokesR3.WholeSpaceUniqueness.classical_uniqueness_on_Icc",
    "NavierStokesR3.WholeSpaceUniqueness.candidate_global_agrees_before_one",
    "NavierStokesR3.ProblemStatement.CandidateProperties.no_global_solution_one",
    "NavierStokesR3.theorem_1_1",
    "NavierStokesR3.comparator_of_breakdown",
)
EXTERNAL_MANIFEST_PATHS = {
    "deepmind/FormalConjectures/Millenium/NavierStokes.lean",
    "deepmind/FormalConjecturesForMathlib/Geometry/Euclidean.lean",
    "deepmind/FormalConjecturesForMathlib/Geometry/3d.lean",
    "openai-src/NavierStokes/ComparatorDefinitions.lean",
    "openai-src/NavierStokes/ComparatorSolution.lean",
    "openai-src/lean-toolchain",
    "openai-src/lake-manifest.json",
}
STATUS_KEYS = ("CACHE", "BUILD", "REFDIFF", "REFERENCE", "BRIDGE", "CLASSICAL", "AXIOMS")
VALID_STATUSES = {"success", "failed", "skipped"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def validate_installer_evidence(source: str, installer: bytes, checksum: str, log: str) -> list[str]:
    errors: list[str] = []
    if source.strip() != EXPECTED_ELAN_SOURCE:
        errors.append("source de l'installateur elan non épinglée au commit attendu")
    if checksum.strip() != f"{sha256_bytes(installer)}  elan-init.sh":
        errors.append("empreinte de l'installateur elan incohérente")
    if not installer.startswith(b"#!/") or not installer.strip():
        errors.append("installateur elan absent ou mal formé")
    if "elan" not in log.lower():
        errors.append("journal d'installation elan sans preuve exploitable")
    return errors


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_axioms_report(report: Any, expected: Iterable[str]) -> list[str]:
    errors: list[str] = []
    expected_set = set(expected)
    required_keys = {"schema_version", "expected_theoremes", "axiomes_autorises", "theoremes", "sorry", "erreurs_lean", "journaux_sha256", "problemes", "ok"}
    if not isinstance(report, dict) or set(report) != required_keys:
        return ["schéma axiomes.json incorrect"]
    if type(report["schema_version"]) is not int or report["schema_version"] != 2:
        errors.append("version de schéma axiomes.json incorrecte")
    if report["expected_theoremes"] != sorted(expected_set):
        errors.append("liste de théorèmes attendue incorrecte")
    if report["axiomes_autorises"] != sorted(STANDARD_AXIOMS):
        errors.append("liste des axiomes autorisés incorrecte")
    declarations = report["theoremes"]
    if not isinstance(declarations, dict) or set(declarations) != expected_set:
        errors.append("ensemble de théorèmes absent, supplémentaire ou différent")
    else:
        for name in sorted(expected_set):
            entry = declarations[name]
            if not isinstance(entry, dict) or set(entry) != {"axiomes", "hors_standard"}:
                errors.append(f"entrée mal formée pour {name}")
                continue
            axioms = entry["axiomes"]
            if not isinstance(axioms, list) or any(not isinstance(a, str) for a in axioms):
                errors.append(f"liste d'axiomes mal formée pour {name}")
                continue
            if len(axioms) != len(set(axioms)):
                errors.append(f"axiome dupliqué pour {name}")
            if not set(axioms) <= STANDARD_AXIOMS:
                errors.append(f"axiome hors liste autorisée pour {name}")
            if entry["hors_standard"] != sorted(set(axioms) - STANDARD_AXIOMS):
                errors.append(f"champ hors_standard incohérent pour {name}")
    if report["sorry"] is not False:
        errors.append("sorry détecté ou indicateur sorry invalide")
    if type(report["erreurs_lean"]) is not int or report["erreurs_lean"] != 0:
        errors.append("erreurs Lean détectées ou compteur invalide")
    hashes = report["journaux_sha256"]
    if not isinstance(hashes, dict) or not hashes or any(
        not isinstance(k, str) or not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v)
        for k, v in hashes.items()
    ):
        errors.append("empreintes des journaux absentes ou mal formées")
    if report["ok"] is not True:
        errors.append("axioms.json ne donne pas ok=true")
    if report["problemes"] != []:
        errors.append("axioms.json contient des problèmes")
    return errors


def validate_reference_diff_report(report: Any) -> list[str]:
    if not isinstance(report, dict) or set(report) != {
        "schema_version", "ok", "problemes", "differences_autorisees", "source_sha256", "generated_sha256"
    }:
        return ["schéma reference-diff.json incorrect"]
    errors = []
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        errors.append("version de schéma reference-diff.json incorrecte")
    if report["ok"] is not True or report["problemes"] != []:
        errors.append("le contrôle textuel de Reference.lean n'est pas validé")
    allowed = report["differences_autorisees"]
    if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) or not x.strip() for x in allowed):
        errors.append("liste des transformations autorisées absente ou mal formée")
    for key in ("source_sha256", "generated_sha256"):
        if not isinstance(report[key], str) or not re.fullmatch(r"[0-9a-f]{64}", report[key]):
            errors.append(f"empreinte {key} absente ou mal formée")
    return errors


def validate_reference_exact_report(report: Any) -> list[str]:
    if not isinstance(report, dict) or set(report) != {"schema_version", "ok", "problemes", "source_sha256", "generated_sha256"}:
        return ["schéma reference-exact.json incorrect"]
    errors = []
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        errors.append("version de schéma reference-exact.json incorrecte")
    if report["ok"] is not True or report["problemes"] != []:
        errors.append("la comparaison exacte de Reference.lean n'est pas validée")
    for key in ("source_sha256", "generated_sha256"):
        if not isinstance(report[key], str) or not re.fullmatch(r"[0-9a-f]{64}", report[key]):
            errors.append(f"empreinte {key} absente ou mal formée")
    return errors


def validate_autotest_report(report: Any) -> list[str]:
    if not isinstance(report, dict) or set(report) != {"schema_version", "ok", "authentique_accepte", "cas", "nombre_falsifications"}:
        return ["schéma reference-diff-autotest.json incorrect"]
    errors = []
    labels = {
        "temps strict dans l'équation", "axiome ajouté", "notation ℝ³ altérée",
        "champ d'énergie neutralisé", "énoncé (C) affaibli", "sorry réintroduit",
        "set_option ajouté", "preuve modifiée", "#print axioms retiré", "attribut simp retiré",
    }
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        errors.append("version de schéma de l'autotest incorrecte")
    if report["ok"] is not True or report["authentique_accepte"] is not True:
        errors.append("autotest de transformations non validé")
    if type(report["nombre_falsifications"]) is not int or report["nombre_falsifications"] != 10:
        errors.append("le nombre de falsifications n'est pas 10")
    cases = report["cas"]
    if not isinstance(cases, list) or len(cases) != 10:
        errors.append("liste des falsifications absente ou incomplète")
    else:
        names = [c.get("nom") if isinstance(c, dict) else None for c in cases]
        if set(names) != labels or len(names) != len(set(names)):
            errors.append("la liste des falsifications ne correspond pas aux dix cas attendus")
        for case in cases:
            if not isinstance(case, dict) or set(case) != {"nom", "applicable", "rejetee"} or case.get("applicable") is not True or case.get("rejetee") is not True:
                errors.append("une falsification n'a pas été appliquée et rejetée")
                break
    return errors


def validate_commit_record(text: str, actual: Mapping[str, str], github_sha: str) -> list[str]:
    errors: list[str] = []
    expected_keys = {"OPENAI", "DEEPMIND", "AUDIT"}
    pairs = []
    for raw in text.splitlines():
        if not raw or "=" not in raw:
            errors.append("ligne invalide dans commits.txt")
            continue
        pairs.append(raw.split("=", 1))
    keys = [pair[0] for pair in pairs]
    if set(keys) != expected_keys or len(keys) != 3 or len(set(keys)) != 3:
        errors.append("commits.txt ne contient pas exactement OPENAI, DEEPMIND et AUDIT")
        return errors
    record = dict(pairs)
    for name in expected_keys:
        value = record[name]
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            errors.append(f"SHA {name} invalide")
        if actual.get(name) != value:
            errors.append(f"SHA {name} différent de la révision réellement extraite")
    if record["OPENAI"] != EXPECTED_OPENAI:
        errors.append("révision OpenAI non verrouillée")
    if record["DEEPMIND"] != EXPECTED_DEEPMIND:
        errors.append("révision DeepMind non verrouillée")
    if record["AUDIT"] != github_sha:
        errors.append("révision d'audit différente de GITHUB_SHA")
    return errors


def parse_manifest(text: str) -> tuple[dict[str, str], list[str]]:
    entries: dict[str, str] = {}
    errors: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"ligne {number} du manifeste mal formée")
            continue
        digest, rel = match.groups()
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts or "\\" in rel or "\x00" in rel:
            errors.append(f"chemin non autorisé dans le manifeste : {rel}")
            continue
        if rel in entries:
            errors.append(f"chemin dupliqué dans le manifeste : {rel}")
            continue
        entries[rel] = digest
    if not entries:
        errors.append("manifeste vide")
    return entries, errors


def verify_manifest(workspace: Path, manifest_text: str, audit_files: Iterable[str], source_paths: Iterable[str]) -> list[str]:
    entries, errors = parse_manifest(manifest_text)
    expected = {f"audit/{p}" for p in audit_files} | set(EXTERNAL_MANIFEST_PATHS) | set(source_paths)
    actual_names = set(entries)
    missing = sorted(expected - actual_names)
    extra = sorted(actual_names - expected)
    if missing:
        errors.append("manifeste incomplet : " + ", ".join(missing))
    if extra:
        errors.append("chemins inattendus dans le manifeste : " + ", ".join(extra))
    for rel, expected_hash in entries.items():
        path = workspace / rel
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(workspace.resolve())
            if not resolved.is_file():
                errors.append(f"entrée de manifeste non fichier : {rel}")
            elif sha256_file(resolved) != expected_hash:
                errors.append(f"empreinte invalide : {rel}")
        except (OSError, ValueError):
            errors.append(f"fichier du manifeste absent ou hors espace : {rel}")
    return errors


def git_head(directory: Path) -> str:
    result = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"], text=True, capture_output=True, check=True)
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError(f"SHA git invalide pour {directory}")
    return value


def tracked_audit_files(audit: Path) -> set[str]:
    result = subprocess.run(["git", "-C", str(audit), "ls-files", "-z"], capture_output=True, check=True)
    return {p.decode("utf-8") for p in result.stdout.split(b"\0") if p}


def parse_source_paths(text: str) -> tuple[dict[str, str], list[str]]:
    required = {"NavierStokes", "Euclidean", "3d"}
    out: dict[str, str] = {}
    errors: list[str] = []
    for line in text.splitlines():
        if "=" not in line:
            errors.append("ligne invalide dans source-paths.txt")
            continue
        key, value = line.split("=", 1)
        if key not in required or key in out:
            errors.append("clé absente, supplémentaire ou dupliquée dans source-paths.txt")
            continue
        value = value.strip()
        if value.startswith("../") or Path(value).is_absolute() or ".." in Path(value).parts:
            errors.append(f"chemin DeepMind non canonique : {value}")
            continue
        out[key] = value
    if set(out) != required:
        errors.append("source-paths.txt ne contient pas exactement les trois sources DeepMind")
    expected_stems = {
        "NavierStokes": "deepmind/FormalConjectures/Millenium/NavierStokes.lean",
        "Euclidean": "deepmind/FormalConjecturesForMathlib/Geometry/Euclidean.lean",
        "3d": "deepmind/FormalConjecturesForMathlib/Geometry/3d.lean",
    }
    for key, value in out.items():
        if value != expected_stems[key]:
            errors.append(f"source {key} différente du chemin verrouillé")
    return out, errors


def make_axioms_report(log_paths: Iterable[Path], include_classical: bool = False) -> dict[str, Any]:
    expected = set(MAIN_THEOREMS)
    if include_classical:
        expected.update(CLASSICAL_THEOREMS)
    text_parts = [p.read_text(encoding="utf-8", errors="replace") for p in log_paths]
    text = "\n".join(text_parts)
    flat = re.sub(r"\s*\n\s*", " ", text)
    depends = re.compile(r"'([^']+)' depends on axioms: \[([^\]]*)\]")
    no_axioms = re.compile(r"'([^']+)' does not depend on any axioms")
    sorry_warning = re.compile(r"declaration uses ['`‘’]sorry['`‘’]")
    parsed: dict[str, list[set[str]]] = {}
    for name, axioms in depends.findall(flat):
        parsed.setdefault(name, []).append({a.strip() for a in axioms.split(",") if a.strip()})
    for name in no_axioms.findall(flat):
        parsed.setdefault(name, []).append(set())
    found = set(parsed)
    errors = []
    if found != expected:
        errors.append("ensemble de déclarations #print axioms inattendu")
    theorem_report: dict[str, Any] = {}
    for name in sorted(expected):
        entries = parsed.get(name, [])
        if len(entries) != 1:
            errors.append(f"déclaration absente ou dupliquée : {name}")
            theorem_report[name] = {"axiomes": [], "hors_standard": []}
            continue
        axioms = entries[0]
        outside = axioms - STANDARD_AXIOMS
        if outside:
            errors.append(f"axiomes hors liste autorisée : {name}")
        theorem_report[name] = {"axiomes": sorted(axioms), "hors_standard": sorted(outside)}
    sorry = bool(sorry_warning.search(flat)) or bool(re.search(r"\bsorryAx\b", flat))
    lean_errors = len(re.findall(r"\berror:", text))
    if sorry:
        errors.append("avertissement sorry ou sorryAx détecté")
    if lean_errors:
        errors.append("erreur Lean détectée")
    log_hashes = {p.name: sha256_file(p) for p in log_paths}
    return {
        "schema_version": 2,
        "expected_theoremes": sorted(expected),
        "axiomes_autorises": sorted(STANDARD_AXIOMS),
        "theoremes": theorem_report,
        "sorry": sorry,
        "erreurs_lean": lean_errors,
        "journaux_sha256": log_hashes,
        "ok": not errors,
        "problemes": errors,
    }


def validate_github_context(env: Mapping[str, str], actual: Mapping[str, str]) -> list[str]:
    errors = []
    if env.get("GITHUB_ACTIONS") != "true":
        errors.append("exécution hors GitHub Actions")
    if env.get("GITHUB_REPOSITORY") != "dominicgravel10-png/navier-stokes-audit":
        errors.append("dépôt GitHub inattendu")
    if env.get("GITHUB_SERVER_URL") != "https://github.com":
        errors.append("serveur GitHub inattendu")
    if not re.fullmatch(r"[0-9]+", env.get("GITHUB_RUN_ID", "")):
        errors.append("identifiant de run GitHub absent ou invalide")
    github_sha = env.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[0-9a-f]{40}", github_sha):
        errors.append("GITHUB_SHA absent ou invalide")
    elif actual.get("AUDIT") != github_sha:
        errors.append("GITHUB_SHA ne correspond pas au checkout d'audit")
    return errors
