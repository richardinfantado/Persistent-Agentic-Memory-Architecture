"""Tests for the R6.1 evidence model.

Covers:
  - The schema itself is a valid JSON Schema (Draft 2020-12).
  - The V08 -> V08.1 reference retraction chain validates cleanly.
  - Invariant enforcement in scripts/validate_evidence.py catches:
      * missing supersede record for a retracted claim
      * supersede pointing at a nonexistent record_id
      * supersede pointing at a record with a different requirement_id
      * controlled_experiment without control_design
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "evidence-record.schema.json"
REFERENCE_CHAIN = ROOT / "validation" / "reports" / "evidence-chain-v08-derived-vector.jsonl"
VALIDATOR = ROOT / "scripts" / "validate_evidence.py"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_chain(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(_load_schema())


def test_reference_chain_validates_against_schema():
    v = Draft202012Validator(_load_schema())
    records = _load_chain(REFERENCE_CHAIN)
    assert len(records) == 2, "reference chain should be exactly two records (V08 probe + V08.1 controlled_experiment)"
    for rec in records:
        errors = list(v.iter_errors(rec))
        assert not errors, f"record {rec.get('record_id')} failed schema: {[e.message for e in errors]}"


def test_reference_chain_is_the_retraction_example():
    records = _load_chain(REFERENCE_CHAIN)
    v08 = next(r for r in records if r["record_id"] == "v08.scenario7.probe")
    v081 = next(r for r in records if r["record_id"] == "v08.1.scenario7.controlled_experiment")

    assert v08["claim_status"] == "retracted"
    assert v08["classification"] == "gap"
    assert v08["test_kind"] == "probe"
    assert v08["evidence_commit"].startswith("8871689")

    assert v081["claim_status"] == "confirmed"
    assert v081["classification"] == "native"
    assert v081["test_kind"] == "controlled_experiment"
    assert v081["supersedes_claim"] == "v08.scenario7.probe"
    assert v081["evidence_commit"].startswith("6ae806b")
    assert v081["requirement_id"] == v08["requirement_id"]
    assert v081["control_design"] is not None
    assert v081["control_design"]["control_count"] >= 5
    assert v081["control_design"]["direct_signal_captured"] is True


def _run_validator(tmp_path: Path, chain: list[dict]) -> subprocess.CompletedProcess:
    p = tmp_path / "chain.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in chain) + "\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(p)],
        capture_output=True,
        text=True,
    )


def _base_records() -> list[dict]:
    return copy.deepcopy(_load_chain(REFERENCE_CHAIN))


def test_validator_accepts_reference_chain():
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), str(REFERENCE_CHAIN)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


def test_validator_rejects_retracted_without_supersede(tmp_path):
    records = _base_records()
    records = records[:1]  # drop the superseding record
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "retracted record has no superseding record" in r.stdout


def test_validator_rejects_supersede_pointing_at_missing_id(tmp_path):
    records = _base_records()
    records[1]["supersedes_claim"] = "nonexistent-id"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "does not reference a record_id present" in r.stdout


def test_validator_rejects_supersede_across_requirement_ids(tmp_path):
    records = _base_records()
    records[1]["requirement_id"] = "PAMSPEC.some.other.requirement"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "requirement_id differs" in r.stdout


def test_validator_rejects_controlled_experiment_without_control_design(tmp_path):
    records = _base_records()
    records[1]["control_design"] = None
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "controlled_experiment MUST have control_design" in r.stdout
