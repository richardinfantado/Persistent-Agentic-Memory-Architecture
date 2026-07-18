"""Tests for the R6.1b evidence model.

Positive coverage:
  - Schema is a valid JSON Schema (Draft 2020-12).
  - The V08 reference retraction chain validates cleanly.
  - Both reference records carry origin='retrospective_reconstruction'
    and harness_commit=null.
  - Effective-status derivation reports V08 as 'retracted' even though
    its intrinsic claim_status remains 'confirmed'.
  - Validator accepts the reference chain end-to-end.

Negative coverage (every entry MUST cause validate_evidence.py to exit
nonzero):
  R6.1a-era rejections retained:
  - retracted / superseded as an intrinsic claim_status
  - missing revises target
  - revises across differing requirement_ids
  - self-revision
  - forward reference (target appears after reviser)
  - revision cycle
  - empty retraction reason
  - controlled_experiment with empty confounder + negative-control lists
  - abbreviated evidence_commit
  - empty subject name
  - classification=not_testable with claim_status=confirmed
  - missing pamspec_context.spec_commit
  - conflicting altering effects on same target
  - backward observation-time along a revision edge

  R6.1b additions (semantic-combination + provenance + format checks):
  - superseded as an intrinsic claim_status (parallel to retracted)
  - claim_status=not_testable with classification=native
    (bidirectional not_testable)
  - classification=emulated with adapter=null
  - evidence_source=['adapter', ...] with adapter=null
  - revises.effect=retracts with claim_status=inconclusive
  - revises.effect=supersedes with claim_status=not_testable
  - profile set but profile_version null
  - profile null but profile_version set
  - malformed recorded_at (FormatChecker)
  - recorded_at without timezone (FormatChecker)
  - controlled_experiment without environment_manifest
  - controlled_experiment without results_artifact
  - environment_manifest non-null but sha256=null
  - retrospective record missing evidence_observed_at
    (subsumed by required-field check; test covers this)
  - invalid origin value
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


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


def _make_schema_validator() -> Draft202012Validator:
    """Use the same custom-checker path as validate_evidence.make_validator()
    so tests reject the same date-time strings the CLI rejects."""
    return validate_evidence.make_validator()


# ------- positive tests -------

def test_schema_is_valid_json_schema():
    Draft202012Validator.check_schema(_load_schema())


def test_reference_chain_validates_against_schema():
    v = _make_schema_validator()
    records = _load_chain(REFERENCE_CHAIN)
    assert len(records) == 2
    for rec in records:
        errors = list(v.iter_errors(rec))
        assert not errors, f"{rec['record_id']} failed schema: {[e.message for e in errors]}"


def test_reference_chain_is_append_only_retraction():
    records = _load_chain(REFERENCE_CHAIN)
    v08 = next(r for r in records if r["record_id"] == "v08.scenario7.probe")
    v081 = next(r for r in records if r["record_id"] == "v08.1.scenario7.controlled_experiment")

    assert v08["claim_status"] == "confirmed"
    assert v08["revises"] is None
    assert v08["classification"] == "gap"
    assert v08["evidence_commit"] == "8871689b831480d8fd8980f4ed40c57c0a550c55"

    assert v081["claim_status"] == "confirmed"
    assert v081["revises"] is not None
    assert v081["revises"]["record_id"] == "v08.scenario7.probe"
    assert v081["revises"]["effect"] == "retracts"
    assert v081["revises"]["reason"]
    assert v081["classification"] == "native"
    assert v081["evidence_commit"] == "6ae806bbeb591c82c91236a191514b1775f24dbf"


def test_reference_records_are_retrospective_with_null_harness_commit():
    records = _load_chain(REFERENCE_CHAIN)
    for rec in records:
        assert rec["origin"] == "retrospective_reconstruction", \
            f"{rec['record_id']} must be retrospective_reconstruction"
        assert rec["pamspec_context"]["harness_commit"] is None, \
            f"{rec['record_id']} harness_commit must be null (not produced by R7 harness)"
        assert "evidence_observed_at" in rec
        assert rec["recorded_at"] != rec["evidence_observed_at"], \
            f"{rec['record_id']}: retrospective_reconstruction expects the two timestamps to differ"


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


def _assert_rejects(r: subprocess.CompletedProcess, needle: str | None = None):
    assert r.returncode != 0, f"expected rejection but got success. stdout={r.stdout}"
    if needle is not None:
        assert needle in r.stdout, f"expected '{needle}' in stdout, got: {r.stdout}"


# ------- negative tests (R6.1a-era, retained) -------

def test_rejects_retracted_as_intrinsic_status(tmp_path):
    records = _base_records()
    records[0]["claim_status"] = "retracted"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_superseded_as_intrinsic_status(tmp_path):
    records = _base_records()
    records[0]["claim_status"] = "superseded"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_missing_revises_target(tmp_path):
    records = _base_records()
    records[1]["revises"]["record_id"] = "nonexistent-id"
    _assert_rejects(_run_validator(tmp_path, records), "no such record_id")


def test_rejects_revises_across_requirement_ids(tmp_path):
    records = _base_records()
    records[1]["requirement_id"] = "PAMSPEC.some.other.requirement"
    _assert_rejects(_run_validator(tmp_path, records), "requirement_id differs")


def test_rejects_self_revision(tmp_path):
    records = _base_records()
    records[1]["revises"]["record_id"] = records[1]["record_id"]
    _assert_rejects(_run_validator(tmp_path, records), "self-revision")


def test_rejects_forward_reference_when_target_appears_later(tmp_path):
    records = _base_records()
    reversed_records = [records[1], records[0]]
    _assert_rejects(_run_validator(tmp_path, reversed_records), "append-only ordering")


def test_rejects_revision_cycle(tmp_path):
    base = _base_records()[0]
    def _mk(rid, revises_target):
        rec = copy.deepcopy(base)
        rec["record_id"] = rid
        rec["revises"] = {"record_id": revises_target, "effect": "reproduces", "reason": "cycle probe"}
        return rec
    a = _mk("A", "C")
    b = _mk("B", "A")
    c = _mk("C", "B")
    _assert_rejects(_run_validator(tmp_path, [a, b, c]))


def test_rejects_empty_retraction_reason(tmp_path):
    records = _base_records()
    records[1]["revises"]["reason"] = ""
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_controlled_experiment_with_empty_controls(tmp_path):
    records = _base_records()
    cd = records[1]["control_design"]
    cd["confounders_ruled_out"] = []
    cd["negative_controls"] = []
    _assert_rejects(
        _run_validator(tmp_path, records),
        "at least one confounders_ruled_out or negative_controls",
    )


def test_rejects_abbreviated_evidence_commit(tmp_path):
    records = _base_records()
    records[0]["evidence_commit"] = "8871689"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_empty_subject_name(tmp_path):
    records = _base_records()
    records[0]["subject"]["name"] = ""
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_not_testable_classification_with_confirmed_status(tmp_path):
    records = _base_records()
    records[0]["classification"] = "not_testable"
    records[0]["claim_status"] = "confirmed"
    records[0]["limitations"] = ["something"]
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_missing_spec_commit(tmp_path):
    records = _base_records()
    records[0]["pamspec_context"]["spec_commit"] = "abc"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_conflicting_altering_effects_on_same_target(tmp_path):
    records = _base_records()
    v08_first = records[0]
    v08_1_retracts = records[1]

    v08_2_supersedes = copy.deepcopy(v08_1_retracts)
    v08_2_supersedes["record_id"] = "v08.2.scenario7.regression"
    v08_2_supersedes["test_kind"] = "regression"
    v08_2_supersedes["recorded_at"] = "2026-07-18T18:00:00+08:00"
    v08_2_supersedes["evidence_observed_at"] = "2026-07-18T12:01:39+08:00"
    v08_2_supersedes["revises"] = {
        "record_id": "v08.scenario7.probe",
        "effect": "supersedes",
        "reason": "regression run, different disposition",
    }
    # regression is not controlled_experiment, so control_design and
    # environment_manifest / results_artifact may be null; keep them as-is.
    v08_2_supersedes["control_design"] = None
    v08_2_supersedes["environment_manifest"] = None
    v08_2_supersedes["results_artifact"] = None
    v08_2_supersedes["evidence_commit"] = "4b4279761ee8a9953bb52e4d794ff75b3a34f1f9"

    _assert_rejects(
        _run_validator(tmp_path, [v08_first, v08_1_retracts, v08_2_supersedes]),
        "conflicting altering revisions",
    )


def test_rejects_backward_observed_at_along_revision_edge(tmp_path):
    records = _base_records()
    records[1]["evidence_observed_at"] = "2026-07-17T00:00:00+08:00"
    _assert_rejects(
        _run_validator(tmp_path, records),
        "evidence_observed_at is BEFORE",
    )


# ------- negative tests (R6.1b additions) -------

def test_rejects_not_testable_status_with_native_classification(tmp_path):
    """Bidirectional not_testable rule."""
    records = _base_records()
    records[0]["classification"] = "native"
    records[0]["claim_status"] = "not_testable"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_emulated_with_null_adapter(tmp_path):
    records = _base_records()
    records[0]["classification"] = "emulated"
    records[0]["adapter"] = None
    records[0]["evidence_source"] = ["public_api"]
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_adapter_evidence_source_with_null_adapter(tmp_path):
    records = _base_records()
    records[0]["evidence_source"] = ["adapter"]
    records[0]["adapter"] = None
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_retracts_with_inconclusive_claim_status(tmp_path):
    records = _base_records()
    records[1]["claim_status"] = "inconclusive"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_supersedes_with_not_testable_claim_status(tmp_path):
    records = _base_records()
    records[1]["revises"]["effect"] = "supersedes"
    records[1]["claim_status"] = "not_testable"
    # classification=not_testable requires claim_status=not_testable (this side)
    records[1]["classification"] = "not_testable"
    records[1]["limitations"] = records[1]["limitations"] + ["not_testable path"]
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_profile_set_profile_version_null(tmp_path):
    records = _base_records()
    records[0]["pamspec_context"]["profile"] = "PAMSPEC-Lite"
    records[0]["pamspec_context"]["profile_version"] = None
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_profile_null_profile_version_set(tmp_path):
    records = _base_records()
    records[0]["pamspec_context"]["profile"] = None
    records[0]["pamspec_context"]["profile_version"] = "0.1-draft"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_malformed_recorded_at(tmp_path):
    records = _base_records()
    records[0]["recorded_at"] = "yesterday afternoon"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_recorded_at_without_timezone(tmp_path):
    records = _base_records()
    records[0]["recorded_at"] = "2026-07-18T15:00:00"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_controlled_experiment_without_environment_manifest(tmp_path):
    records = _base_records()
    records[1]["environment_manifest"] = None
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_controlled_experiment_without_results_artifact(tmp_path):
    records = _base_records()
    records[1]["results_artifact"] = None
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_environment_manifest_with_null_hash(tmp_path):
    records = _base_records()
    records[1]["environment_manifest"]["sha256"] = None
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_missing_evidence_observed_at(tmp_path):
    records = _base_records()
    del records[0]["evidence_observed_at"]
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_invalid_origin_value(tmp_path):
    records = _base_records()
    records[0]["origin"] = "native"  # missing suffix
    _assert_rejects(_run_validator(tmp_path, records))


# ------- R6.1c: retrospective provenance invariants -------

def test_rejects_retrospective_with_non_null_harness_commit(tmp_path):
    """Schema conditional 11: origin=retrospective_reconstruction must
    have pamspec_context.harness_commit=null. A retrospective record
    cannot falsely attribute its evidence to an R7 harness run."""
    records = _base_records()
    records[0]["pamspec_context"]["harness_commit"] = \
        "0123456789012345678901234567890123456789"
    _assert_rejects(_run_validator(tmp_path, records))


def test_rejects_retrospective_observed_after_materialized(tmp_path):
    """Invariant 13: for origin=retrospective_reconstruction records,
    evidence_observed_at must be <= recorded_at. The underlying
    experiment cannot occur after the retrospective record was
    materialized."""
    records = _base_records()
    # V08.1's evidence_observed_at pushed after V08.1's recorded_at.
    records[1]["evidence_observed_at"] = "2026-07-19T00:00:00+08:00"
    _assert_rejects(
        _run_validator(tmp_path, records),
        "R6 invariant 13",
    )


def test_rejects_date_time_with_space_separator(tmp_path):
    """Strict RFC 3339: space between date and time is rejected."""
    records = _base_records()
    records[0]["recorded_at"] = "2026-07-18 15:00:00+08:00"
    _assert_rejects(_run_validator(tmp_path, records))
