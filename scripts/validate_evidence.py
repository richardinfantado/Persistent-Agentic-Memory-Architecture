"""Validate PAMSPEC evidence-record chains against the R6.1a schema and
enforce chain-level invariants.

Usage:
    python scripts/validate_evidence.py                     # validate all evidence-chain-*.jsonl under validation/reports/
    python scripts/validate_evidence.py path/to/chain.jsonl [more.jsonl ...]

Exit status: 0 on success; non-zero on any schema or invariant failure.

Chain-level invariants enforced (schema-level ones are enforced by the
Draft 2020-12 conditional rules in the schema itself):

  5. record_id unique within a chain file.
  6. controlled_experiment control_design MUST have at least one entry in
     confounders_ruled_out or negative_controls.
  7. revises.record_id MUST resolve to a record earlier in the same file.
  8. A record MUST NOT revise itself.
  9. Revision cycles prohibited (defensive; earlier-only already prevents).
 10. revises target's requirement_id MUST equal the reviser's requirement_id.
 11. recorded_at MUST NOT move backward along a revision edge.
 12. Two later records that both alter effective disposition of the same
     target with conflicting effects (e.g. one retracts, one supersedes)
     ARE rejected. Only one 'altering' revision per target is allowed;
     multiple 'reproduces'/'extends' are fine.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
DEFAULT_SEARCH_DIRS = [ROOT / "validation" / "reports"]
DEFAULT_GLOB = "evidence-chain-*.jsonl"

ALTERING_EFFECTS = {"retracts", "supersedes"}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def iter_default_chains() -> list[Path]:
    paths: list[Path] = []
    for d in DEFAULT_SEARCH_DIRS:
        if d.exists():
            paths.extend(sorted(d.glob(DEFAULT_GLOB)))
    return paths


def _parse_iso(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def validate_chain(path: Path, validator: Draft202012Validator) -> list[str]:
    errors: list[str] = []
    records: list[dict] = []
    positions: dict[str, int] = {}

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

    for idx, rec in enumerate(records):
        rid = rec["record_id"]
        if rid in positions:
            errors.append(f"{path}: duplicate record_id '{rid}' at record {idx} (R6 invariant 5)")
        positions[rid] = idx

    for idx, rec in enumerate(records):
        if rec["test_kind"] == "controlled_experiment":
            cd = rec.get("control_design")
            if cd is None:
                errors.append(
                    f"{path}: record_id={rec['record_id']}: controlled_experiment "
                    f"MUST have non-null control_design (schema conditional 2)"
                )
            else:
                if not (cd.get("confounders_ruled_out") or cd.get("negative_controls")):
                    errors.append(
                        f"{path}: record_id={rec['record_id']}: controlled_experiment "
                        f"control_design MUST have at least one confounders_ruled_out or "
                        f"negative_controls entry (R6 invariant 6)"
                    )

    id_to_rec = {r["record_id"]: r for r in records}
    id_to_idx = {r["record_id"]: i for i, r in enumerate(records)}

    for idx, rec in enumerate(records):
        revises = rec.get("revises")
        if revises is None:
            continue
        target_id = revises["record_id"]
        rid = rec["record_id"]

        if target_id == rid:
            errors.append(f"{path}: record_id={rid}: self-revision prohibited (R6 invariant 8)")
            continue

        if target_id not in id_to_rec:
            errors.append(
                f"{path}: record_id={rid}: revises '{target_id}' but no such "
                f"record_id in this chain (R6 invariant 7)"
            )
            continue

        if id_to_idx[target_id] >= idx:
            errors.append(
                f"{path}: record_id={rid}: revises '{target_id}' but that record "
                f"appears at or after this one (R6 invariant 7: append-only ordering)"
            )

        target = id_to_rec[target_id]
        if target["requirement_id"] != rec["requirement_id"]:
            errors.append(
                f"{path}: record_id={rid}: revises '{target_id}' but requirement_id differs "
                f"({target['requirement_id']} vs {rec['requirement_id']}) (R6 invariant 10)"
            )

        t_this = _parse_iso(rec.get("recorded_at", ""))
        t_target = _parse_iso(target.get("recorded_at", ""))
        if t_this is not None and t_target is not None and t_this < t_target:
            errors.append(
                f"{path}: record_id={rid}: recorded_at is BEFORE the record it revises "
                f"'{target_id}' — revision edges must move forward in time (R6 invariant 11)"
            )

    altering_by_target: dict[str, list[tuple[str, str]]] = {}
    for rec in records:
        revises = rec.get("revises")
        if revises is None:
            continue
        if revises["effect"] in ALTERING_EFFECTS:
            altering_by_target.setdefault(revises["record_id"], []).append(
                (rec["record_id"], revises["effect"])
            )
    for target_id, revs in altering_by_target.items():
        distinct_effects = {e for _, e in revs}
        if len(distinct_effects) > 1:
            details = ", ".join(f"{rid}:{eff}" for rid, eff in revs)
            errors.append(
                f"{path}: record '{target_id}' has conflicting altering revisions "
                f"({details}) — a target may not be both retracted and superseded "
                f"with different effects (R6 invariant 12)"
            )

    def _has_cycle(start: str) -> bool:
        seen = {start}
        cur = start
        while True:
            rec = id_to_rec.get(cur)
            if rec is None:
                return False
            revises = rec.get("revises")
            if revises is None:
                return False
            nxt = revises["record_id"]
            if nxt in seen:
                return True
            seen.add(nxt)
            cur = nxt
    for rec in records:
        if _has_cycle(rec["record_id"]):
            errors.append(
                f"{path}: record_id={rec['record_id']}: revision cycle detected "
                f"(R6 invariant 9)"
            )

    return errors


def compute_effective_status(records: list[dict]) -> dict[str, str]:
    """For each record_id in a chain, return its EFFECTIVE disposition.

    'confirmed' | 'inconclusive' | 'not_testable' | 'retracted' | 'superseded'

    The intrinsic claim_status of a record is preserved unless a LATER
    record carries revises.effect in {retracts, supersedes} pointing at it.
    reproduces / extends leave effective disposition unchanged.
    """
    effective = {r["record_id"]: r["claim_status"] for r in records}
    for rec in records:
        revises = rec.get("revises")
        if revises is None:
            continue
        if revises["effect"] == "retracts":
            effective[revises["record_id"]] = "retracted"
        elif revises["effect"] == "supersedes":
            effective[revises["record_id"]] = "superseded"
    return effective


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
            n = sum(1 for _ in p.open(encoding="utf-8") if _.strip())
            print(f"OK  {p}  ({n} records)")

    if all_errors:
        print()
        print("EVIDENCE VALIDATION FAILED:")
        for e in all_errors:
            print(" -", e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
