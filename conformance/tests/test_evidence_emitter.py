"""R6.2 tests: EvidenceRecord emission alongside the legacy
ConformanceReport.

Acceptance-criteria coverage:
  - existing 26 pre-R6 conformance tests remain unchanged (separate file)
  - legacy report emits successfully AND is byte-identical to what the
    unmodified runner produces (byte compat)
  - EvidenceRecords validate against the merged R6.1c schema
  - emitted hashes resolve to actual artifacts
  - all commit fields use full 40-char SHAs
  - timestamps pass strict RFC 3339 validation
  - deterministic runs produce stable semantic records
  - failure, not_testable, and limitation cases are covered
  - malformed emission fails closed
  - schema/repo/reference-python/conformance/MCP suites remain green
    (checked via CLI after commit, not inside this test file)
"""

from __future__ import annotations

import copy
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
    EmissionContext,
    emit_evidence_from_report,
    normalize_for_determinism,
)
from conformance.adapters.reference_python import ReferencePythonAdapter


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
VALIDATOR_CLI = ROOT / "scripts" / "validate_evidence.py"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_evidence  # noqa: E402


FAKE_SPEC_COMMIT = "a" * 40
FAKE_HARNESS_COMMIT = "b" * 40


def _make_context(**overrides):
    kwargs = dict(
        spec_commit=FAKE_SPEC_COMMIT,
        harness_commit=FAKE_HARNESS_COMMIT,
        profile="PAMSPEC-Lite",
        profile_version="0.1-draft",
        subject={"kind": "implementation", "name": "reference-python", "version": "0.1-draft"},
        run_id="testrun0001",
    )
    kwargs.update(overrides)
    return EmissionContext(**kwargs)


def _run_lite_against_reference(tmp_path: Path):
    """Run the Lite profile against ReferencePythonAdapter, persist the
    legacy report to tmp_path, and return (report_dict, report_path)."""
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    report = runner.run_profile("PAMSPEC-Lite", ReferencePythonAdapter)
    report_dict = report.to_dict()
    report_path = tmp_path / "conformance-report.json"
    report_path.write_text(report.to_json(), encoding="utf-8")
    return report, report_dict, report_path


# ---------- positive: end-to-end ----------

def test_end_to_end_emission_produces_valid_chain(tmp_path):
    report, report_dict, report_path = _run_lite_against_reference(tmp_path)
    emission_path = tmp_path / "evidence-chain.jsonl"
    context = _make_context()

    records = emit_evidence_from_report(report_dict, report_path, emission_path, context)

    assert len(records) == len(report.cases) == 15
    assert emission_path.exists()
    lines = emission_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(records)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(schema)
    for rec in records:
        errors = list(schema_validator.iter_errors(rec))
        assert not errors, f"{rec['record_id']} failed schema: {[e.message for e in errors]}"


def test_emitted_chain_passes_full_validator_cli(tmp_path):
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    emission_path = tmp_path / "evidence-chain-cli.jsonl"
    emit_evidence_from_report(report_dict, report_path, emission_path, _make_context())
    r = subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), str(emission_path)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


# ---------- semantic content ----------

def test_records_use_native_emission_origin(tmp_path):
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    assert all(r["origin"] == "native_emission" for r in records)


def test_records_use_conformance_test_kind(tmp_path):
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    assert all(r["test_kind"] == "conformance" for r in records)


def test_records_include_adapter_evidence_source(tmp_path):
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    assert all("adapter" in r["evidence_source"] for r in records)


def test_records_use_full_40_char_commit_shas(tmp_path):
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    sha40 = re.compile(r"^[0-9a-f]{40}$")
    for r in records:
        assert sha40.match(r["pamspec_context"]["spec_commit"])
        assert sha40.match(r["pamspec_context"]["harness_commit"])
        assert sha40.match(r["evidence_commit"])


def test_records_use_strict_rfc3339_timestamps(tmp_path):
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    checker = validate_evidence._make_datetime_format_checker()
    for r in records:
        checker.check(r["recorded_at"], "date-time")
        checker.check(r["evidence_observed_at"], "date-time")


def test_results_artifact_hash_resolves(tmp_path):
    import hashlib
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    expected = hashlib.sha256(report_path.read_bytes()).hexdigest()
    for r in records:
        assert r["results_artifact"]["sha256"] == expected
        assert Path(r["results_artifact"]["reference"]).name == report_path.name


# ---------- legacy compatibility ----------

def test_legacy_report_bytes_unchanged_by_emission(tmp_path):
    """Emitter must NEVER modify the legacy report file."""
    _, report_dict, report_path = _run_lite_against_reference(tmp_path)
    original_bytes = report_path.read_bytes()
    emit_evidence_from_report(
        report_dict, report_path, tmp_path / "c.jsonl", _make_context(),
    )
    assert report_path.read_bytes() == original_bytes, \
        "emitter must not modify the legacy report file"


