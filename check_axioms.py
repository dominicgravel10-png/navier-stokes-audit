#!/usr/bin/env python3
"""Extrait et contrôle exact des sorties `#print axioms` du noyau Lean."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_validation import COMPLEMENTS, expected_theorems, make_axioms_report, validate_axioms_report


def main() -> int:
    args = sys.argv[1:]
    complement = None
    if args and args[0] == "--avec-classique":
        complement = "CLASSICAL"
        args.pop(0)
    elif len(args) >= 2 and args[0] == "--complement":
        complement = args[1]
        if complement not in COMPLEMENTS:
            raise SystemExit(f"complément inconnu : {complement}")
        args = args[2:]
    if len(args) < 2:
        raise SystemExit("Usage : check_axioms.py [--avec-classique | --complement CLE] "
                         "RAPPORT.json JOURNAL.log [JOURNAL.log ...]")
    output = Path(args[0])
    logs = [Path(p) for p in args[1:]]
    if any(not p.is_file() for p in logs):
        raise SystemExit("journal d'axiomes absent")
    report = make_axioms_report(logs, complement=complement)
    expected = expected_theorems(complement)
    report["problemes"].extend(validate_axioms_report(report, expected))
    report["problemes"] = sorted(set(report["problemes"]))
    report["ok"] = not report["problemes"]
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
