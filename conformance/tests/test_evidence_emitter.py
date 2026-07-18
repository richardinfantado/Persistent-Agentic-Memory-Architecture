"""R6.2b tests: EvidenceRecord emission bound to structured execution
provenance.

Covers every reviewer-required guarantee for R6.2b, plus regression
of R6.2/R6.2a acceptance criteria.

Reviewer's additional required tests (R6.2b):
  1.  execution exception -> questionable/inconclusive, not gap/confirmed
  2.  missing feature classified via structured outcome metadata
  3.  forged evidence_commit rejected
  4.  forged harness_commit rejected
  5.  adapter-class mismatch rejected
  6.  subprocess subject/version mismatch rejected
  7.  missing report profile rejected
  8.  direct old-report helper cannot claim native emission
  9.  schema-invalid existing record rejected without write
  10. bad environment-manifest hash rejected without write
  11. concurrent writers do not lose either batch silently
  12. delayed emission retains report finish time as observation time
  13. dynamic traceback differences do not change semantic hash
      when structured outcomes are equivalent
"""

from __future__ import annotations

import copy
import hashlib
import json
import multiprocessing
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from conformance.harness import runner
from conformance.harness.evidence_emitter import (
    DEFAULT_ADAPTER_LIMITATION,
    CaseAssessment,
    EmissionContext,
    EvidenceEmissionError,
    ExecutionSession,
    _emit_native_evidence,
    _sha256_bytes,
    build_retrospective_record,
    normalize_for_determinism,
    run_and_emit,
)
from conformance.harness.case_registries.reference_python_lite import (
    REFERENCE_PYTHON_ADAPTER,
    REFERENCE_PYTHON_LITE_REGISTRY,
    REFERENCE_PYTHON_SUBJECT,
)
from conformance.adapters.reference_python import ReferencePythonAdapter


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
VALIDATOR_CLI = ROOT / "scripts" / "validate_evidence.py"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence  # noqa: E402


def _real_suite_commit() -> str:
    """Return the actual git HEAD SHA. Emission binding requires
    context.harness_commit == report.suite_commit, and the runner
    populates suite_commit from git rev-parse HEAD."""
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


SUITE_COMMIT = _real_suite_commit()

# R6.2c: tests inject a clean source_state so they do not depend on the
# repository being clean at test time. Tests that specifically verify
# dirty-source rejection pass an explicit dirty state.
CLEAN_SOURCE_STATE = {"head": SUITE_COMMIT, "clean": True, "modified_files": []}

# R6.2c: default evidence_identity for the reference-python subject.
# Bypass sessions inject this into adapter_info to satisfy the
# in-process identity-binding rule.
REF_PY_ADAPTER_INFO = {
    "class_name": "ReferencePythonAdapter",
    "evidence_identity": {
        "adapter_name": "ReferencePythonAdapter",
        "adapter_version": "translation-only",
        "implementation_name": "reference-python",
        "implementation_version": "0.1-draft",
    },
}


def _make_context(tmp_path: Path, **overrides) -> EmissionContext:
    kwargs = dict(
        spec_commit=SUITE_COMMIT,
        harness_commit=SUITE_COMMIT,
        evidence_commit=SUITE_COMMIT,
        profile="PAMSPEC-Lite",
        profile_version="0.1-draft",
        artifact_root=tmp_path,
        subject=dict(REFERENCE_PYTHON_SUBJECT),
        adapter=dict(REFERENCE_PYTHON_ADAPTER),
        run_id="testrun0001",
    )
    kwargs.update(overrides)
    return EmissionContext(**kwargs)


@pytest.fixture
def clean_source(monkeypatch):
    """R6.2d: substitute capture_source_state so tests do not depend
    on a genuinely clean worktree. The public API has no source_state
    parameter; only monkeypatch of the module-level function works."""
    def _clean(root=None):
        return {"head": SUITE_COMMIT, "clean": True, "modified_files": []}
    monkeypatch.setattr(
        "conformance.harness.evidence_emitter.capture_source_state", _clean,
    )
    return _clean


# ===========================================================================
# Integrated orchestration
# ===========================================================================

def test_run_and_emit_legacy_only_path(tmp_path):
    report_path = tmp_path / "r.json"
    report, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter, report_output_path=report_path,
    )
    assert report_path.exists()
    assert records is None
    assert not list(tmp_path.glob("*.jsonl"))


def test_run_and_emit_integrated_produces_valid_chain(tmp_path, clean_source):
    report_path = tmp_path / "r.json"
    evidence_path = tmp_path / "e.jsonl"
    report, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=report_path,
        evidence_output_path=evidence_path,
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    assert records is not None
    assert len(records) == len(report.cases) == 17
    # Chain-level invariants and schema pass
    r = subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), str(evidence_path)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"


# ===========================================================================
# Legacy report shape preserved (to_dict has no outcome_kind)
# ===========================================================================

def test_legacy_to_dict_has_no_outcome_kind_field(tmp_path):
    report, _ = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
    )
    d = report.to_dict()
    expected_case_keys = {"name", "passed", "duration_ms"}  # error only when present
    for case in d["cases"]:
        keys = set(case.keys()) - {"error"}
        assert keys == expected_case_keys, \
            f"legacy case shape drifted: {keys - expected_case_keys}"
        assert "outcome_kind" not in case, \
            "outcome_kind must not leak into legacy JSON (backward compat)"