def test_legacy_to_dict_shape_unchanged(tmp_path):
    """The legacy ConformanceReport.to_dict() shape must be identical
    to the R7 shape at merged main (a6a0d05...). If R6.2 accidentally
    added a key, this test flags it."""
    report, _, _ = _run_lite_against_reference(tmp_path)
    d = report.to_dict()
    expected_top_keys = {
        "report_format_version", "profile", "adapter_class", "adapter_info",
        "suite_commit", "started_at", "finished_at", "totals", "cases",
    }
    assert set(d.keys()) == expected_top_keys, \
        f"legacy report top-level keys drifted: {set(d.keys()) ^ expected_top_keys}"


# ---------- determinism ----------

def test_deterministic_runs_produce_stable_semantic_records(tmp_path):
    """Two independent runs at the same commit, with masked timing and
    per-run fields, must produce semantically identical records."""
    _, d1, p1 = _run_lite_against_reference(tmp_path)
    time.sleep(1.0)  # ensure recorded_at differs
    _, d2, p2 = _run_lite_against_reference(tmp_path / "second")

    r1 = emit_evidence_from_report(d1, p1, tmp_path / "c1.jsonl", _make_context(run_id="r1"))
    r2 = emit_evidence_from_report(d2, p2, tmp_path / "c2.jsonl", _make_context(run_id="r2"))

    n1 = [normalize_for_determinism(x) for x in r1]
    n2 = [normalize_for_determinism(x) for x in r2]
    # Also mask reference (path differs between temp dirs); we already
    # masked sha256 in the helper. Mask reference path too.
    for arr in (n1, n2):
        for rec in arr:
            if rec.get("results_artifact"):
                rec["results_artifact"]["reference"] = "<masked>"
            # observed_evidence.error may be None on both runs; leave as-is
    assert n1 == n2, "semantic records must be stable across identical runs"


# ---------- classification: pass / fail / not_testable ----------

def test_passing_case_classifies_native_confirmed(tmp_path):
    fake_report = {
        "profile": "PAMSPEC-Lite",
        "adapter_class": "FakeAdapter",
        "adapter_info": {"class_name": "FakeAdapter"},
        "cases": [{"name": "case_ok", "passed": True, "duration_ms": 1.0}],
    }
    p = tmp_path / "r.json"
    p.write_text(json.dumps(fake_report), encoding="utf-8")
    recs = emit_evidence_from_report(fake_report, p, tmp_path / "c.jsonl", _make_context())
    assert recs[0]["classification"] == "native"
    assert recs[0]["claim_status"] == "confirmed"


def test_failing_case_classifies_gap_confirmed(tmp_path):
    fake_report = {
        "profile": "PAMSPEC-Lite",
        "adapter_class": "FakeAdapter",
        "adapter_info": {"class_name": "FakeAdapter"},
        "cases": [{"name": "case_fail", "passed": False, "duration_ms": 1.0,
                   "error": "assertion failed: expected 3 got 2"}],
    }
    p = tmp_path / "r.json"
    p.write_text(json.dumps(fake_report), encoding="utf-8")
    recs = emit_evidence_from_report(fake_report, p, tmp_path / "c.jsonl", _make_context())
    assert recs[0]["classification"] == "gap"
    assert recs[0]["claim_status"] == "confirmed"
    assert any("case failed" in lim for lim in recs[0]["limitations"])


def test_missing_feature_classifies_not_testable(tmp_path):
    fake_report = {
        "profile": "PAMSPEC-Lite",
        "adapter_class": "FakeAdapter",
        "adapter_info": {"class_name": "FakeAdapter"},
        "cases": [{"name": "case_missing", "passed": False, "duration_ms": 0.5,
                   "error": "adapter missing feature: delegation.check"}],
    }
    p = tmp_path / "r.json"
    p.write_text(json.dumps(fake_report), encoding="utf-8")
    recs = emit_evidence_from_report(fake_report, p, tmp_path / "c.jsonl", _make_context())
    assert recs[0]["classification"] == "not_testable"
    assert recs[0]["claim_status"] == "not_testable"
    assert len(recs[0]["limitations"]) >= 1


# ---------- fail-closed on bad input ----------

def test_missing_spec_commit_raises():
    with pytest.raises(ValueError, match="spec_commit"):
        EmissionContext(
            spec_commit="",
            harness_commit=FAKE_HARNESS_COMMIT,
            profile="PAMSPEC-Lite",
            profile_version="0.1-draft",
            subject={"kind": "implementation", "name": "x", "version": "y"},
        )


def test_short_spec_commit_raises():
    with pytest.raises(ValueError, match="spec_commit"):
        EmissionContext(
            spec_commit="abc123",
            harness_commit=FAKE_HARNESS_COMMIT,
            profile="PAMSPEC-Lite",
            profile_version="0.1-draft",
            subject={"kind": "implementation", "name": "x", "version": "y"},
        )


