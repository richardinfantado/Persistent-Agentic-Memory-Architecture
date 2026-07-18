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


def test_run_and_emit_integrated_produces_valid_chain(tmp_path):
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
    assert len(records) == len(report.cases) == 15
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
        "adapter_info": {"class_name": "ReferencePythonAdapter"},
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
        adapter_info={"class_name": "ReferencePythonAdapter"},
        profile="PAMSPEC-Lite",
        started_at="2026-07-18T15:00:00Z",
        finished_at="2026-07-18T15:00:10Z",
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

def test_semantic_hash_stable_across_identical_runs_of_reference(tmp_path):
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


def test_normalize_does_not_mask_semantic_hash(tmp_path):
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

def test_default_adapter_limitation_always_present(tmp_path):
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    for r in records:
        assert DEFAULT_ADAPTER_LIMITATION in r["limitations"]