# ===========================================================================
# Structured outcome classification (reviewer's tests 1 + 2 + 13)
# ===========================================================================

def _harness_bypass_session(tmp_path: Path, cases_with_outcomes: list[dict]) -> ExecutionSession:
    """Construct an ExecutionSession directly for structured-outcome
    testing. Simulates what run_and_emit would build if the runner
    encountered these specific outcomes."""
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    report_dict = {
        "report_format_version": 1,
        "profile": "PAMSPEC-Lite",
        "adapter_class": "ReferencePythonAdapter",
        "adapter_info": dict(REF_PY_ADAPTER_INFO),
        "suite_commit": SUITE_COMMIT,
        "started_at": "2026-07-18T15:00:00Z",
        "finished_at": "2026-07-18T15:00:10Z",
        "totals": {
            "total": len(cases_with_outcomes),
            "passed": sum(1 for c in cases_with_outcomes if c["passed"]),
            "failed": sum(1 for c in cases_with_outcomes if not c["passed"]),
            "all_passed": all(c["passed"] for c in cases_with_outcomes),
        },
        "cases": [{"name": c["name"], "passed": c["passed"], "duration_ms": 1.0,
                   **({"error": c["error"]} if c.get("error") else {})}
                  for c in cases_with_outcomes],
    }
    report_bytes = json.dumps(report_dict, indent=2, sort_keys=True).encode("utf-8")
    report_path = tmp_path / "r.json"
    report_path.write_bytes(report_bytes)
    return ExecutionSession(
        report_dict=report_dict,
        report_bytes=report_bytes,
        report_path=report_path,
        report_sha256=_sha256_bytes(report_bytes),
        outcome_kinds={c["name"]: c["outcome_kind"] for c in cases_with_outcomes},
        suite_commit=SUITE_COMMIT,
        adapter_class="ReferencePythonAdapter",
        adapter_info=dict(REF_PY_ADAPTER_INFO),
        profile="PAMSPEC-Lite",
        started_at="2026-07-18T15:00:00Z",
        finished_at="2026-07-18T15:00:10Z",
        source_state_before=dict(CLEAN_SOURCE_STATE),
        source_state_after=dict(CLEAN_SOURCE_STATE),
    )


def test_execution_exception_maps_to_questionable_inconclusive(tmp_path):
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "execution_error",
         "error": "Traceback ...\nRuntimeError: DB connection lost"},
    ])
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert recs[0]["classification"] == "questionable"
    assert recs[0]["claim_status"] == "inconclusive"


def test_assertion_failure_maps_to_gap_confirmed(tmp_path):
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "assertion_failure",
         "error": "assertion failed: expected 3 got 2"},
    ])
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert recs[0]["classification"] == "gap"
    assert recs[0]["claim_status"] == "confirmed"


def test_missing_feature_maps_to_not_testable(tmp_path):
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "missing_feature",
         "error": "adapter missing feature: something"},
    ])
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert recs[0]["classification"] == "not_testable"
    assert recs[0]["claim_status"] == "not_testable"


def test_semantic_hash_ignores_dynamic_error_text_when_outcomes_equivalent(tmp_path):
    """Two runs with the same outcome_kind but different traceback text
    MUST produce the same semantic hash."""
    session_a = _harness_bypass_session(tmp_path / "a", [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "execution_error",
         "error": "Traceback ...\nRuntimeError: /tmp/aXYZ/socket failed at line 42"},
    ])
    session_b = _harness_bypass_session(tmp_path / "b", [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "execution_error",
         "error": "Traceback ...\nRuntimeError: /tmp/bABC/socket failed at line 17"},
    ])
    from conformance.harness.evidence_emitter import _semantic_hash_from_session
    assert _semantic_hash_from_session(session_a) == _semantic_hash_from_session(session_b)


def test_semantic_hash_differs_when_structured_outcome_differs(tmp_path):
    session_pass = _harness_bypass_session(tmp_path / "a", [
        {"name": "case_read_returns_current_envelope", "passed": True,
         "outcome_kind": "passed"},
    ])
    session_fail = _harness_bypass_session(tmp_path / "b", [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "assertion_failure", "error": "assertion failed"},
    ])
    from conformance.harness.evidence_emitter import _semantic_hash_from_session
    assert _semantic_hash_from_session(session_pass) != _semantic_hash_from_session(session_fail)


# ===========================================================================
# Execution provenance binding (reviewer's tests 3 + 4 + 5 + 6 + 7)
# ===========================================================================

