"""R6.2a tests: EvidenceRecord emission integrated with the harness.

Covers every reviewer-required guarantee:
  * `run_and_emit` orchestrates both artifacts in one invocation.
  * Legacy behavior (no evidence_output_path) unchanged.
  * Single authoritative source (report file bytes are hashed and parsed).
  * Explicit CaseAssessment required for every reported case; missing
    entries fail closed.
  * No pass/fail-only classification inference; classification comes
    from the registry.
  * Structured "adapter missing feature" detection (prefix, not
    fuzzy substring).
  * Preflight-and-atomic-commit: schema + chain-invariant checks before
    any write; failures leave the existing evidence file byte-identical.
  * Profile identity: report.profile MUST match context.profile.
  * Portable artifact references only (relative to artifact_root; no
    absolute paths, no .. traversal).
  * evidence_commit is a distinct required context field.
  * observed_evidence.semantic_results_sha256 captures a canonical
    projection and surfaces real semantic differences.
  * Determinism helper works and does not mask the semantic hash.
"""

from __future__ import annotations

import copy
import hashlib
import json
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
    emit_evidence_from_report_file,
    normalize_for_determinism,
    run_and_emit,
)
from conformance.harness.case_registries.reference_python_lite import (
    REFERENCE_PYTHON_LITE_REGISTRY,
    REFERENCE_PYTHON_SUBJECT,
    REFERENCE_PYTHON_ADAPTER,
)
from conformance.adapters.reference_python import ReferencePythonAdapter


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
VALIDATOR_CLI = ROOT / "scripts" / "validate_evidence.py"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence  # noqa: E402


FAKE_SPEC = "a" * 40
FAKE_HARNESS = "b" * 40
FAKE_EVIDENCE = "c" * 40


def _make_context(tmp_path: Path, **overrides) -> EmissionContext:
    kwargs = dict(
        spec_commit=FAKE_SPEC,
        harness_commit=FAKE_HARNESS,
        evidence_commit=FAKE_EVIDENCE,
        profile="PAMSPEC-Lite",
        profile_version="0.1-draft",
        artifact_root=tmp_path,
        subject=dict(REFERENCE_PYTHON_SUBJECT),
        adapter=dict(REFERENCE_PYTHON_ADAPTER),
        run_id="testrun0001",
    )
    kwargs.update(overrides)
    return EmissionContext(**kwargs)


# --------------------------------------------------------------------------- #
# run_and_emit orchestration
# --------------------------------------------------------------------------- #

def test_run_and_emit_produces_only_legacy_report_when_evidence_output_absent(tmp_path):
    """Default (backward-compat) call path: no evidence emitted."""
    report_path = tmp_path / "report.json"
    report, records = run_and_emit(
        "PAMSPEC-Lite",
        ReferencePythonAdapter,
        report_output_path=report_path,
    )
    assert report_path.exists()
    assert records is None
    # No stray evidence file created anywhere.
    assert not list(tmp_path.glob("*.jsonl"))


def test_run_and_emit_produces_both_artifacts_in_one_invocation(tmp_path):
    report_path = tmp_path / "report.json"
    evidence_path = tmp_path / "evidence.jsonl"
    context = _make_context(tmp_path)

    report, records = run_and_emit(
        "PAMSPEC-Lite",
        ReferencePythonAdapter,
        report_output_path=report_path,
        evidence_output_path=evidence_path,
        context=context,
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )

    assert report_path.exists()
    assert evidence_path.exists()
    assert records is not None
    assert len(records) == len(report.cases) == 15


def test_run_and_emit_requires_context_when_evidence_requested(tmp_path):
    with pytest.raises(EvidenceEmissionError):
        run_and_emit(
            "PAMSPEC-Lite",
            ReferencePythonAdapter,
            report_output_path=tmp_path / "r.json",
            evidence_output_path=tmp_path / "e.jsonl",
            context=None,
            case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
        )


def test_run_and_emit_requires_registry_when_evidence_requested(tmp_path):
    with pytest.raises(EvidenceEmissionError):
        run_and_emit(
            "PAMSPEC-Lite",
            ReferencePythonAdapter,
            report_output_path=tmp_path / "r.json",
            evidence_output_path=tmp_path / "e.jsonl",
            context=_make_context(tmp_path),
            case_registry=None,
        )


