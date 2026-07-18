"""Tests for the R6.1a evidence model.

Positive coverage:
  - Schema itself is a valid JSON Schema (Draft 2020-12).
  - The V08 -> V08.1 reference retraction chain validates cleanly.
  - The chain has the expected append-only shape: V08 record is
    claim_status='confirmed' (its author's assertion at the time),
    revises=null; V08.1 record carries revises.effect='retracts' pointing
    at V08.
  - Effective-status derivation reports V08 as 'retracted' even though
    its intrinsic claim_status remains 'confirmed'.

Negative coverage (each MUST cause validate_evidence.py to exit nonzero):
  - Missing intrinsic claim_status enum change (retracted or superseded
    used as an intrinsic status — schema rejects).
  - revises target does not exist.
  - revises across differing requirement_ids.
  - Self-revision.
  - Revision target appears AFTER the revising record (backward-ordered
    JSONL).
  - Revision cycle across three records.
  - Retraction reason empty.
  - controlled_experiment with empty confounder + negative-control lists.
  - Abbreviated (7-char) evidence_commit SHA.
  - Subject with empty name.
  - classification=not_testable but claim_status=confirmed.
  - Missing pamspec_context.spec_commit.
  - Two later records with conflicting altering effects (one retracts,
    one supersedes) on the same target.
  - Backward recorded_at along a revision edge.
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
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
REFERENCE_CHAIN = ROOT / "validation" / "reports" / "evidence-chain-v08-derived-vector.jsonl"
VALIDATOR = ROOT / "scripts" / "validate_evidence.py"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence  # noqa: E402


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_chain(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# ------- positive tests -------

def test_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(_load_schema())


def test_reference_chain_validates_against_schema():
    v = Draft202012Validator(_load_schema())
    records = _load_chain(REFERENCE_CHAIN)
    assert len(records) == 2
    for rec in records:
        errors = list(v.iter_errors(rec))
        assert not errors, f"{rec['record_id']} failed schema: {[e.message for e in errors]}"


def test_reference_chain_is_append_only_retraction():
    records = _load_chain(REFERENCE_CHAIN)
    v08 = next(r for r in records if r["record_id"] == "v08.scenario7.probe")
    v081 = next(r for r in records if r["record_id"] == "v08.1.scenario7.controlled_experiment")

    assert v08["claim_status"] == "confirmed", \
        "V08 record must preserve its authoring-time claim_status (append-only)"
    assert v08["revises"] is None
    assert v08["classification"] == "gap"
    assert v08["evidence_commit"] == "8871689b831480d8fd8980f4ed40c57c0a550c55"

    assert v081["claim_status"] == "confirmed"
    assert v081["revises"] is not None
    assert v081["revises"]["record_id"] == "v08.scenario7.probe"
    assert v081["revises"]["effect"] == "retracts"
    assert v081["revises"]["reason"], "retraction reason must be non-empty"
    assert v081["classification"] == "native"
    assert v081["evidence_commit"] == "6ae806bbeb591c82c91236a191514b1775f24dbf"


def test_effective_status_derivation():
    records = _load_chain(REFERENCE_CHAIN)
    effective = validate_evidence.compute_effective_status(records)
    assert effective["v08.scenario7.probe"] == "retracted"
    assert effective["v08.1.scenario7.controlled_experiment"] == "confirmed"


def test_validator_accepts_reference_chain():
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), str(REFERENCE_CHAIN)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


# ------- helpers for negative tests -------

def _base_records() -> list[dict]:
    return copy.deepcopy(_load_chain(REFERENCE_CHAIN))


def _run_validator(tmp_path: Path, records: list[dict]) -> subprocess.CompletedProcess:
    p = tmp_path / "chain.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(p)],
        capture_output=True, text=True,
    )


# ------- negative tests -------

def test_rejects_retracted_as_intrinsic_status(tmp_path):
    records = _base_records()
    records[0]["claim_status"] = "retracted"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "claim_status" in r.stdout or "enum" in r.stdout.lower() or "schema" in r.stdout


def test_rejects_missing_revises_target(tmp_path):
    records = _base_records()
    records[1]["revises"]["record_id"] = "nonexistent-id"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "no such record_id" in r.stdout or "R6 invariant 7" in r.stdout


def test_rejects_revises_across_requirement_ids(tmp_path):
    records = _base_records()
    records[1]["requirement_id"] = "PAMSPEC.some.other.requirement"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "requirement_id differs" in r.stdout or "R6 invariant 10" in r.stdout


def test_rejects_self_revision(tmp_path):
    records = _base_records()
    records[1]["revises"]["record_id"] = records[1]["record_id"]
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "self-revision" in r.stdout or "R6 invariant 8" in r.stdout


def test_rejects_forward_reference_when_target_appears_later(tmp_path):
    """Swap record order so the reviser appears BEFORE its target."""
    records = _base_records()
    reversed_records = [records[1], records[0]]
    r = _run_validator(tmp_path, reversed_records)
    assert r.returncode != 0
    assert "append-only ordering" in r.stdout or "R6 invariant 7" in r.stdout


def test_rejects_revision_cycle(tmp_path):
    """Construct a three-record cycle A -> B -> C -> A."""
    base = _base_records()[0]
    def _mk(rid, revises_target):
        rec = copy.deepcopy(base)
        rec["record_id"] = rid
        rec["revises"] = {"record_id": revises_target, "effect": "reproduces", "reason": "cycle probe"}
        return rec
    a = _mk("A", "C")
    b = _mk("B", "A")
    c = _mk("C", "B")
    r = _run_validator(tmp_path, [a, b, c])
    assert r.returncode != 0
    # The earlier-only rule fires first; either message is acceptable evidence of rejection.
    assert (
        "revision cycle" in r.stdout
        or "append-only ordering" in r.stdout
        or "R6 invariant" in r.stdout
    )


def test_rejects_empty_retraction_reason(tmp_path):
    records = _base_records()
    records[1]["revises"]["reason"] = ""
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0


def test_rejects_controlled_experiment_with_empty_controls(tmp_path):
    records = _base_records()
    cd = records[1]["control_design"]
    cd["confounders_ruled_out"] = []
    cd["negative_controls"] = []
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "at least one confounders_ruled_out or negative_controls" in r.stdout \
        or "R6 invariant 6" in r.stdout


def test_rejects_abbreviated_evidence_commit(tmp_path):
    records = _base_records()
    records[0]["evidence_commit"] = "8871689"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0


def test_rejects_empty_subject_name(tmp_path):
    records = _base_records()
    records[0]["subject"]["name"] = ""
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0


def test_rejects_not_testable_classification_with_confirmed_status(tmp_path):
    records = _base_records()
    records[0]["classification"] = "not_testable"
    records[0]["claim_status"] = "confirmed"
    records[0]["limitations"] = ["something"]  # bypass the limitations-required conditional
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0


def test_rejects_missing_spec_commit(tmp_path):
    records = _base_records()
    records[0]["pamspec_context"]["spec_commit"] = "abc"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0


def test_rejects_conflicting_altering_effects_on_same_target(tmp_path):
    """One record retracts, another supersedes — the same target has
    conflicting effective outcomes."""
    records = _base_records()
    v08_first = records[0]
    v08_1_retracts = records[1]

    v08_2_supersedes = copy.deepcopy(v08_1_retracts)
    v08_2_supersedes["record_id"] = "v08.2.scenario7.regression"
    v08_2_supersedes["test_kind"] = "regression"
    v08_2_supersedes["recorded_at"] = "2026-07-18T12:00:00+08:00"
    v08_2_supersedes["revises"] = {
        "record_id": "v08.scenario7.probe",
        "effect": "supersedes",
        "reason": "regression run, different disposition",
    }
    v08_2_supersedes["control_design"] = None
    v08_2_supersedes["evidence_commit"] = "4b4279761ee8a9953bb52e4d794ff75b3a34f1f9"

    r = _run_validator(tmp_path, [v08_first, v08_1_retracts, v08_2_supersedes])
    assert r.returncode != 0
    assert "conflicting altering revisions" in r.stdout or "R6 invariant 12" in r.stdout


def test_rejects_backward_recorded_at_along_revision_edge(tmp_path):
    records = _base_records()
    records[1]["recorded_at"] = "2026-07-17T00:00:00+08:00"
    r = _run_validator(tmp_path, records)
    assert r.returncode != 0
    assert "recorded_at is BEFORE" in r.stdout or "R6 invariant 11" in r.stdout
