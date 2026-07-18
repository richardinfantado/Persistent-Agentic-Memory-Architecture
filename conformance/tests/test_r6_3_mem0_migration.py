"""R6.3 tests: V08 Mem0 evidence migration into retrospective EvidenceRecords.

Verifies:
  - all 9 records (8 scenarios + V08 scenario-7 retracted probe) validate
  - all 8 scenarios are represented
  - retrospective records have harness_commit=null and origin=retrospective_reconstruction
  - historical evidence commits and artifact hashes resolve in git
  - Scenario 7 original claim is effectively retracted
  - Scenario 7 corrected result remains confirmed/native
  - Scenario 5 contains the not_testable sub-requirement
  - no record claims origin=native_emission
  - no historical V08/V08.1 evidence file was modified
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_CHAIN = ROOT / "validation" / "evidence" / "mem0-v08-validation.jsonl"
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
VALIDATOR_CLI = ROOT / "scripts" / "validate_evidence.py"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence  # noqa: E402


def _load_chain():
    return [json.loads(l) for l in MIGRATION_CHAIN.read_text(encoding="utf-8").splitlines() if l.strip()]


def _git_show_hash(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        capture_output=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, f"git show failed: {commit}:{path}"
    return hashlib.sha256(result.stdout).hexdigest()


# ---------- P ositive: chain validation ----------

def test_migration_chain_passes_validator_cli():
    r = subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), str(MIGRATION_CHAIN)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


def test_migration_chain_passes_schema_validation():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = validate_evidence.make_validator()
    records = _load_chain()
    for rec in records:
        errors = list(Draft202012Validator(schema).iter_errors(rec))
        assert not errors, f"{rec['record_id']} schema errors: {[e.message for e in errors]}"


def test_nine_records_total():
    records = _load_chain()
    assert len(records) == 9, f"expected 9 records, got {len(records)}"


# ---------- All 8 scenarios represented ----------

EXPECTED_REQUIREMENTS = {
    "PAMSPEC.scope.immutable_across_update",
    "PAMSPEC.identity.stable_object_and_history_ledger",
    "PAMSPEC.mutation.expected_version_conflict_rejection",
    "PAMSPEC.mutation.idempotent_create",
    "PAMSPEC.deletion.tombstone_and_identity_reservation",
    "PAMSPEC.provenance.source_actor_and_activity",
    "PAMSPEC.authoritative_derived.vector_refresh_on_update",
    "PAMSPEC.extensibility.unknown_fields_survive_roundtrip",
}


def test_all_eight_scenarios_represented():
    records = _load_chain()
    present = {r["requirement_id"] for r in records}
    assert EXPECTED_REQUIREMENTS == present, \
        f"missing: {EXPECTED_REQUIREMENTS - present}\nunexpected: {present - EXPECTED_REQUIREMENTS}"


# ---------- Retrospective provenance ----------

def test_all_records_are_retrospective():
    for r in _load_chain():
        assert r["origin"] == "retrospective_reconstruction", \
            f"{r['record_id']}: origin must be retrospective_reconstruction"


def test_no_record_claims_native_emission():
    for r in _load_chain():
        assert r["origin"] != "native_emission", \
            f"{r['record_id']}: must not claim native_emission"


def test_all_records_have_null_harness_commit():
    for r in _load_chain():
        assert r["pamspec_context"]["harness_commit"] is None, \
            f"{r['record_id']}: harness_commit must be null"


# ---------- Artifact hash resolution ----------

def test_v08_1_results_artifact_hash_resolves():
    """SHA-256 of V08.1 results JSONL at commit 6ae806b must match
    the declared hash in the R6.3 records that reference it."""
    actual = _git_show_hash(
        "6ae806bbeb591c82c91236a191514b1775f24dbf",
        "validation/reports/mem0_scenario_results.jsonl",
    )
    records = _load_chain()
    for r in records:
        ra = r.get("results_artifact") or {}
        if ra.get("sha256") and ra.get("reference", "").endswith("mem0_scenario_results.jsonl"):
            expected = ra["sha256"]
            if r["evidence_commit"].startswith("6ae806b"):
                assert actual == expected, \
                    f"{r['record_id']}: results_artifact.sha256 mismatch (got {actual[:16]}...)"


def test_v08_1_env_manifest_hash_resolves():
    actual = _git_show_hash(
        "6ae806bbeb591c82c91236a191514b1775f24dbf",
        "validation/environment-manifest.json",
    )
    records = _load_chain()
    for r in records:
        em = r.get("environment_manifest") or {}
        if em.get("sha256") and em.get("reference", "").endswith("environment-manifest.json"):
            assert em["sha256"] == actual, \
                f"{r['record_id']}: environment_manifest.sha256 mismatch"


def test_v08_original_results_artifact_hash_resolves():
    actual = _git_show_hash(
        "8871689b831480d8fd8980f4ed40c57c0a550c55",
        "validation/reports/mem0_scenario_results.jsonl",
    )
    records = _load_chain()
    for r in records:
        if r["evidence_commit"].startswith("8871689"):
            ra = r.get("results_artifact") or {}
            if ra.get("sha256"):
                assert ra["sha256"] == actual, \
                    f"{r['record_id']}: V08 results_artifact.sha256 mismatch"


# ---------- Scenario 7 retraction chain ----------

def test_scenario7_original_claim_is_retracted():
    records = _load_chain()
    effective = validate_evidence.compute_effective_status(records)
    assert effective["v08.s7.derived-state.original-probe"] == "retracted", \
        "V08 scenario-7 original claim must be retracted by V08.1 corrected record"


def test_scenario7_corrected_result_is_confirmed():
    records = _load_chain()
    corrected = next(
        r for r in records
        if r["record_id"] == "v08.s7.derived-state.controlled-experiment"
    )
    assert corrected["claim_status"] == "confirmed"
    assert corrected["classification"] == "native"
    assert corrected["revises"]["effect"] == "retracts"
    assert corrected["revises"]["record_id"] == "v08.s7.derived-state.original-probe"


def test_scenario7_original_preserved_with_gap_classification():
    """R6 append-only: the original V08 probe record MUST remain with
    its original classification and claim_status, not be rewritten."""
    records = _load_chain()
    original = next(
        r for r in records
        if r["record_id"] == "v08.s7.derived-state.original-probe"
    )
    assert original["classification"] == "gap"
    assert original["claim_status"] == "confirmed"
    assert original["revises"] is None


# ---------- Scenario 5 sub-requirements ----------

def test_scenario5_contains_not_testable_sub_requirement():
    records = _load_chain()
    s5 = next(r for r in records if "deletion" in r["requirement_id"])
    sub_classes = {sr["sub_requirement_id"]: sr["classification"] for sr in s5["sub_requirements"]}
    assert "same_id_recreation_prohibited" in sub_classes, \
        "Scenario 5 must have same_id_recreation_prohibited sub-requirement"
    assert sub_classes["same_id_recreation_prohibited"] == "not_testable"


def test_scenario5_has_native_delete_sub_requirements():
    records = _load_chain()
    s5 = next(r for r in records if "deletion" in r["requirement_id"])
    sub_classes = {sr["sub_requirement_id"]: sr["classification"] for sr in s5["sub_requirements"]}
    assert sub_classes.get("delete_event_recorded_in_history") == "native"
    assert sub_classes.get("get_after_delete_returns_no_active_object") == "native"


# ---------- Historical evidence files not modified by R6.3 ----------

# R6.3 branch base commit — the merged main HEAD before R6.3 began.
R63_BRANCH_BASE = "a20489a20111cd4ea0fdeed328ec64fddcd3f35e"


def _git_tracked_hash_at_head(path: str) -> str:
    """SHA-256 of the git-tracked version of a file at the current HEAD.
    Uses git show HEAD:path rather than the on-disk file, which may have
    uncommitted local regenerations from test runs."""
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        capture_output=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, f"git show HEAD:{path} failed"
    return hashlib.sha256(result.stdout).hexdigest()


def test_v08_1_results_jsonl_not_modified_by_r63():
    """R6.3 must not modify the git-tracked V08.1 results JSONL.
    Comparison is between the git-tracked file at HEAD and at the
    R6.3 branch base (a20489a), not against on-disk state which may
    differ due to local validation test regeneration."""
    path = "validation/reports/mem0_scenario_results.jsonl"
    base_hash = _git_show_hash(R63_BRANCH_BASE, path)
    head_hash = _git_tracked_hash_at_head(path)
    assert head_hash == base_hash, \
        "R6.3 modified the git-tracked V08.1 results JSONL; must not touch historical evidence"


def test_v08_1_env_manifest_not_modified_by_r63():
    path = "validation/environment-manifest.json"
    base_hash = _git_show_hash(R63_BRANCH_BASE, path)
    head_hash = _git_tracked_hash_at_head(path)
    assert head_hash == base_hash, \
        "R6.3 modified the git-tracked V08.1 environment-manifest.json"


# ---------- R6.3a: corrective-pass checks ----------

V08_1_OBSERVED = "2026-07-18T04:18:54+08:00"


def test_scenario1_observation_time_is_v08_1_not_v08():
    """Scenario 1 uses the Alice/Bob visibility evidence added in V08.1,
    so its evidence_observed_at MUST be the V08.1 time, not the
    earlier V08 sprint time."""
    records = _load_chain()
    s1 = next(r for r in records if r["record_id"] == "v08.s1.scope-immutability.probe")
    assert s1["evidence_observed_at"] == V08_1_OBSERVED, (
        f"Scenario 1 evidence_observed_at is {s1['evidence_observed_at']!r}; "
        f"must be {V08_1_OBSERVED!r} (V08.1 time) because the Alice/Bob "
        f"visibility probe was added in V08.1, not V08"
    )


def test_no_emulated_without_adapter_anywhere_in_chain():
    """No record or sub-requirement may use 'emulated' unless the record
    has adapter non-null and evidence_source contains 'adapter'.
    The schema enforces this at the top-level classification; this test
    also enforces it at the sub-requirement level (schema permissiveness
    does not override the evidence taxonomy)."""
    records = _load_chain()
    for rec in records:
        adapter_present = isinstance(rec.get("adapter"), dict)
        adapter_in_sources = "adapter" in (rec.get("evidence_source") or [])

        # Top-level
        if rec["classification"] == "emulated":
            assert adapter_present and adapter_in_sources, (
                f"{rec['record_id']}: top-level classification=emulated but "
                f"adapter={rec.get('adapter')!r}, evidence_source={rec.get('evidence_source')!r}"
            )
        # Sub-requirements
        for sr in rec.get("sub_requirements") or []:
            if sr.get("classification") == "emulated":
                assert adapter_present and adapter_in_sources, (
                    f"{rec['record_id']} sub-req {sr.get('sub_requirement_id')!r}: "
                    f"classification=emulated but no adapter in this probe record"
                )