# --------------------------------------------------------------------------- #
# Single authoritative source
# --------------------------------------------------------------------------- #

def test_emitter_loads_and_hashes_same_bytes(tmp_path):
    report_path = tmp_path / "report.json"
    evidence_path = tmp_path / "evidence.jsonl"
    context = _make_context(tmp_path)
    report, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=report_path,
        evidence_output_path=evidence_path,
        context=context, case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    expected = hashlib.sha256(report_path.read_bytes()).hexdigest()
    for r in records:
        assert r["results_artifact"]["sha256"] == expected


# --------------------------------------------------------------------------- #
# Schema and chain-level validity
# --------------------------------------------------------------------------- #

def test_emitted_chain_passes_schema_and_chain_invariants(tmp_path):
    report_path = tmp_path / "report.json"
    evidence_path = tmp_path / "evidence.jsonl"
    run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=report_path,
        evidence_output_path=evidence_path,
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    r = subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), str(evidence_path)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


def test_records_use_native_emission_origin_and_conformance_kind(tmp_path):
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    for r in records:
        assert r["origin"] == "native_emission"
        assert r["test_kind"] == "conformance"
        assert "adapter" in r["evidence_source"]


def test_records_use_full_40_char_shas_and_strict_rfc3339_timestamps(tmp_path):
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    sha40 = re.compile(r"^[0-9a-f]{40}$")
    checker = validate_evidence._make_datetime_format_checker()
    for r in records:
        assert sha40.match(r["pamspec_context"]["spec_commit"])
        assert sha40.match(r["pamspec_context"]["harness_commit"])
        assert sha40.match(r["evidence_commit"])
        checker.check(r["recorded_at"], "date-time")
        checker.check(r["evidence_observed_at"], "date-time")


# --------------------------------------------------------------------------- #
# Legacy compat
# --------------------------------------------------------------------------- #

def test_default_call_produces_legacy_report_with_unchanged_shape(tmp_path):
    report_path = tmp_path / "r.json"
    report, _ = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=report_path,
    )
    d = report.to_dict()
    expected_top_keys = {
        "report_format_version", "profile", "adapter_class", "adapter_info",
        "suite_commit", "started_at", "finished_at", "totals", "cases",
    }
    assert set(d.keys()) == expected_top_keys


def test_emission_does_not_modify_legacy_report(tmp_path):
    report_path = tmp_path / "r.json"
    evidence_path = tmp_path / "e.jsonl"
    run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=report_path,
        evidence_output_path=evidence_path,
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    bytes_after_emission = report_path.read_bytes()
    # Second emission into a different chain must not touch the report
    other = tmp_path / "e2.jsonl"
    emit_evidence_from_report_file(
        report_path, other, _make_context(tmp_path, run_id="second"),
        REFERENCE_PYTHON_LITE_REGISTRY,
    )
    assert report_path.read_bytes() == bytes_after_emission


# --------------------------------------------------------------------------- #
# Explicit classification (no pass/fail inference)
# --------------------------------------------------------------------------- #

def _write_report(tmp_path: Path, cases: list[dict], profile: str = "PAMSPEC-Lite") -> Path:
    r = {
        "profile": profile,
        "adapter_class": "ReferencePythonAdapter",
        "adapter_info": {"class_name": "ReferencePythonAdapter"},
        "cases": cases,
    }
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = tmp_path / "r.json"
    p.write_text(json.dumps(r), encoding="utf-8")
    return p


def test_passing_case_uses_registry_pass_action(tmp_path):
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
    ])
    recs = emit_evidence_from_report_file(
        p, tmp_path / "e.jsonl", _make_context(tmp_path),
        REFERENCE_PYTHON_LITE_REGISTRY,
    )
    assert recs[0]["classification"] == "native"
    assert recs[0]["claim_status"] == "confirmed"