def test_forged_evidence_commit_rejected(tmp_path):
    fake = "d" * 40
    ctx = _make_context(tmp_path, evidence_commit=fake)
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="evidence_commit"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_forged_harness_commit_rejected(tmp_path):
    fake = "d" * 40
    ctx = _make_context(tmp_path, harness_commit=fake)
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="harness_commit"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_adapter_class_mismatch_rejected(tmp_path):
    ctx = _make_context(tmp_path, adapter={"name": "WrongAdapter", "version": "x"})
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="adapter"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_subprocess_implementation_mismatch_rejected(tmp_path):
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    # Inject subprocess metadata reporting a different implementation
    subproc_ai = {
        "class_name": "ReferencePythonAdapter",
        "subprocess": {
            "adapter_name": "ReferencePythonAdapter",
            "adapter_version": "translation-only",
            "implementation_name": "OTHER-IMPL",
            "implementation_version": "9.9",
        },
    }
    session2 = ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class=session.adapter_class, adapter_info=subproc_ai,
        profile=session.profile, started_at=session.started_at,
        finished_at=session.finished_at,
    )
    ctx = _make_context(tmp_path)  # subject.name = "reference-python"
    with pytest.raises(EvidenceEmissionError, match="implementation_name"):
        _emit_native_evidence(session2, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_missing_report_profile_rejected(tmp_path):
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    session2 = ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class=session.adapter_class, adapter_info=session.adapter_info,
        profile="", started_at=session.started_at, finished_at=session.finished_at,
    )
    ctx = _make_context(tmp_path)
    with pytest.raises(EvidenceEmissionError, match="profile"):
        _emit_native_evidence(session2, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


# ===========================================================================
# Native vs retrospective enforcement (reviewer's test 8)
# ===========================================================================

def test_retrospective_constructor_forces_null_harness_commit(tmp_path):
    """build_retrospective_record cannot produce a native record;
    harness_commit is FORCED to null."""
    rec = build_retrospective_record(
        record_id="test.record.abc",
        evidence_observed_at="2026-07-18T00:00:00Z",
        test_kind="probe",
        requirement_id="PAMSPEC.example",
        subject={"kind": "framework", "name": "x", "version": "1"},
        adapter=None,
        spec_commit=SUITE_COMMIT,
        profile=None, profile_version=None,
        classification="gap", claim_status="confirmed",
        evidence_commit=SUITE_COMMIT,
        evidence_source=["public_api"],
        limitations=["limitation"],
        observed_evidence={"noted": True},
    )
    assert rec["origin"] == "retrospective_reconstruction"
    assert rec["pamspec_context"]["harness_commit"] is None


def test_retrospective_constructor_cannot_produce_native_emission():
    """There is no code path from build_retrospective_record to
    origin='native_emission'."""
    rec = build_retrospective_record(
        record_id="test.record.def",
        evidence_observed_at="2026-07-18T00:00:00Z",
        test_kind="probe",
        requirement_id="PAMSPEC.example",
        subject={"kind": "framework", "name": "x", "version": "1"},
        adapter=None,
        spec_commit=SUITE_COMMIT,
        profile=None, profile_version=None,
        classification="native", claim_status="confirmed",
        evidence_commit=SUITE_COMMIT,
        evidence_source=["public_api"],
        limitations=[],
        observed_evidence={},
    )
    assert rec["origin"] != "native_emission"


# ===========================================================================
# Combined-chain schema validation (reviewer's test 9)
# ===========================================================================

def test_schema_invalid_existing_record_rejects_new_write_without_touching_file(tmp_path):
    """An existing chain record that is JSON-parseable but
    schema-invalid must cause the new emission to be rejected without
    modifying the existing chain file."""
    evidence = tmp_path / "e.jsonl"
    bogus = {"record_id": "bogus", "test_kind": "conformance"}  # missing required fields
    evidence.write_text(json.dumps(bogus) + "\n", encoding="utf-8")
    original_bytes = evidence.read_bytes()

    ctx = _make_context(tmp_path)
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="existing"):
        _emit_native_evidence(session, evidence, ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert evidence.read_bytes() == original_bytes


# ===========================================================================
# Environment-manifest verification (reviewer's test 10)
# ===========================================================================

def test_env_manifest_bytes_verified_at_emission_time(tmp_path):
    manifest_path = tmp_path / "env.json"
    manifest_path.write_bytes(b'{"env": "real"}')
    correct_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    ctx = _make_context(
        tmp_path,
        environment_manifest={"reference": "env.json", "sha256": correct_sha},
    )
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    # Should succeed
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert len(recs) == 1


def test_env_manifest_incorrect_hash_rejected_no_write(tmp_path):
    manifest_path = tmp_path / "env.json"
    manifest_path.write_bytes(b'{"env": "real"}')
    wrong = "0" * 64
    ctx = _make_context(
        tmp_path,
        environment_manifest={"reference": "env.json", "sha256": wrong},
    )
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    evidence = tmp_path / "e.jsonl"
    with pytest.raises(EvidenceEmissionError, match="mismatch"):
        _emit_native_evidence(session, evidence, ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert not evidence.exists()


def test_env_manifest_nonexistent_file_rejected(tmp_path):
    ctx = _make_context(
        tmp_path,
        environment_manifest={"reference": "does-not-exist.json", "sha256": "0" * 64},
    )
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="does not exist"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_env_manifest_absolute_reference_rejected(tmp_path):
    """An absolute path in environment_manifest.reference is rejected
    (portable references only)."""
    abs_ref = "/etc/passwd" if os.name != "nt" else "C:\\Windows\\System32\\drivers\\etc\\hosts"
    ctx = _make_context(
        tmp_path,
        environment_manifest={"reference": abs_ref, "sha256": "0" * 64},
    )
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="relative"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_env_manifest_traversal_reference_rejected(tmp_path):
    ctx = _make_context(
        tmp_path,
        environment_manifest={"reference": "../out.json", "sha256": "0" * 64},
    )
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="traversal"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


# ===========================================================================
# Concurrent-writer safety (reviewer's test 11)
# ===========================================================================

def test_concurrent_writers_fail_closed_no_silent_loss(tmp_path):
    """Two writers racing to append: at least one must fail with an
    explicit EvidenceEmissionError. Silent lost updates must be
    impossible.

    This test simulates the race by acquiring the lock first, then
    attempting a second emission while the lock is held.
    """
    from conformance.harness.evidence_emitter import _EmissionLock
    ctx = _make_context(tmp_path)
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    evidence = tmp_path / "e.jsonl"
    with _EmissionLock(evidence):
        with pytest.raises(EvidenceEmissionError, match="lock"):
            _emit_native_evidence(session, evidence, ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    # Now the lock is released; a subsequent emission MUST succeed.
    recs = _emit_native_evidence(session, evidence, ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert len(recs) == 1


# ===========================================================================
# Delayed emission time (reviewer's test 12)
# ===========================================================================

def test_delayed_emission_uses_report_finished_at_as_observed(tmp_path):
    """Delaying emission does NOT change the apparent observation time."""
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    # Simulate delay (the emitter uses now for recorded_at but not for observed).
    time.sleep(1.0)
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    # The critical assertion: emitter did NOT overwrite the observed
    # time with its own current wall clock. It preserved the report's
    # finished_at as the record's evidence_observed_at.
    assert recs[0]["evidence_observed_at"] == session.finished_at
    # recorded_at is set by the emitter's own wall clock — the two
    # fields are distinct and independent (this fake session uses a
    # fixed finished_at that may be past or future relative to now).
    assert recs[0]["recorded_at"] != recs[0]["evidence_observed_at"] \
        or session.finished_at == recs[0]["recorded_at"]


# ===========================================================================
# Preflight/atomic: various failures leave chain unchanged
# ===========================================================================

def test_duplicate_record_id_rejects_and_leaves_chain_unchanged(tmp_path):
    ctx = _make_context(tmp_path, run_id="samerun")
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    evidence = tmp_path / "e.jsonl"
    _emit_native_evidence(session, evidence, ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    first_bytes = evidence.read_bytes()
    with pytest.raises(EvidenceEmissionError):
        _emit_native_evidence(session, evidence, ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    assert evidence.read_bytes() == first_bytes


def test_missing_registry_entry_leaves_chain_unchanged(tmp_path):
    evidence = tmp_path / "e.jsonl"
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_UNKNOWN", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError):
        _emit_native_evidence(session, evidence, _make_context(tmp_path), REFERENCE_PYTHON_LITE_REGISTRY)
    assert not evidence.exists()


# ===========================================================================
# Semantic determinism (reviewer's test 13 counterpart + regression)
# ===========================================================================

def test_semantic_hash_stable_across_identical_runs_of_reference(tmp_path, clean_source):
    root1 = tmp_path / "root1"
    root1.mkdir()
    _, r1 = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=root1 / "r.json",
        evidence_output_path=root1 / "e.jsonl",
        context=_make_context(root1, run_id="r1"),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    time.sleep(1.0)
    root2 = tmp_path / "root2"
    root2.mkdir()
    _, r2 = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=root2 / "r.json",
        evidence_output_path=root2 / "e.jsonl",
        context=_make_context(root2, run_id="r2"),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    sem1 = {r["observed_evidence"]["semantic_results_sha256"] for r in r1}
    sem2 = {r["observed_evidence"]["semantic_results_sha256"] for r in r2}
    assert sem1 == sem2
    assert len(sem1) == 1


def test_normalize_does_not_mask_semantic_hash(tmp_path, clean_source):
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    n = normalize_for_determinism(records[0])
    assert n["observed_evidence"]["semantic_results_sha256"] \
        == records[0]["observed_evidence"]["semantic_results_sha256"]


# ===========================================================================
# CaseAssessment integrity
# ===========================================================================

def test_case_assessment_rejects_construction_without_all_four_outcomes():
    with pytest.raises(TypeError):
        CaseAssessment(  # type: ignore[call-arg]
            requirement_id="x",
            on_passed_classification="native",
            on_passed_claim_status="confirmed",
        )


def test_case_assessment_rejects_invalid_classification_enum():
    with pytest.raises(ValueError, match="classification"):
        CaseAssessment(
            requirement_id="x",
            on_passed_classification="inconclusive",  # not a classification
            on_passed_claim_status="confirmed",
            on_assertion_failure_classification="gap",
            on_assertion_failure_claim_status="confirmed",
            on_missing_feature_classification="not_testable",
            on_missing_feature_claim_status="not_testable",
            on_execution_error_classification="questionable",
            on_execution_error_claim_status="inconclusive",
        )


# ===========================================================================
# Context validation
# ===========================================================================

def test_context_rejects_short_sha(tmp_path):
    with pytest.raises(ValueError, match="spec_commit"):
        EmissionContext(
            spec_commit="abc", harness_commit=SUITE_COMMIT, evidence_commit=SUITE_COMMIT,
            profile="PAMSPEC-Lite", profile_version="0.1-draft",
            artifact_root=tmp_path, subject=dict(REFERENCE_PYTHON_SUBJECT),
        )


def test_context_rejects_bad_env_manifest_syntax(tmp_path):
    with pytest.raises(ValueError, match="environment_manifest"):
        EmissionContext(
            spec_commit=SUITE_COMMIT, harness_commit=SUITE_COMMIT, evidence_commit=SUITE_COMMIT,
            profile="PAMSPEC-Lite", profile_version="0.1-draft",
            artifact_root=tmp_path, subject=dict(REFERENCE_PYTHON_SUBJECT),
            environment_manifest={"reference": "x"},  # missing sha256
        )


# ===========================================================================
# Default limitation always present
# ===========================================================================

def test_default_adapter_limitation_always_present(tmp_path, clean_source):
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    for r in records:
        assert DEFAULT_ADAPTER_LIMITATION in r["limitations"]


# ===========================================================================
# R6.2c: repository commit provenance
# ===========================================================================

def test_runner_git_head_uses_repo_root_not_process_cwd(tmp_path, monkeypatch):
    """The runner MUST resolve `git rev-parse HEAD` against REPO_ROOT,
    not the process cwd. Otherwise a caller inside a different git
    repo would attribute PAMSPEC evidence to the wrong commit."""
    monkeypatch.chdir(tmp_path)
    # tmp_path is not a git repo, so a cwd-based git rev-parse would fail;
    # the runner MUST still return the PAMSPEC repo's HEAD.
    from conformance.harness.runner import _git_head_commit
    head = _git_head_commit()
    assert re.match(r"^[0-9a-f]{40}$", head), \
        f"runner should return PAMSPEC repo HEAD from any cwd, got {head!r}"


# ===========================================================================
# R6.2c: clean-source provenance
# ===========================================================================

def test_dirty_source_rejects_native_emission(tmp_path, monkeypatch):
    """R6.2d: monkeypatch (not a public parameter) is the only way to
    substitute source state. Dirty state MUST reject."""
    dirty = {"head": SUITE_COMMIT, "clean": False,
             "modified_files": [" M conformance/harness/runner.py"]}
    monkeypatch.setattr(
        "conformance.harness.evidence_emitter.capture_source_state",
        lambda root=None: dirty,
    )
    evidence = tmp_path / "e.jsonl"
    with pytest.raises(EvidenceEmissionError, match="not clean"):
        run_and_emit(
            "PAMSPEC-Lite", ReferencePythonAdapter,
            report_output_path=tmp_path / "r.json",
            evidence_output_path=evidence,
            context=_make_context(tmp_path),
            case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
        )
    assert not evidence.exists()


# ---------- R6.2d: no public source_state bypass ----------

def test_run_and_emit_has_no_source_state_parameter():
    """R6.2d: the public API MUST NOT accept a caller-supplied
    source_state. Only monkeypatch of the module-level function
    substitutes the inspection."""
    import inspect
    sig = inspect.signature(run_and_emit)
    assert "source_state" not in sig.parameters, \
        "R6.2d requires removing the public source_state bypass; " \
        f"got signature: {sig}"


# ---------- R6.2d: pre/post source consistency ----------

def test_head_change_during_execution_rejects(tmp_path, monkeypatch):
    """If HEAD changes between pre-run and post-run capture, native
    evidence MUST be refused."""
    states = iter([
        {"head": SUITE_COMMIT, "clean": True, "modified_files": []},
        {"head": "0" * 40, "clean": True, "modified_files": []},
    ])
    monkeypatch.setattr(
        "conformance.harness.evidence_emitter.capture_source_state",
        lambda root=None: next(states),
    )
    with pytest.raises(EvidenceEmissionError, match="HEAD changed"):
        run_and_emit(
            "PAMSPEC-Lite", ReferencePythonAdapter,
            report_output_path=tmp_path / "r.json",
            evidence_output_path=tmp_path / "e.jsonl",
            context=_make_context(tmp_path),
            case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
        )


def test_post_run_dirty_rejects(tmp_path, monkeypatch):
    """If the source becomes dirty during execution, native evidence
    MUST be refused."""
    states = iter([
        {"head": SUITE_COMMIT, "clean": True, "modified_files": []},
        {"head": SUITE_COMMIT, "clean": False,
         "modified_files": [" M conformance/harness/runner.py"]},
    ])
    monkeypatch.setattr(
        "conformance.harness.evidence_emitter.capture_source_state",
        lambda root=None: next(states),
    )
    with pytest.raises(EvidenceEmissionError, match="source_state_after"):
        run_and_emit(
            "PAMSPEC-Lite", ReferencePythonAdapter,
            report_output_path=tmp_path / "r.json",
            evidence_output_path=tmp_path / "e.jsonl",
            context=_make_context(tmp_path),
            case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
        )


def test_source_head_mismatched_with_report_suite_commit_rejects(tmp_path, monkeypatch):
    """source_state.head MUST equal report.suite_commit."""
    forged = {"head": "1" * 40, "clean": True, "modified_files": []}
    monkeypatch.setattr(
        "conformance.harness.evidence_emitter.capture_source_state",
        lambda root=None: forged,
    )
    with pytest.raises(EvidenceEmissionError, match="does not match"):
        run_and_emit(
            "PAMSPEC-Lite", ReferencePythonAdapter,
            report_output_path=tmp_path / "r.json",
            evidence_output_path=tmp_path / "e.jsonl",
            context=_make_context(tmp_path),
            case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
        )


# ---------- R6.2d: whole-repo cleanliness ----------

def test_capture_source_state_uses_untracked_files_normal(monkeypatch):
    """capture_source_state MUST invoke `git status --porcelain
    --untracked-files=normal` — whole-repo scope, not path-scoped."""
    calls = []
    def _fake_run(cmd, **kw):
        calls.append(list(cmd))
        class _R:
            returncode = 0
            stdout = "abc\n" if "rev-parse" in cmd else ""
        return _R()
    import conformance.harness.evidence_emitter as ee
    monkeypatch.setattr(ee.subprocess, "run", _fake_run)
    ee.capture_source_state()
    status_calls = [c for c in calls if "status" in c]
    assert status_calls, "capture_source_state must call git status"
    assert "--untracked-files=normal" in status_calls[0], \
        "R6.2d requires whole-repo untracked-files=normal scope"


# ---------- R6.2d: complete identity fields required ----------

def _partial_identity_session(tmp_path: Path, identity_override: dict) -> ExecutionSession:
    """A bypass session where the in-process evidence_identity is a
    partial dict (missing or empty field). Used to prove that partial
    identity is rejected."""
    partial_ai = {"class_name": "ReferencePythonAdapter",
                  "evidence_identity": identity_override}
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    return ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class=session.adapter_class, adapter_info=partial_ai,
        profile=session.profile, started_at=session.started_at,
        finished_at=session.finished_at,
        source_state_before=dict(CLEAN_SOURCE_STATE),
        source_state_after=dict(CLEAN_SOURCE_STATE),
    )


def test_missing_adapter_version_rejected(tmp_path):
    session = _partial_identity_session(tmp_path, {
        "adapter_name": "ReferencePythonAdapter",
        "implementation_name": "reference-python",
        "implementation_version": "0.1-draft",
        # adapter_version missing
    })
    with pytest.raises(EvidenceEmissionError, match="complete runtime identity"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", _make_context(tmp_path),
                              REFERENCE_PYTHON_LITE_REGISTRY)


def test_missing_implementation_version_rejected(tmp_path):
    session = _partial_identity_session(tmp_path, {
        "adapter_name": "ReferencePythonAdapter",
        "adapter_version": "translation-only",
        "implementation_name": "reference-python",
        # implementation_version missing
    })
    with pytest.raises(EvidenceEmissionError, match="complete runtime identity"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", _make_context(tmp_path),
                              REFERENCE_PYTHON_LITE_REGISTRY)


def test_empty_adapter_version_rejected(tmp_path):
    session = _partial_identity_session(tmp_path, {
        "adapter_name": "ReferencePythonAdapter",
        "adapter_version": "",
        "implementation_name": "reference-python",
        "implementation_version": "0.1-draft",
    })
    with pytest.raises(EvidenceEmissionError, match="complete runtime identity"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", _make_context(tmp_path),
                              REFERENCE_PYTHON_LITE_REGISTRY)


def test_empty_implementation_version_rejected(tmp_path):
    session = _partial_identity_session(tmp_path, {
        "adapter_name": "ReferencePythonAdapter",
        "adapter_version": "translation-only",
        "implementation_name": "reference-python",
        "implementation_version": "",
    })
    with pytest.raises(EvidenceEmissionError, match="complete runtime identity"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", _make_context(tmp_path),
                              REFERENCE_PYTHON_LITE_REGISTRY)


def test_mismatched_subject_kind_rejected(tmp_path):
    """R6.2d: subject.kind MUST be 'implementation' for native emission."""
    ctx = _make_context(tmp_path, subject={
        "kind": "framework", "name": "reference-python", "version": "0.1-draft",
    })
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="subject.kind"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


# ---------- R6.2d: semantic hash includes in-process identity ----------

def test_semantic_hash_changes_with_adapter_version(tmp_path):
    """Same case outcomes but different adapter_version -> different
    semantic hashes (R6.2d closes the in-process-identity omission)."""
    from conformance.harness.evidence_emitter import _semantic_hash_from_session
    ai_v1 = {"class_name": "X", "evidence_identity": {
        "adapter_name": "A", "adapter_version": "1",
        "implementation_name": "I", "implementation_version": "1",
    }}
    ai_v2 = {"class_name": "X", "evidence_identity": {
        "adapter_name": "A", "adapter_version": "2",
        "implementation_name": "I", "implementation_version": "1",
    }}
    s1 = _harness_bypass_session(tmp_path / "a", [
        {"name": "case_x", "passed": True, "outcome_kind": "passed"},
    ])
    s1 = ExecutionSession(
        report_dict={**s1.report_dict, "adapter_info": ai_v1},
        report_bytes=s1.report_bytes, report_path=s1.report_path,
        report_sha256=s1.report_sha256, outcome_kinds=s1.outcome_kinds,
        suite_commit=s1.suite_commit, adapter_class=s1.adapter_class,
        adapter_info=ai_v1, profile=s1.profile,
        started_at=s1.started_at, finished_at=s1.finished_at,
        source_state_before=s1.source_state_before,
        source_state_after=s1.source_state_after,
    )
    s2 = _harness_bypass_session(tmp_path / "b", [
        {"name": "case_x", "passed": True, "outcome_kind": "passed"},
    ])
    s2 = ExecutionSession(
        report_dict={**s2.report_dict, "adapter_info": ai_v2},
        report_bytes=s2.report_bytes, report_path=s2.report_path,
        report_sha256=s2.report_sha256, outcome_kinds=s2.outcome_kinds,
        suite_commit=s2.suite_commit, adapter_class=s2.adapter_class,
        adapter_info=ai_v2, profile=s2.profile,
        started_at=s2.started_at, finished_at=s2.finished_at,
        source_state_before=s2.source_state_before,
        source_state_after=s2.source_state_after,
    )
    assert _semantic_hash_from_session(s1) != _semantic_hash_from_session(s2)


def test_semantic_hash_changes_with_implementation_version(tmp_path):
    from conformance.harness.evidence_emitter import _semantic_hash_from_session
    ai_a = {"class_name": "X", "evidence_identity": {
        "adapter_name": "A", "adapter_version": "1",
        "implementation_name": "I", "implementation_version": "1",
    }}
    ai_b = {"class_name": "X", "evidence_identity": {
        "adapter_name": "A", "adapter_version": "1",
        "implementation_name": "I", "implementation_version": "2",
    }}
    def _sess(root, ai):
        s = _harness_bypass_session(root, [
            {"name": "case_x", "passed": True, "outcome_kind": "passed"},
        ])
        return ExecutionSession(
            report_dict={**s.report_dict, "adapter_info": ai},
            report_bytes=s.report_bytes, report_path=s.report_path,
            report_sha256=s.report_sha256, outcome_kinds=s.outcome_kinds,
            suite_commit=s.suite_commit, adapter_class=s.adapter_class,
            adapter_info=ai, profile=s.profile,
            started_at=s.started_at, finished_at=s.finished_at,
            source_state_before=s.source_state_before,
            source_state_after=s.source_state_after,
        )
    assert _semantic_hash_from_session(_sess(tmp_path / "a", ai_a)) \
        != _semantic_hash_from_session(_sess(tmp_path / "b", ai_b))


# ---------- R6.2d: per-case adapter identity consistency ----------

def test_per_case_identity_drift_rejected(tmp_path):
    """If a case adapter's evidence_identity differs from the probe's,
    native emission MUST refuse."""
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
        {"name": "case_scope_isolation", "passed": True, "outcome_kind": "passed"},
    ])
    # Inject a per-case identity that DIFFERS from the probe.
    drifted = ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class=session.adapter_class, adapter_info=session.adapter_info,
        profile=session.profile, started_at=session.started_at,
        finished_at=session.finished_at,
        source_state_before=session.source_state_before,
        source_state_after=session.source_state_after,
        case_adapter_identities={
            "case_scope_isolation": {
                "adapter_name": "ReferencePythonAdapter",
                "adapter_version": "translation-only",
                "implementation_name": "reference-python",
                "implementation_version": "999.999",  # drifted
            },
        },
    )
    with pytest.raises(EvidenceEmissionError, match="per-case adapter identity drift"):
        _emit_native_evidence(drifted, tmp_path / "e.jsonl",
                              _make_context(tmp_path), REFERENCE_PYTHON_LITE_REGISTRY)


def test_matching_per_case_identity_succeeds(tmp_path):
    """All cases report the same identity as the probe -> native
    emission succeeds."""
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    matching = ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class=session.adapter_class, adapter_info=session.adapter_info,
        profile=session.profile, started_at=session.started_at,
        finished_at=session.finished_at,
        source_state_before=session.source_state_before,
        source_state_after=session.source_state_after,
        case_adapter_identities={
            "case_read_returns_current_envelope": dict(
                REF_PY_ADAPTER_INFO["evidence_identity"]
            ),
        },
    )
    recs = _emit_native_evidence(matching, tmp_path / "e.jsonl",
                                 _make_context(tmp_path), REFERENCE_PYTHON_LITE_REGISTRY)
    assert len(recs) == 1


def test_capture_source_state_shape():
    """capture_source_state returns the expected fields for downstream
    consumption. Content depends on real repo state; we check shape only."""
    from conformance.harness.evidence_emitter import capture_source_state
    s = capture_source_state()
    assert set(s.keys()) == {"head", "clean", "modified_files"}
    assert isinstance(s["modified_files"], list)
    assert isinstance(s["clean"], bool)


# ===========================================================================
# R6.2c: specification commit binding
# ===========================================================================

def test_forged_spec_commit_rejected(tmp_path):
    """context.spec_commit MUST equal report.suite_commit."""
    fake = "e" * 40
    ctx = _make_context(tmp_path, spec_commit=fake)
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="spec_commit"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_subprocess_spec_commit_mismatch_rejected(tmp_path):
    """A subprocess adapter that self-reports a spec_commit different
    from context.spec_commit MUST cause rejection."""
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    forged_sub = {
        "class_name": "SubprocessAdapter",
        "subprocess": {
            "adapter_name": "ReferencePythonAdapter",
            "adapter_version": "translation-only",
            "implementation_name": "reference-python",
            "implementation_version": "0.1-draft",
            "spec_commit": "f" * 40,
        },
    }
    session2 = ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class=session.adapter_class, adapter_info=forged_sub,
        profile=session.profile, started_at=session.started_at,
        finished_at=session.finished_at,
        source_state_before=dict(CLEAN_SOURCE_STATE),
        source_state_after=dict(CLEAN_SOURCE_STATE),
    )
    with pytest.raises(EvidenceEmissionError, match="subprocess-reported spec_commit"):
        _emit_native_evidence(session2, tmp_path / "e.jsonl", _make_context(tmp_path),
                              REFERENCE_PYTHON_LITE_REGISTRY)


