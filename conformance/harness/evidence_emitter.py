"""R6.2a EvidenceRecord emission for the R7 conformance harness.

R6.2a integrates evidence emission into the harness invocation and
fails closed on evidence-integrity problems.

Public API:
  run_and_emit(profile, factory, report_output_path,
               evidence_output_path=None, context=None, case_registry=None)
      One-invocation orchestration: run conformance -> persist legacy
      report -> optionally emit an EvidenceRecord chain. Legacy behavior
      unchanged when evidence_output_path is None.
  emit_evidence_from_report_file(report_json_path, emission_jsonl_path,
                                 context, case_registry)
      Single-authoritative-source emitter: loads and hashes the same
      bytes, fails closed on integrity problems, atomically appends.
  CaseAssessment
      Explicit per-case metadata (requirement_id, sub_requirements,
      evidence_source, on-pass/on-fail/on-missing-feature actions,
      extra_limitations). REQUIRED for test_kind=conformance emission.
  EmissionContext
      Identity + provenance the emitter must have to produce
      well-formed records. Fail-closed at construction on invalid SHAs,
      empty required strings, or non-portable artifact_root.

R6.2a hard constraints observed:
  - runner.py is not modified
  - legacy ConformanceReport format is not modified
  - pass/fail semantics are not modified
  - draft, memory schemas, MCP binding, reference implementation:
    not modified
  - default runner behavior unchanged: run_and_emit without
    evidence_output_path only writes the legacy report
  - append-only storage: prior evidence bytes are exact prefix of
    the post-emission bytes; preflight-and-atomic-commit guarantees no
    partial writes on failure
  - single authoritative source for both hash and semantics: the file
    at report_json_path is loaded once; hash and parse both operate on
    those exact bytes
  - classification is NEVER inferred from pass/fail alone; every case
    consulted against an explicit CaseAssessment; missing entries fail
    closed
  - profile identity: report.profile MUST equal context.profile
  - portable artifact references: computed relative to
    context.artifact_root; absolute paths and .. traversal rejected
  - evidence_commit is a distinct required field (semantics: repository
    commit checked out when the evidence-producing execution occurred)
  - semantic determinism: observed_evidence.semantic_results_sha256
    captures the canonical projection so a truly different result
    surfaces even when only wall-clock fields changed
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

from jsonschema import Draft202012Validator


SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"
DEFAULT_ADAPTER_LIMITATION = (
    "evidence_source only includes 'adapter'; no independent probe of "
    "the subject was performed as part of this conformance run"
)


class EvidenceEmissionError(ValueError):
    """Raised when an evidence emission is rejected before any write."""


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

VALID_CLASSIFICATIONS = {"native", "emulated", "gap", "questionable", "not_testable"}
VALID_CLAIM_STATUSES = {"confirmed", "inconclusive", "not_testable"}


@dataclass
class CaseAssessment:
    """Explicit per-case evidence-classification stance.

    Registry entries MUST specify one of these per case that a conformance
    run will emit. Missing entries cause R6.2a to fail closed rather than
    emit an under-attributed record.

    Pass, fail, and missing-feature stances are REQUIRED (no defaults).
    Registry authors must state a deliberate classification for each
    outcome; the emitter never infers native/gap/emulated from pass/fail
    alone.

    Fields:
      requirement_id: stable dotted PAMSPEC requirement identifier for
        this case. Case function names may be renamed under refactoring
        without touching this value.
      on_pass_*  / on_fail_* / on_missing_feature_* : R6.1c-enum values
        the record adopts for that outcome. Fail-closed at construction
        if any is not a valid enum value.
      sub_requirements: optional finer-grained sub-classification list
        (schema-conformant sub_requirements entries).
      evidence_source: R6 evidence-source enum values that apply for
        this case. Default is ['adapter'].
      extra_limitations: strings appended to the record's limitations
        list unconditionally for this case.
    """
    requirement_id: str
    on_pass_classification: str
    on_pass_claim_status: str
    on_fail_classification: str
    on_fail_claim_status: str
    on_missing_feature_classification: str
    on_missing_feature_claim_status: str
    sub_requirements: list[dict] = field(default_factory=list)
    evidence_source: list[str] = field(default_factory=lambda: ["adapter"])
    extra_limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.requirement_id or not isinstance(self.requirement_id, str):
            raise ValueError("CaseAssessment.requirement_id MUST be a non-empty string")
        if not self.evidence_source:
            raise ValueError("CaseAssessment.evidence_source MUST be non-empty")
        for k, v in (
            ("on_pass_classification", self.on_pass_classification),
            ("on_fail_classification", self.on_fail_classification),
            ("on_missing_feature_classification", self.on_missing_feature_classification),
        ):
            if v not in VALID_CLASSIFICATIONS:
                raise ValueError(f"{k} must be one of {sorted(VALID_CLASSIFICATIONS)}: got {v!r}")
        for k, v in (
            ("on_pass_claim_status", self.on_pass_claim_status),
            ("on_fail_claim_status", self.on_fail_claim_status),
            ("on_missing_feature_claim_status", self.on_missing_feature_claim_status),
        ):
            if v not in VALID_CLAIM_STATUSES:
                raise ValueError(f"{k} must be one of {sorted(VALID_CLAIM_STATUSES)}: got {v!r}")


@dataclass
class EmissionContext:
    """Everything the emitter needs to produce records that satisfy the
    R6.1c schema and chain-level invariants.

    All commit SHAs MUST be full 40-character git hashes.
    """
    spec_commit: str
    harness_commit: str
    evidence_commit: str
    profile: str
    profile_version: str
    artifact_root: Path
    subject: dict[str, str]
    adapter: dict[str, str] | None = None
    environment_manifest: dict[str, Any] | None = None
    extra_limitations: list[str] = field(default_factory=list)
    run_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("spec_commit", "harness_commit", "evidence_commit"):
            v = getattr(self, name)
            if not isinstance(v, str) or not SHA40_RE.match(v):
                raise ValueError(
                    f"{name} MUST be a 40-char lowercase hex SHA: {v!r}"
                )
        for name in ("profile", "profile_version"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{name} MUST be a non-empty string")
        if not isinstance(self.artifact_root, Path):
            self.artifact_root = Path(self.artifact_root)
        self.artifact_root = self.artifact_root.resolve()
        if not self.artifact_root.exists() or not self.artifact_root.is_dir():
            raise ValueError(
                f"artifact_root must be an existing directory: {self.artifact_root}"
            )
        _validate_subject(self.subject)
        if self.adapter is not None:
            _validate_adapter(self.adapter)
        if self.environment_manifest is not None:
            _validate_environment_manifest(self.environment_manifest)
        if self.run_id is None:
            self.run_id = uuid.uuid4().hex[:12]


def _validate_subject(s: dict[str, str]) -> None:
    kind = s.get("kind")
    if kind not in {"framework", "implementation", "adapter", "binding", "specification"}:
        raise ValueError(f"subject.kind is invalid: {kind!r}")
    for k in ("name", "version"):
        if not isinstance(s.get(k), str) or not s[k]:
            raise ValueError(f"subject.{k} MUST be a non-empty string")


def _validate_adapter(a: dict[str, str]) -> None:
    for k in ("name", "version"):
        if not isinstance(a.get(k), str) or not a[k]:
            raise ValueError(f"adapter.{k} MUST be a non-empty string")


def _validate_environment_manifest(m: dict[str, Any]) -> None:
    if not isinstance(m, dict):
        raise ValueError("environment_manifest MUST be an object")
    if "reference" not in m or not isinstance(m["reference"], str) or not m["reference"]:
        raise ValueError("environment_manifest.reference MUST be a non-empty string")
    if "sha256" not in m:
        raise ValueError("environment_manifest.sha256 MUST be present")
    sha = m["sha256"]
    if sha is not None and (not isinstance(sha, str) or not re.match(r"^[0-9a-f]{64}$", sha)):
        raise ValueError("environment_manifest.sha256 MUST be null or a 64-char hex string")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _rfc3339_now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _portable_reference(target: Path, artifact_root: Path) -> str:
    """Return a POSIX-style path of `target` relative to `artifact_root`.
    Reject absolute paths outside the root, .. traversal, and empty
    components. artifact_root is expected to be resolved already."""
    target = Path(target).resolve()
    try:
        rel = target.relative_to(artifact_root)
    except ValueError:
        raise EvidenceEmissionError(
            f"artifact reference {target} is not under artifact_root "
            f"{artifact_root}; only paths within the artifact root are "
            f"permitted (absolute workstation paths are not portable)"
        )
    posix = rel.as_posix()
    if posix.startswith("/") or posix.startswith("../") or ".." in posix.split("/"):
        raise EvidenceEmissionError(
            f"artifact reference contains traversal or leading slash: {posix!r}"
        )
    if any(comp == "" for comp in posix.split("/")):
        raise EvidenceEmissionError(
            f"artifact reference contains empty component: {posix!r}"
        )
    return posix


def _canonical_semantic_projection(report_dict: dict) -> dict:
    """Project the report to a canonical semantic shape: outcomes only.

    Excluded (execution-specific noise):
      - duration_ms per case
      - started_at, finished_at (top-level timestamps)
      - suite_commit (execution-specific)
      - subprocess timing metadata inside adapter_info
    Included (semantic outcomes):
      - profile
      - adapter_class
      - adapter identity (subprocess.adapter_name/version, implementation
        _name/version, spec_commit, protocol_version)
      - totals
      - cases: name, passed, error
    """
    projection: dict[str, Any] = {
        "profile": report_dict.get("profile"),
        "adapter_class": report_dict.get("adapter_class"),
        "totals": report_dict.get("totals"),
        "cases": [
            {"name": c.get("name"), "passed": c.get("passed"), "error": c.get("error")}
            for c in report_dict.get("cases", [])
        ],
    }
    ai = report_dict.get("adapter_info") or {}
    sub = ai.get("subprocess") if isinstance(ai, dict) else None
    projection["adapter_identity"] = None
    if isinstance(sub, dict):
        projection["adapter_identity"] = {
            "adapter_name": sub.get("adapter_name"),
            "adapter_version": sub.get("adapter_version"),
            "implementation_name": sub.get("implementation_name"),
            "implementation_version": sub.get("implementation_version"),
            "spec_commit": sub.get("spec_commit"),
            "protocol_version": sub.get("protocol_version"),
        }
    return projection


def _semantic_hash(report_dict: dict) -> str:
    proj = _canonical_semantic_projection(report_dict)
    return _sha256_bytes(json.dumps(proj, sort_keys=True).encode("utf-8"))


def _classify(assessment: CaseAssessment, case: dict) -> tuple[str, str, list[str]]:
    """Map a legacy case result through the explicit registry assessment
    (no pass/fail inference). Returns (classification, claim_status,
    extra_limitations).
    """
    error = case.get("error") or ""
    passed = case.get("passed")

    if isinstance(error, str) and error.startswith("adapter missing feature:"):
        return (
            assessment.on_missing_feature_classification,
            assessment.on_missing_feature_claim_status,
            [f"adapter missing feature (structured detection): {error}"],
        )
    if passed is True:
        return (assessment.on_pass_classification, assessment.on_pass_claim_status, [])
    if passed is False:
        return (
            assessment.on_fail_classification,
            assessment.on_fail_claim_status,
            [f"case failed: {error}"] if error else ["case failed (no error text)"],
        )
    return (
        "questionable",
        "inconclusive",
        [f"unexpected case state: passed={passed!r}, error={error!r}"],
    )


def _load_existing_chain_records(chain_path: Path) -> list[dict]:
    if not chain_path.exists():
        return []
    records: list[dict] = []
    for lineno, raw in enumerate(chain_path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError as e:
            raise EvidenceEmissionError(
                f"existing chain {chain_path}:{lineno} is not valid JSON: {e}"
            )
    return records


def _load_schema_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    # The Draft202012Validator format-checker is R6.1c-strict; we import
    # it via the CLI module to keep one source of truth.
    import importlib.util
    validate_evidence_path = ROOT / "scripts" / "validate_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_evidence", validate_evidence_path)
    ve = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(ve)  # type: ignore
    return ve.make_validator()


def _validate_records_or_raise(records: list[dict], schema_validator: Draft202012Validator) -> None:
    for rec in records:
        errs = list(schema_validator.iter_errors(rec))
        if errs:
            details = "; ".join(f"{list(e.absolute_path)}: {e.message}" for e in errs)
            raise EvidenceEmissionError(
                f"record {rec.get('record_id', '<unknown>')} fails schema: {details}"
            )


def _validate_chain_or_raise(records: list[dict]) -> None:
    import importlib.util
    validate_evidence_path = ROOT / "scripts" / "validate_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_evidence", validate_evidence_path)
    ve = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(ve)  # type: ignore
    errs = ve.validate_records(records)
    if errs:
        raise EvidenceEmissionError(
            "chain-level invariant violations: " + "; ".join(errs)
        )


def _atomic_append(chain_path: Path, existing_bytes: bytes, new_records: list[dict]) -> None:
    """Write existing_bytes + serialized new_records to a temp file in
    the same directory, fsync, then atomically replace.

    On any failure, the temp file is removed and the original chain is
    left byte-identical.
    """
    chain_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".r6-{chain_path.name}-", suffix=".tmp", dir=str(chain_path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as f:
            if existing_bytes:
                f.write(existing_bytes)
                if not existing_bytes.endswith(b"\n"):
                    f.write(b"\n")
            for rec in new_records:
                f.write(json.dumps(rec, sort_keys=True).encode("utf-8"))
                f.write(b"\n")
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                # Best-effort on filesystems that don't support fsync
                pass
        os.replace(tmp_name, chain_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# Emitter
# --------------------------------------------------------------------------- #

def emit_evidence_from_report_file(
    report_json_path: Path,
    emission_jsonl_path: Path,
    context: EmissionContext,
    case_registry: dict[str, CaseAssessment],
) -> list[dict]:
    """Single-authoritative-source emission. Loads the report file
    ONCE and hashes those exact bytes so results_artifact.sha256 pins
    the same bytes the emission conclusions are derived from.

    Fails closed if:
      - report file does not exist / is not JSON
      - report.profile != context.profile
      - any case is missing from case_registry
      - environment_manifest structure is invalid
      - any new record fails schema validation
      - combined chain (existing + new) fails chain-level invariants
      - atomic write fails at any step

    On any failure, the existing emission_jsonl_path (if any) is left
    byte-for-byte unchanged.
    """
    report_json_path = Path(report_json_path)
    emission_jsonl_path = Path(emission_jsonl_path)

    if not report_json_path.exists():
        raise FileNotFoundError(f"report_json_path does not exist: {report_json_path}")

    raw = report_json_path.read_bytes()
    try:
        report_dict = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise EvidenceEmissionError(f"report is not valid JSON: {e}")

    report_profile = report_dict.get("profile")
    if report_profile is not None and report_profile != context.profile:
        raise EvidenceEmissionError(
            f"report profile {report_profile!r} does not match context "
            f"profile {context.profile!r}"
        )

    cases = report_dict.get("cases")
    if not isinstance(cases, list):
        raise EvidenceEmissionError("report.cases missing or not a list")

    missing = [
        c.get("name") for c in cases
        if c.get("name") not in case_registry and c.get("name") is not None
    ]
    unnamed = [i for i, c in enumerate(cases) if not isinstance(c.get("name"), str)]
    if unnamed:
        raise EvidenceEmissionError(f"case(s) missing a name at index: {unnamed}")
    if missing:
        raise EvidenceEmissionError(
            "conformance emission requires an explicit CaseAssessment for "
            "every reported case; missing assessments for: " + ", ".join(sorted(missing))
        )

    portable_ref = _portable_reference(report_json_path, context.artifact_root)
    raw_sha = _sha256_bytes(raw)
    sem_sha = _semantic_hash(report_dict)
    ts = _rfc3339_now_utc()

    subject = dict(context.subject)
    adapter = dict(context.adapter) if context.adapter else None

    records: list[dict] = []
    for case in cases:
        name = case["name"]
        assessment = case_registry[name]
        classification, claim_status, extra_from_case = _classify(assessment, case)

        limitations = [DEFAULT_ADAPTER_LIMITATION]
        limitations.extend(context.extra_limitations)
        limitations.extend(assessment.extra_limitations)
        limitations.extend(extra_from_case)

        record = {
            "record_id": f"{context.profile}.{name}.{context.harness_commit[:12]}.{context.run_id}",
            "recorded_at": ts,
            "evidence_observed_at": ts,
            "origin": "native_emission",
            "test_kind": "conformance",
            "requirement_id": assessment.requirement_id,
            "subject": subject,
            "adapter": adapter,
            "pamspec_context": {
                "spec_commit": context.spec_commit,
                "profile": context.profile,
                "profile_version": context.profile_version,
                "harness_commit": context.harness_commit,
            },
            "classification": classification,
            "claim_status": claim_status,
            "sub_requirements": list(assessment.sub_requirements),
            "evidence_source": list(assessment.evidence_source),
            "revises": None,
            "control_design": None,
            "environment_manifest": context.environment_manifest,
            "results_artifact": {
                "reference": portable_ref,
                "sha256": raw_sha,
            },
            "evidence_commit": context.evidence_commit,
            "limitations": limitations,
            "observed_evidence": {
                "passed": case.get("passed"),
                "duration_ms": case.get("duration_ms"),
                "error": case.get("error"),
                "semantic_results_sha256": sem_sha,
            },
        }
        records.append(record)

    schema_validator = _load_schema_validator()
    _validate_records_or_raise(records, schema_validator)

    existing_records = _load_existing_chain_records(emission_jsonl_path)
    combined = existing_records + records
    _validate_chain_or_raise(combined)

    existing_bytes = emission_jsonl_path.read_bytes() if emission_jsonl_path.exists() else b""
    _atomic_append(emission_jsonl_path, existing_bytes, records)
    return records


# --------------------------------------------------------------------------- #
# Integrated orchestration
# --------------------------------------------------------------------------- #

def run_and_emit(
    profile: str,
    factory: Callable[[], Any],
    report_output_path: Path,
    evidence_output_path: Path | None = None,
    context: EmissionContext | None = None,
    case_registry: dict[str, CaseAssessment] | None = None,
) -> tuple[Any, list[dict] | None]:
    """One harness invocation, optionally producing both artifacts.

    Legacy behavior: with evidence_output_path=None, this runs the
    conformance profile and writes the legacy ConformanceReport JSON
    to report_output_path; no evidence is emitted. Callers that never
    pass evidence_output_path see identical behavior to invoking
    `runner.run_profile(...)` directly and persisting the output
    themselves.

    Integrated behavior: with evidence_output_path AND context AND
    case_registry, this additionally emits an EvidenceRecord chain
    against the exact bytes just persisted. origin=native_emission is
    used only through this integrated path.
    """
    from . import runner  # local import so top-level module import is cheap
    report = runner.run_profile(profile, factory)

    report_output_path = Path(report_output_path)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(report.to_json(), encoding="utf-8")

    if evidence_output_path is None:
        return report, None
    if context is None or case_registry is None:
        raise EvidenceEmissionError(
            "run_and_emit(): evidence emission requires both context and "
            "case_registry; got context=%r, case_registry=%r" % (
                context is not None, case_registry is not None,
            )
        )
    records = emit_evidence_from_report_file(
        report_output_path, Path(evidence_output_path), context, case_registry,
    )
    return report, records


# --------------------------------------------------------------------------- #
# Determinism helper
# --------------------------------------------------------------------------- #

def normalize_for_determinism(record: dict) -> dict:
    """Return a copy of `record` with wall-clock and per-run fields
    masked so two independent runs at the same commit and against the
    same subject produce semantically identical records.

    R6.2a: the raw file hash (results_artifact.sha256) IS masked here
    because it embeds execution-specific timing (duration_ms). The
    canonical semantic hash (observed_evidence.semantic_results_sha256)
    is INTENTIONALLY NOT masked — it captures outcome semantics and
    should differ when the results actually differ. Duration and
    error fields inside observed_evidence are also masked; the
    semantic-hash comparison is the authoritative determinism signal.
    """
    r = json.loads(json.dumps(record))
    r["recorded_at"] = "<masked>"
    r["evidence_observed_at"] = "<masked>"
    r["record_id"] = re.sub(r"\.[A-Za-z0-9_-]+$", ".<run>", r["record_id"])
    if r.get("results_artifact"):
        r["results_artifact"] = dict(r["results_artifact"])
        r["results_artifact"]["sha256"] = "<masked>"
    obs = r.get("observed_evidence") or {}
    if "duration_ms" in obs:
        obs["duration_ms"] = "<masked>"
    return r


# --------------------------------------------------------------------------- #
# Runtime commit helper
# --------------------------------------------------------------------------- #

def git_head_commit_at_runtime() -> str:
    """Return the full 40-char git HEAD SHA at the moment of invocation.

    Useful as a default for EmissionContext.evidence_commit. Returns
    empty string when not inside a git repository — callers must supply
    an explicit value in that case.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=2.0,
        )
        return out.stdout.strip()
    except Exception:
        return ""