def test_failing_case_uses_registry_fail_action(tmp_path):
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False, "duration_ms": 1.0,
         "error": "assertion failed: expected 3 got 2"},
    ])
    recs = emit_evidence_from_report_file(
        p, tmp_path / "e.jsonl", _make_context(tmp_path),
        REFERENCE_PYTHON_LITE_REGISTRY,
    )
    # Reference-python registry says fail -> gap/confirmed
    assert recs[0]["classification"] == "gap"
    assert recs[0]["claim_status"] == "confirmed"
    assert any("case failed" in lim for lim in recs[0]["limitations"])


def test_missing_feature_uses_registry_missing_feature_action(tmp_path):
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": False, "duration_ms": 0.5,
         "error": "adapter missing feature: query"},
    ])
    recs = emit_evidence_from_report_file(
        p, tmp_path / "e.jsonl", _make_context(tmp_path),
        REFERENCE_PYTHON_LITE_REGISTRY,
    )
    assert recs[0]["classification"] == "not_testable"
    assert recs[0]["claim_status"] == "not_testable"


def test_case_assessment_rejects_construction_without_explicit_stances():
    """R6.2a hard rule: registry authors MUST state a deliberate
    stance for pass/fail/missing-feature. Omitting them raises
    TypeError from the dataclass. This prevents unannotated passing
    or failing cases from being emitted with a silent default."""
    with pytest.raises(TypeError):
        CaseAssessment(requirement_id="PAMSPEC-Lite.SOMETHING")  # type: ignore[call-arg]


def test_case_assessment_rejects_invalid_classification_enum():
    with pytest.raises(ValueError, match="on_pass_classification"):
        CaseAssessment(
            requirement_id="PAMSPEC-Lite.SOMETHING",
            on_pass_classification="inconclusive",  # not a classification enum value
            on_pass_claim_status="inconclusive",
            on_fail_classification="gap",
            on_fail_claim_status="confirmed",
            on_missing_feature_classification="not_testable",
            on_missing_feature_claim_status="not_testable",
        )


def test_case_assessment_permits_explicit_questionable_stance(tmp_path):
    """Registry authors CAN choose a conservative stance explicitly:
    a passing test recorded as `questionable`/`inconclusive` for a
    framework subject where native-ness is not established."""
    ca = CaseAssessment(
        requirement_id="PAMSPEC-Lite.SOMETHING",
        on_pass_classification="questionable",
        on_pass_claim_status="inconclusive",
        on_fail_classification="questionable",
        on_fail_claim_status="inconclusive",
        on_missing_feature_classification="not_testable",
        on_missing_feature_claim_status="not_testable",
    )
    p = _write_report(tmp_path, [
        {"name": "case_x", "passed": True, "duration_ms": 1.0},
    ])
    recs = emit_evidence_from_report_file(
        p, tmp_path / "e.jsonl", _make_context(tmp_path),
        {"case_x": ca},
    )
    assert recs[0]["classification"] == "questionable"
    assert recs[0]["claim_status"] == "inconclusive"


# --------------------------------------------------------------------------- #
# Fail-closed on registry gaps
# --------------------------------------------------------------------------- #

def test_missing_registry_entry_rejects_emission(tmp_path):
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
        {"name": "case_UNMAPPED", "passed": True, "duration_ms": 1.0},
    ])
    evidence = tmp_path / "e.jsonl"
    assert not evidence.exists()
    with pytest.raises(EvidenceEmissionError, match="case_UNMAPPED"):
        emit_evidence_from_report_file(
            p, evidence, _make_context(tmp_path), REFERENCE_PYTHON_LITE_REGISTRY,
        )
    # And no evidence was written.
    assert not evidence.exists()


# --------------------------------------------------------------------------- #
# Profile identity
# --------------------------------------------------------------------------- #

def test_profile_mismatch_rejects_emission(tmp_path):
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
    ], profile="PAMSPEC-Delegation")  # report says Delegation
    with pytest.raises(EvidenceEmissionError, match="profile"):
        emit_evidence_from_report_file(
            p, tmp_path / "e.jsonl",
            _make_context(tmp_path),  # context says PAMSPEC-Lite
            REFERENCE_PYTHON_LITE_REGISTRY,
        )


# --------------------------------------------------------------------------- #
# Fail-closed: SHA, profile, artifact_root, subject/adapter validation
# --------------------------------------------------------------------------- #

