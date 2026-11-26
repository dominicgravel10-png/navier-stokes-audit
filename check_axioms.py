#!/usr/bin/env python3
"""Extrait et contrôle exact des sorties `#print axioms` du noyau Lean."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_validation import make_axioms_report, validate_axioms_report, MAIN_THEOREMS, CLASSICAL_THEOREMS


def main() -> int:
    args = sys.argv[1:]
    include_classical = False
    if args and args[0] == "--avec-classique":
        include_classical = True
        args.pop(0)
    if len(args) < 2:
        raise SystemExit("Usage : check_axioms.py [--avec-classique] RAPPORT.json JOURNAL.log [JOURNAL.log ...]")
    output = Path(args[0])
    logs = [Path(p) for p in args[1:]]
    if any(not p.is_file() for p in logs):
        raise SystemExit("journal d'axiomes absent")
    report = make_axioms_report(logs, include_classical=include_classical)
    expected = list(MAIN_THEOREMS) + (list(CLASSICAL_THEOREMS) if include_classical else [])
    report["problemes"].extend(validate_axioms_report(report, expected))
    report["problemes"] = sorted(set(report["problemes"]))
    report["ok"] = not report["problemes"]
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