# ===========================================================================
# R6.2c: in-process subject / version binding
# ===========================================================================

def test_forged_in_process_subject_name_rejected(tmp_path):
    ctx = _make_context(tmp_path, subject={"kind": "implementation", "name": "another-impl", "version": "0.1-draft"})
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="implementation_name"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_forged_in_process_subject_version_rejected(tmp_path):
    ctx = _make_context(tmp_path, subject={"kind": "implementation", "name": "reference-python", "version": "9.9"})
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="implementation_version"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_forged_in_process_adapter_version_rejected(tmp_path):
    ctx = _make_context(tmp_path, adapter={"name": "ReferencePythonAdapter", "version": "certified-3.0"})
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    with pytest.raises(EvidenceEmissionError, match="adapter_version"):
        _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_missing_runtime_identity_rejects_native_emission(tmp_path):
    """An adapter that supplies NO evidence_identity AND no subprocess
    metadata MUST cause native emission to fail."""
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    no_identity_ai = {"class_name": "SomeAdapter"}  # no evidence_identity, no subprocess
    session2 = ExecutionSession(
        report_dict=session.report_dict, report_bytes=session.report_bytes,
        report_path=session.report_path, report_sha256=session.report_sha256,
        outcome_kinds=session.outcome_kinds, suite_commit=session.suite_commit,
        adapter_class="SomeAdapter", adapter_info=no_identity_ai,
        profile=session.profile, started_at=session.started_at,
        finished_at=session.finished_at,
        source_state_before=dict(CLEAN_SOURCE_STATE),
        source_state_after=dict(CLEAN_SOURCE_STATE),
    )
    ctx = _make_context(tmp_path, adapter={"name": "SomeAdapter", "version": "x"})
    with pytest.raises(EvidenceEmissionError, match="evidence_identity"):
        _emit_native_evidence(session2, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)