def test_context_rejects_short_spec_commit(tmp_path):
    with pytest.raises(ValueError, match="spec_commit"):
        EmissionContext(
            spec_commit="abc", harness_commit=FAKE_HARNESS,
            evidence_commit=FAKE_EVIDENCE, profile="PAMSPEC-Lite",
            profile_version="0.1-draft", artifact_root=tmp_path,
            subject=dict(REFERENCE_PYTHON_SUBJECT),
        )


def test_context_rejects_missing_evidence_commit(tmp_path):
    with pytest.raises(ValueError, match="evidence_commit"):
        EmissionContext(
            spec_commit=FAKE_SPEC, harness_commit=FAKE_HARNESS,
            evidence_commit="", profile="PAMSPEC-Lite",
            profile_version="0.1-draft", artifact_root=tmp_path,
            subject=dict(REFERENCE_PYTHON_SUBJECT),
        )


def test_context_rejects_nonexistent_artifact_root(tmp_path):
    with pytest.raises(ValueError, match="artifact_root"):
        EmissionContext(
            spec_commit=FAKE_SPEC, harness_commit=FAKE_HARNESS,
            evidence_commit=FAKE_EVIDENCE, profile="PAMSPEC-Lite",
            profile_version="0.1-draft",
            artifact_root=tmp_path / "does-not-exist",
            subject=dict(REFERENCE_PYTHON_SUBJECT),
        )


def test_context_rejects_invalid_env_manifest(tmp_path):
    with pytest.raises(ValueError, match="environment_manifest"):
        EmissionContext(
            spec_commit=FAKE_SPEC, harness_commit=FAKE_HARNESS,
            evidence_commit=FAKE_EVIDENCE, profile="PAMSPEC-Lite",
            profile_version="0.1-draft", artifact_root=tmp_path,
            subject=dict(REFERENCE_PYTHON_SUBJECT),
            environment_manifest={"reference": "x"},  # missing sha256
        )


# --------------------------------------------------------------------------- #
# Portable artifact references
# --------------------------------------------------------------------------- #

def test_reference_is_portable_relative_path(tmp_path):
    _, records = run_and_emit(
        "PAMSPEC-Lite", ReferencePythonAdapter,
        report_output_path=tmp_path / "sub" / "r.json",
        evidence_output_path=tmp_path / "e.jsonl",
        context=_make_context(tmp_path),
        case_registry=REFERENCE_PYTHON_LITE_REGISTRY,
    )
    for r in records:
        ref = r["results_artifact"]["reference"]
        assert ref == "sub/r.json", f"non-portable reference emitted: {ref}"


def test_reference_outside_artifact_root_rejected(tmp_path):
    """A report path outside artifact_root is rejected — the reference
    could not be made portable."""
    (tmp_path / "root").mkdir()
    outside = tmp_path / "outside" / "r.json"
    outside.parent.mkdir()
    outside.write_text(json.dumps({"profile": "PAMSPEC-Lite", "cases": []}), encoding="utf-8")
    context = _make_context(tmp_path / "root")
    with pytest.raises(EvidenceEmissionError, match="not under artifact_root"):
        emit_evidence_from_report_file(
            outside, tmp_path / "e.jsonl", context, REFERENCE_PYTHON_LITE_REGISTRY,
        )


# --------------------------------------------------------------------------- #
# Atomic / preflight: failures leave chain unchanged
# --------------------------------------------------------------------------- #

def test_duplicate_record_id_rejects_and_leaves_chain_unchanged(tmp_path):
    """Emit once, then try to emit again with the same run_id -> record_id
    collision -> validator rejects -> file is byte-identical to first
    emission."""
    context1 = _make_context(tmp_path, run_id="samerun")
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
    ])
    evidence = tmp_path / "e.jsonl"
    emit_evidence_from_report_file(p, evidence, context1, REFERENCE_PYTHON_LITE_REGISTRY)
    first_bytes = evidence.read_bytes()
    with pytest.raises(EvidenceEmissionError):
        emit_evidence_from_report_file(p, evidence, context1, REFERENCE_PYTHON_LITE_REGISTRY)
    assert evidence.read_bytes() == first_bytes