def test_short_harness_commit_raises():
    with pytest.raises(ValueError, match="harness_commit"):
        EmissionContext(
            spec_commit=FAKE_SPEC_COMMIT,
            harness_commit="abc123",
            profile="PAMSPEC-Lite",
            profile_version="0.1-draft",
            subject={"kind": "implementation", "name": "x", "version": "y"},
        )


def test_empty_profile_raises():
    with pytest.raises(ValueError, match="profile"):
        EmissionContext(
            spec_commit=FAKE_SPEC_COMMIT,
            harness_commit=FAKE_HARNESS_COMMIT,
            profile="",
            profile_version="0.1-draft",
            subject={"kind": "implementation", "name": "x", "version": "y"},
        )


def test_empty_profile_version_raises():
    with pytest.raises(ValueError, match="profile_version"):
        EmissionContext(
            spec_commit=FAKE_SPEC_COMMIT,
            harness_commit=FAKE_HARNESS_COMMIT,
            profile="PAMSPEC-Lite",
            profile_version="",
            subject={"kind": "implementation", "name": "x", "version": "y"},
        )


def test_missing_report_file_raises(tmp_path):
    fake_report = {"profile": "PAMSPEC-Lite", "cases": []}
    with pytest.raises(FileNotFoundError):
        emit_evidence_from_report(
            fake_report,
            tmp_path / "does-not-exist.json",
            tmp_path / "c.jsonl",
            _make_context(),
        )


def test_report_missing_cases_raises(tmp_path):
    p = tmp_path / "r.json"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="cases"):
        emit_evidence_from_report({}, p, tmp_path / "c.jsonl", _make_context())


def test_case_missing_name_raises(tmp_path):
    p = tmp_path / "r.json"
    p.write_text("{}", encoding="utf-8")
    # subject + adapter provided in context so derivation is skipped
    # and the name check is the first thing to fail.
    context = _make_context(adapter={"name": "FakeAdapter", "version": "0"})
    fake_report = {"profile": "PAMSPEC-Lite", "cases": [{"passed": True, "duration_ms": 1}]}
    with pytest.raises(ValueError, match="'name'"):
        emit_evidence_from_report(fake_report, p, tmp_path / "c.jsonl", context)


def test_subject_derivation_fails_when_in_process_adapter_has_no_identity(tmp_path):
    """The in-process reference adapter carries no subprocess-reported
    implementation identity. Without an explicit subject, the emitter
    MUST refuse rather than emit an unidentified record."""
    p = tmp_path / "r.json"
    fake_report = {
        "profile": "PAMSPEC-Lite",
        "adapter_class": "SomeAdapter",
        "adapter_info": {"class_name": "SomeAdapter"},
        "cases": [{"name": "case_x", "passed": True, "duration_ms": 1.0}],
    }
    p.write_text(json.dumps(fake_report), encoding="utf-8")
    context = EmissionContext(
        spec_commit=FAKE_SPEC_COMMIT,
        harness_commit=FAKE_HARNESS_COMMIT,
        profile="PAMSPEC-Lite",
        profile_version="0.1-draft",
        # subject=None deliberately omitted to trigger derivation
    )
    with pytest.raises(ValueError, match="cannot derive subject"):
        emit_evidence_from_report(fake_report, p, tmp_path / "c.jsonl", context)


# ---------- append-only behavior ----------

def test_emission_appends_and_preserves_prior_lines(tmp_path):
    """Simulate a second emission into the same JSONL and confirm the
    first records are byte-identical prefix (append-only)."""
    _, d1, p1 = _run_lite_against_reference(tmp_path)
    chain = tmp_path / "chain.jsonl"
    emit_evidence_from_report(d1, p1, chain, _make_context(run_id="one"))
    prefix_bytes = chain.read_bytes()

    _, d2, p2 = _run_lite_against_reference(tmp_path / "second")
    emit_evidence_from_report(d2, p2, chain, _make_context(run_id="two"))
    combined = chain.read_bytes()

    assert combined.startswith(prefix_bytes), "emission must be append-only"


def test_records_pass_all_chain_level_invariants_when_emitted_alone(tmp_path):
    """One emission's records — even 15 of them — must pass the R6.1c
    chain-level invariants when validated as a standalone chain file."""
    _, d, p = _run_lite_against_reference(tmp_path)
    chain = tmp_path / "chain.jsonl"
    emit_evidence_from_report(d, p, chain, _make_context())
    r = subprocess.run(
        [sys.executable, str(VALIDATOR_CLI), str(chain)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"stdout={r.stdout}"


def test_default_limitations_always_present(tmp_path):
    _, d, p = _run_lite_against_reference(tmp_path)
    records = emit_evidence_from_report(d, p, tmp_path / "c.jsonl", _make_context())
    for r in records:
        assert DEFAULT_ADAPTER_LIMITATION in r["limitations"], \
            "the adapter-only-evidence limitation must be present on every record"