def test_matching_evidence_identity_succeeds(tmp_path, clean_source):
    """The reference in-process adapter's evidence_identity matches the
    reference registry's declared subject/adapter, so integrated
    emission succeeds."""
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    assert records is not None and len(records) == 17


def test_runner_collects_evidence_identity_from_adapter(tmp_path):
    """The runner MUST invoke adapter.evidence_identity() and store
    the result under adapter_info.evidence_identity."""
    report, _ = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
    )
    identity = (report.adapter_info or {}).get("evidence_identity")
    assert identity == {
        "adapter_name": "ReferencePythonAdapter",
        "adapter_version": "translation-only",
        "implementation_name": "reference-python",
        "implementation_version": "0.1-draft",
    }


# ===========================================================================
# R6.2c: traceback disclosure control
# ===========================================================================

def test_records_do_not_expose_raw_traceback(tmp_path):
    """Emitted records MUST NOT copy the raw traceback into
    observed_evidence.error. The redacted error_summary and stable
    failure_code stand in; the full text remains in the pinned
    results_artifact."""
    ugly_error = (
        "Traceback (most recent call last):\n"
        "  File \"/tmp/pytest-of-secret/test.py\", line 42, in run\n"
        "    raise RuntimeError('C:\\Users\\somebody\\workspace failed')\n"
        "RuntimeError: C:\\Users\\somebody\\workspace failed"
    )
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "execution_error", "error": ugly_error},
    ])
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    obs = recs[0]["observed_evidence"]
    assert "error" not in obs, "raw error text must not be copied into evidence records"
    assert obs["failure_code"] == "HARNESS_EXECUTION_ERROR"
    assert obs["error_summary"] == "Runtime execution failed; inspect the pinned result artifact."
    # And the redacted-summary path never has workstation paths anywhere.
    dumped = json.dumps(recs[0])
    assert "/tmp/pytest-of-secret" not in dumped
    assert "C:\\Users\\somebody" not in dumped
    assert "somebody" not in dumped
    assert "workspace failed" not in dumped


def test_assertion_failure_summary_is_redacted_and_capped(tmp_path):
    long_error = ("assertion failed: " + "verbose " * 60
                  + "in /tmp/pytest-of-someone/x/y.py at line 99")
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "outcome_kind": "assertion_failure", "error": long_error},
    ])
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    obs = recs[0]["observed_evidence"]
    assert obs["failure_code"] == "ASSERTION_FAILURE"
    assert obs["error_summary"] is not None
    assert len(obs["error_summary"]) <= 200
    assert "/tmp/pytest-of-someone" not in obs["error_summary"]


def test_passed_case_has_no_error_summary(tmp_path):
    session = _harness_bypass_session(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "outcome_kind": "passed"},
    ])
    ctx = _make_context(tmp_path)
    recs = _emit_native_evidence(session, tmp_path / "e.jsonl", ctx, REFERENCE_PYTHON_LITE_REGISTRY)
    obs = recs[0]["observed_evidence"]
    assert obs["failure_code"] is None
    assert obs["error_summary"] is None
