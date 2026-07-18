"""Validate PAMSPEC evidence-record chains against the R6 schema and
enforce the retraction-chain invariants.

Usage:
    python scripts/validate_evidence.py                     # validate all *.jsonl under validation/reports/
    python scripts/validate_evidence.py path/to/chain.jsonl [more.jsonl ...]

Exit status: 0 on success; non-zero on any schema or invariant failure.

R6.1 invariants enforced:
  1. Every record validates against conformance/schemas/evidence-record.schema.json.
  2. record_id values are unique within a chain file.
  3. controlled_experiment records MUST have control_design present.
  4. retracted records MUST have a superseding record with matching requirement_id
     and supersedes_claim = <retracted record_id>, appearing later in the file.
  5. supersedes_claim, when non-null, MUST reference a record_id present in the file
     with a matching requirement_id.
  6. classification and claim_status enums are enforced by the schema.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "evidence-record.schema.json"
DEFAULT_SEARCH_DIRS = [ROOT / "validation" / "reports"]
DEFAULT_GLOB = "evidence-chain-*.jsonl"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def iter_default_chains() -> list[Path]:
    paths: list[Path] = []
    for d in DEFAULT_SEARCH_DIRS:
        if d.exists():
            paths.extend(sorted(d.glob(DEFAULT_GLOB)))
    return paths


def validate_chain(path: Path, validator: Draft202012Validator) -> list[str]:
    errors: list[str] = []
    records: list[dict] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as e:
            errors.append(f"{path}:{lineno}: JSON decode error: {e}")
            continue
        schema_errors = list(validator.iter_errors(rec))
        for err in schema_errors:
            errors.append(f"{path}:{lineno}: schema: {err.message} at {list(err.absolute_path)}")
        if schema_errors:
            continue
        records.append(rec)

    seen_ids: set[str] = set()
    for rec in records:
        rid = rec["record_id"]
        if rid in seen_ids:
            errors.append(f"{path}: duplicate record_id '{rid}'")
        seen_ids.add(rid)

    for rec in records:
        if rec["test_kind"] == "controlled_experiment" and rec.get("control_design") is None:
            errors.append(
                f"{path}: record_id={rec['record_id']}: controlled_experiment "
                f"MUST have control_design (R6 invariant 3)"
            )

    id_to_rec = {r["record_id"]: r for r in records}
    for rec in records:
        sup = rec.get("supersedes_claim")
        if sup is None:
            continue
        if sup not in id_to_rec:
            errors.append(
                f"{path}: record_id={rec['record_id']}: supersedes_claim '{sup}' "
                f"does not reference a record_id present in this chain (R6 invariant 5)"
            )
            continue
        target = id_to_rec[sup]
        if target["requirement_id"] != rec["requirement_id"]:
            errors.append(
                f"{path}: record_id={rec['record_id']}: supersedes '{sup}' but "
                f"requirement_id differs ({target['requirement_id']} vs "
                f"{rec['requirement_id']}) (R6 invariant 5)"
            )

    superseded_by: dict[str, str] = {}
    for rec in records:
        sup = rec.get("supersedes_claim")
        if sup is not None:
            superseded_by.setdefault(sup, rec["record_id"])
    for rec in records:
        if rec["claim_status"] == "retracted":
            rid = rec["record_id"]
            if rid not in superseded_by:
                errors.append(
                    f"{path}: record_id={rid}: retracted record has no superseding "
                    f"record in this chain (R6 invariant 4)"
                )

    return errors


def main(argv: list[str]) -> int:
    validator = Draft202012Validator(load_schema())
    if len(argv) > 1:
        paths = [Path(a) for a in argv[1:]]
    else:
        paths = iter_default_chains()

    if not paths:
        print("validate_evidence: no evidence-chain files found (searched:",
              ", ".join(str(d) for d in DEFAULT_SEARCH_DIRS), ")")
        return 0

    all_errors: list[str] = []
    for p in paths:
        if not p.exists():
            all_errors.append(f"{p}: file not found")
            continue
        errs = validate_chain(p, validator)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK  {p}  ({sum(1 for _ in p.open(encoding='utf-8') if _.strip())} records)")

    if all_errors:
        print()
        print("EVIDENCE VALIDATION FAILED:")
        for e in all_errors:
            print(" -", e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