def test_missing_report_file_leaves_chain_unchanged(tmp_path):
    evidence = tmp_path / "e.jsonl"
    evidence.write_bytes(b"existing_bytes_never_touched\n")
    with pytest.raises(FileNotFoundError):
        emit_evidence_from_report_file(
            tmp_path / "nope.json", evidence, _make_context(tmp_path),
            REFERENCE_PYTHON_LITE_REGISTRY,
        )
    assert evidence.read_bytes() == b"existing_bytes_never_touched\n"


def test_missing_registry_entry_leaves_chain_unchanged(tmp_path):
    evidence = tmp_path / "e.jsonl"
    evidence.write_bytes(b"prior\n")
    p = _write_report(tmp_path, [
        {"name": "case_UNKNOWN", "passed": True, "duration_ms": 1.0},
    ])
    with pytest.raises(EvidenceEmissionError):
        emit_evidence_from_report_file(
            p, evidence, _make_context(tmp_path),
            REFERENCE_PYTHON_LITE_REGISTRY,
        )
    assert evidence.read_bytes() == b"prior\n"


def test_append_is_byte_prefix_preserving(tmp_path):
    """After a successful append, the pre-existing chain bytes are an
    exact byte prefix of the post-append bytes."""
    ctx1 = _make_context(tmp_path, run_id="first")
    ctx2 = _make_context(tmp_path, run_id="second")
    p = _write_report(tmp_path, [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
    ])
    evidence = tmp_path / "e.jsonl"
    emit_evidence_from_report_file(p, evidence, ctx1, REFERENCE_PYTHON_LITE_REGISTRY)
    prefix = evidence.read_bytes()
    emit_evidence_from_report_file(p, evidence, ctx2, REFERENCE_PYTHON_LITE_REGISTRY)
    combined = evidence.read_bytes()
    assert combined.startswith(prefix), "R6.1c invariant 7 violated: chain not append-only"


# --------------------------------------------------------------------------- #
# Semantic determinism
# --------------------------------------------------------------------------- #

def test_semantic_hash_stable_across_identical_runs(tmp_path):
    """Two independent runs at the same subject produce the same
    canonical semantic hash even though wall-clock and duration
    values differ between runs."""
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
    assert sem1 == sem2, "semantic hash MUST be stable across identical runs"
    # All 15 records in a single run share the same semantic hash (it
    # describes the whole report projection, not any individual case).
    assert len(sem1) == 1


def test_semantic_hash_differs_when_outcomes_differ(tmp_path):
    """If the underlying report has genuinely different outcomes, the
    semantic hash MUST change — determinism cannot mask this."""
    p1 = _write_report(tmp_path / "a", [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
    ])
    (tmp_path / "a").mkdir(exist_ok=True)
    p1.parent.mkdir(parents=True, exist_ok=True)
    p1 = _write_report(tmp_path / "a", [
        {"name": "case_read_returns_current_envelope", "passed": True, "duration_ms": 1.0},
    ])
    p2 = _write_report(tmp_path / "b", [
        {"name": "case_read_returns_current_envelope", "passed": False,
         "duration_ms": 1.0, "error": "assertion failed: x"},
    ])
    r1 = emit_evidence_from_report_file(
        p1, tmp_path / "a" / "e.jsonl",
        _make_context(tmp_path / "a", run_id="one"),
        REFERENCE_PYTHON_LITE_REGISTRY,
    )
    r2 = emit_evidence_from_report_file(
        p2, tmp_path / "b" / "e.jsonl",
        _make_context(tmp_path / "b", run_id="two"),
        REFERENCE_PYTHON_LITE_REGISTRY,
    )
    assert r1[0]["observed_evidence"]["semantic_results_sha256"] \
        != r2[0]["observed_evidence"]["semantic_results_sha256"], \
        "semantic hash MUST differ when the underlying outcome differs"


def test_normalize_does_not_mask_semantic_hash(tmp_path):
    """normalize_for_determinism() must NOT mask the semantic hash;
    that field is the authoritative determinism signal."""
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
    assert n["results_artifact"]["sha256"] == "<masked>"


# --------------------------------------------------------------------------- #
# Default limitation always present
# --------------------------------------------------------------------------- #

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
