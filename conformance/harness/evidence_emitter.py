"""R6.2c EvidenceRecord emission for the R7 conformance harness.

R6.2c binds native evidence to a clean, correctly-identified source
tree and to a complete runtime identity for both subprocess and
in-process adapters.

Wording note (R6.2c): the supported public API produces native
evidence only through the integrated execution path
(run_and_emit -> ExecutionSession -> _emit_native_evidence). Python
does not prevent an in-process caller from importing and calling
`_emit_native_evidence` or constructing an ExecutionSession directly;
this restriction is an API convention, not a security boundary.

Public API:
  run_and_emit(profile, factory, report_output_path,
               evidence_output_path=None, context=None,
               case_registry=None)
      One-invocation orchestration. Runs the conformance profile,
      persists the legacy report, and (when evidence parameters are
      supplied) produces an EvidenceRecord chain bound to an
      ExecutionSession captured inside this call. origin='native_emission'
      is emitted ONLY through this path.

  build_retrospective_record(...)
      Explicit constructor for R6.3 (and any post-hoc reconstruction).
      Fixes origin='retrospective_reconstruction' and
      harness_commit=None. Cannot be used to fabricate native evidence.

  CaseAssessment
      Explicit per-case metadata mapping the four structured outcomes
      (passed / assertion_failure / missing_feature / execution_error)
      to (classification, claim_status) stances. Every stance is
      required — no defaults.

  EmissionContext
      Identity + provenance + artifact_root. All commit SHAs, subject,
      and artifact_root validated at construction.

R6.2b hard rules:
  - runner.py legacy JSON shape unchanged (outcome_kind is a
    non-serialized CaseResult field consumed via ExecutionSession)
  - default runner behavior unchanged when evidence_output_path is None
  - execution provenance binding: report.suite_commit MUST equal
    context.evidence_commit AND context.harness_commit
  - profile identity: report.profile MUST be present and equal to
    context.profile
  - adapter identity: context.adapter.name MUST equal
    report.adapter_class (or, for subprocess adapters, the reported
    adapter_name)
  - subject identity: for subprocess adapters, the reported
    implementation_name/version MUST equal context.subject.name/version
  - environment_manifest, when non-null, MUST reference a file under
    artifact_root whose actual sha256 matches the declared value
  - existing chain records are schema-validated AND chain-validated
    together with new records before any write
  - concurrent writers acquire an exclusive lock file (O_CREAT|O_EXCL);
    lost updates are impossible
  - atomic append: temp file + fsync + os.replace; failures leave the
    original chain byte-identical
  - evidence_observed_at = report.finished_at (validated strict RFC 3339);
    recorded_at = emission time
  - semantic_results_sha256 is computed from a projection that uses
    outcome_kind (not raw error text) so dynamic tracebacks do not
    change the semantic hash
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
from typing import Any, Callable

from jsonschema import Draft202012Validator


SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "conformance" / "schemas" / "0.1-draft" / "evidence-record.schema.json"

DEFAULT_ADAPTER_LIMITATION = (
    "evidence_source only includes 'adapter'; no independent probe of "
    "the subject was performed as part of this conformance run"
)

STRUCTURED_OUTCOMES = ("passed", "assertion_failure", "missing_feature", "execution_error")
VALID_CLASSIFICATIONS = {"native", "emulated", "gap", "questionable", "not_testable"}
VALID_CLAIM_STATUSES = {"confirmed", "inconclusive", "not_testable"}


class EvidenceEmissionError(ValueError):
    """Raised when an evidence emission is rejected before any write."""


# --------------------------------------------------------------------------- #
# Case assessment
# --------------------------------------------------------------------------- #

@dataclass
class CaseAssessment:
    """Explicit per-case stance keyed by STRUCTURED outcome_kind.

    Every one of the four structured outcome kinds MUST have a
    classification and a claim_status specified. No defaults; construction
    raises TypeError if any is omitted, and ValueError if any is not a
    valid R6.1c enum value.
    """
    requirement_id: str
    on_passed_classification: str
    on_passed_claim_status: str
    on_assertion_failure_classification: str
    on_assertion_failure_claim_status: str
    on_missing_feature_classification: str
    on_missing_feature_claim_status: str
    on_execution_error_classification: str
    on_execution_error_claim_status: str
    sub_requirements: list[dict] = field(default_factory=list)
    evidence_source: list[str] = field(default_factory=lambda: ["adapter"])
    extra_limitations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.requirement_id or not isinstance(self.requirement_id, str):
            raise ValueError("CaseAssessment.requirement_id MUST be a non-empty string")
        if not self.evidence_source:
            raise ValueError("CaseAssessment.evidence_source MUST be non-empty")
        for k, v in [
            ("on_passed_classification", self.on_passed_classification),
            ("on_assertion_failure_classification", self.on_assertion_failure_classification),
            ("on_missing_feature_classification", self.on_missing_feature_classification),
            ("on_execution_error_classification", self.on_execution_error_classification),
        ]:
            if v not in VALID_CLASSIFICATIONS:
                raise ValueError(f"{k} must be one of {sorted(VALID_CLASSIFICATIONS)}: got {v!r}")
        for k, v in [
            ("on_passed_claim_status", self.on_passed_claim_status),
            ("on_assertion_failure_claim_status", self.on_assertion_failure_claim_status),
            ("on_missing_feature_claim_status", self.on_missing_feature_claim_status),
            ("on_execution_error_claim_status", self.on_execution_error_claim_status),
        ]:
            if v not in VALID_CLAIM_STATUSES:
                raise ValueError(f"{k} must be one of {sorted(VALID_CLAIM_STATUSES)}: got {v!r}")

    def action_for(self, outcome_kind: str) -> tuple[str, str]:
        mapping = {
            "passed": (self.on_passed_classification, self.on_passed_claim_status),
            "assertion_failure": (self.on_assertion_failure_classification, self.on_assertion_failure_claim_status),
            "missing_feature": (self.on_missing_feature_classification, self.on_missing_feature_claim_status),
            "execution_error": (self.on_execution_error_classification, self.on_execution_error_claim_status),
        }
        if outcome_kind not in mapping:
            raise EvidenceEmissionError(f"unknown outcome_kind: {outcome_kind!r}")
        return mapping[outcome_kind]


# --------------------------------------------------------------------------- #
# Emission context
# --------------------------------------------------------------------------- #

@dataclass
class EmissionContext:
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
                raise ValueError(f"{name} MUST be a 40-char lowercase hex SHA: {v!r}")
        for name in ("profile", "profile_version"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{name} MUST be a non-empty string")
        if not isinstance(self.artifact_root, Path):
            self.artifact_root = Path(self.artifact_root)
        self.artifact_root = self.artifact_root.resolve()
        if not self.artifact_root.exists() or not self.artifact_root.is_dir():
            raise ValueError(f"artifact_root must be an existing directory: {self.artifact_root}")
        _validate_subject(self.subject)
        if self.adapter is not None:
            _validate_adapter(self.adapter)
        if self.environment_manifest is not None:
            _validate_environment_manifest_syntax(self.environment_manifest)
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


def _validate_environment_manifest_syntax(m: dict[str, Any]) -> None:
    if not isinstance(m, dict):
        raise ValueError("environment_manifest MUST be an object")
    if "reference" not in m or not isinstance(m["reference"], str) or not m["reference"]:
        raise ValueError("environment_manifest.reference MUST be a non-empty string")
    if "sha256" not in m:
        raise ValueError("environment_manifest.sha256 MUST be present")
    sha = m["sha256"]
    if not isinstance(sha, str) or not SHA64_RE.match(sha):
        raise ValueError("environment_manifest.sha256 MUST be a 64-char hex string (non-null for native emission)")


# --------------------------------------------------------------------------- #
# Execution session (created only by run_and_emit)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ExecutionSession:
    """Captured provenance for one harness invocation.

    Constructed by run_and_emit(). Passed to _emit_native_evidence().
    Public constructor exists (Python cannot prevent import), but the
    supported public API for native emission is run_and_emit only.

    R6.2c: source_state carries the repository provenance
    (`{head, clean, modified_files}`) captured at run time. The
    emitter refuses native emission when the source is dirty in the
    files that shape evidence semantics.
    """
    report_dict: dict
    report_bytes: bytes
    report_path: Path
    report_sha256: str
    outcome_kinds: dict[str, str]
    suite_commit: str
    adapter_class: str
    adapter_info: dict
    profile: str
    started_at: str
    finished_at: str
    source_state: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def _validate_rfc3339(ts: str, label: str) -> None:
    if not isinstance(ts, str) or not RFC3339_RE.match(ts):
        raise EvidenceEmissionError(
            f"{label} is not a valid strict RFC 3339 date-time: {ts!r}"
        )
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError as e:
        raise EvidenceEmissionError(f"{label} has invalid calendar values: {ts!r} ({e})")


def _rfc3339_now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _portable_reference(target: Path, artifact_root: Path) -> str:
    target = Path(target).resolve()
    try:
        rel = target.relative_to(artifact_root)
    except ValueError:
        raise EvidenceEmissionError(
            f"artifact reference {target} is not under artifact_root "
            f"{artifact_root}"
        )
    posix = rel.as_posix()
    if posix.startswith("/") or posix.startswith("../") or ".." in posix.split("/"):
        raise EvidenceEmissionError(f"artifact reference contains traversal: {posix!r}")
    if any(comp == "" for comp in posix.split("/")):
        raise EvidenceEmissionError(f"artifact reference contains empty component: {posix!r}")
    return posix


def _verify_environment_manifest(manifest: dict, artifact_root: Path) -> None:
    """Full runtime verification: reference must resolve under
    artifact_root, the file must exist, and its actual sha256 must
    equal the declared value."""
    ref = manifest["reference"]
    if os.path.isabs(ref):
        raise EvidenceEmissionError(f"environment_manifest.reference must be relative: {ref!r}")
    if ".." in Path(ref).parts:
        raise EvidenceEmissionError(f"environment_manifest.reference contains traversal: {ref!r}")
    p = (artifact_root / ref).resolve()
    try:
        p.relative_to(artifact_root)
    except ValueError:
        raise EvidenceEmissionError(
            f"environment_manifest.reference resolves outside artifact_root: {ref!r}"
        )
    if not p.exists():
        raise EvidenceEmissionError(f"environment_manifest file does not exist: {p}")
    actual = _sha256_bytes(p.read_bytes())
    if actual != manifest["sha256"]:
        raise EvidenceEmissionError(
            f"environment_manifest.sha256 mismatch for {ref!r}: "
            f"declared {manifest['sha256']}, actual {actual}"
        )


def _canonical_semantic_projection(session: ExecutionSession) -> dict:
    """Semantic projection independent of wall-clock and error-text
    noise. Uses structured outcome_kind rather than the raw error
    string so dynamic tracebacks do not change the semantic hash."""
    d = session.report_dict
    cases = []
    for c in d.get("cases", []):
        name = c.get("name")
        cases.append({
            "name": name,
            "passed": c.get("passed"),
            "outcome_kind": session.outcome_kinds.get(name, "unknown"),
        })
    ai = d.get("adapter_info") or {}
    sub = ai.get("subprocess") if isinstance(ai, dict) else None
    return {
        "profile": d.get("profile"),
        "adapter_class": d.get("adapter_class"),
        "totals": d.get("totals"),
        "cases": cases,
        "adapter_identity": {
            "adapter_name": (sub or {}).get("adapter_name") if isinstance(sub, dict) else None,
            "adapter_version": (sub or {}).get("adapter_version") if isinstance(sub, dict) else None,
            "implementation_name": (sub or {}).get("implementation_name") if isinstance(sub, dict) else None,
            "implementation_version": (sub or {}).get("implementation_version") if isinstance(sub, dict) else None,
            "spec_commit": (sub or {}).get("spec_commit") if isinstance(sub, dict) else None,
            "protocol_version": (sub or {}).get("protocol_version") if isinstance(sub, dict) else None,
        },
    }


def _semantic_hash_from_session(session: ExecutionSession) -> str:
    return _sha256_bytes(
        json.dumps(_canonical_semantic_projection(session), sort_keys=True).encode("utf-8")
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
            raise EvidenceEmissionError(f"existing chain {chain_path}:{lineno} not valid JSON: {e}")
    return records


def _load_schema_validator() -> Draft202012Validator:
    import importlib.util
    validate_evidence_path = ROOT / "scripts" / "validate_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_evidence", validate_evidence_path)
    ve = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(ve)  # type: ignore
    return ve.make_validator()


def _validate_records_or_raise(records: list[dict], schema_validator: Draft202012Validator, label: str) -> None:
    for rec in records:
        errs = list(schema_validator.iter_errors(rec))
        if errs:
            details = "; ".join(f"{list(e.absolute_path)}: {e.message}" for e in errs)
            raise EvidenceEmissionError(
                f"{label} record {rec.get('record_id', '<unknown>')} fails schema: {details}"
            )


def _validate_chain_or_raise(records: list[dict]) -> None:
    import importlib.util
    validate_evidence_path = ROOT / "scripts" / "validate_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_evidence", validate_evidence_path)
    ve = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(ve)  # type: ignore
    errs = ve.validate_records(records)
    if errs:
        raise EvidenceEmissionError("chain-level invariant violations: " + "; ".join(errs))


class _EmissionLock:
    """Advisory exclusive file lock via O_CREAT|O_EXCL. Concurrent
    writers race to create the lock; the loser gets an
    EvidenceEmissionError. Lock is released on __exit__ regardless of
    exception. Do NOT silently remove based on age — a stale lock is
    a signal a previous writer crashed and must be investigated.
    """
    def __init__(self, chain_path: Path):
        self.chain_path = chain_path
        self.lock_path = chain_path.parent / (chain_path.name + ".lock")
        self.fd: int | None = None

    def __enter__(self) -> "_EmissionLock":
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            raise EvidenceEmissionError(
                f"another writer holds the evidence-chain lock at {self.lock_path}; "
                f"if you know no other writer is running, inspect and remove it manually"
            )
        try:
            os.write(self.fd, f"pid={os.getpid()}\ntime={_rfc3339_now_utc()}\n".encode())
        except OSError:
            pass
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
        try:
            os.unlink(self.lock_path)
        except OSError:
            pass


def _atomic_write(chain_path: Path, existing_bytes: bytes, new_records: list[dict]) -> None:
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
                pass
        os.replace(tmp_name, chain_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# Provenance binding
# --------------------------------------------------------------------------- #

def _bind_context_to_session(session: ExecutionSession, context: EmissionContext) -> None:
    """Fail-closed provenance checks. Every check raises
    EvidenceEmissionError BEFORE any write occurs.

    R6.2c additions:
      * spec_commit is now bound: context.spec_commit MUST equal
        context.harness_commit MUST equal context.evidence_commit
        MUST equal report.suite_commit. All four are the same repo
        revision because the spec, schema, harness, and requirement
        registry all live at that single SHA.
      * subprocess-reported spec_commit (if present) MUST equal
        context.spec_commit.
      * In-process adapters MUST supply structured evidence_identity;
        the emitter binds subject.name/version and adapter.name/version
        against it. If neither subprocess metadata NOR
        evidence_identity is available, native emission is refused.
      * Source state MUST be clean: the emitter refuses when any
        native-source path (see NATIVE_SOURCE_PATHS in
        capture_source_state) is dirty.
    """
    if not session.profile:
        raise EvidenceEmissionError("report.profile is missing")
    if session.profile != context.profile:
        raise EvidenceEmissionError(
            f"report.profile ({session.profile!r}) != context.profile ({context.profile!r})"
        )
    # Commit binding: all three context commits MUST equal report.suite_commit.
    if session.suite_commit != context.harness_commit:
        raise EvidenceEmissionError(
            f"context.harness_commit ({context.harness_commit}) does not match "
            f"report.suite_commit ({session.suite_commit!r})"
        )
    if session.suite_commit != context.evidence_commit:
        raise EvidenceEmissionError(
            f"context.evidence_commit ({context.evidence_commit}) does not match "
            f"report.suite_commit ({session.suite_commit!r})"
        )
    if session.suite_commit != context.spec_commit:
        raise EvidenceEmissionError(
            f"context.spec_commit ({context.spec_commit}) does not match "
            f"report.suite_commit ({session.suite_commit!r}); PAMSPEC spec, "
            f"harness, and requirement registry currently live at one repo "
            f"revision"
        )
    ai = session.adapter_info or {}
    sub = ai.get("subprocess") if isinstance(ai, dict) else None
    identity = ai.get("evidence_identity") if isinstance(ai, dict) else None
    # Subprocess-reported spec_commit binding
    if isinstance(sub, dict) and sub.get("spec_commit"):
        if sub["spec_commit"] != context.spec_commit:
            raise EvidenceEmissionError(
                f"subprocess-reported spec_commit ({sub['spec_commit']!r}) does not "
                f"match context.spec_commit ({context.spec_commit!r})"
            )
    # Identity binding — subprocess OR evidence_identity is REQUIRED
    if context.adapter is not None:
        if isinstance(sub, dict) and sub.get("adapter_name"):
            reported_adapter_name = sub["adapter_name"]
            reported_adapter_version = sub.get("adapter_version")
        elif isinstance(identity, dict) and identity.get("adapter_name"):
            reported_adapter_name = identity["adapter_name"]
            reported_adapter_version = identity.get("adapter_version")
        else:
            raise EvidenceEmissionError(
                "native emission requires either subprocess-reported adapter "
                "identity or an in-process adapter with evidence_identity() "
                "returning adapter_name/adapter_version — got neither"
            )
        if reported_adapter_name != context.adapter["name"]:
            raise EvidenceEmissionError(
                f"context.adapter.name ({context.adapter['name']!r}) does not match "
                f"reported adapter identity ({reported_adapter_name!r})"
            )
        if reported_adapter_version and reported_adapter_version != context.adapter["version"]:
            raise EvidenceEmissionError(
                f"context.adapter.version ({context.adapter['version']!r}) does not "
                f"match reported adapter_version ({reported_adapter_version!r})"
            )
    # Subject identity binding — subprocess OR evidence_identity is REQUIRED
    if isinstance(sub, dict) and sub.get("implementation_name"):
        impl_name = sub["implementation_name"]
        impl_version = sub.get("implementation_version")
    elif isinstance(identity, dict) and identity.get("implementation_name"):
        impl_name = identity["implementation_name"]
        impl_version = identity.get("implementation_version")
    else:
        raise EvidenceEmissionError(
            "native emission requires either subprocess-reported implementation "
            "identity or an in-process adapter with evidence_identity() returning "
            "implementation_name/implementation_version — got neither"
        )
    if context.subject.get("name") != impl_name:
        raise EvidenceEmissionError(
            f"context.subject.name ({context.subject['name']!r}) does not match "
            f"reported implementation_name ({impl_name!r})"
        )
    if impl_version and context.subject.get("version") != impl_version:
        raise EvidenceEmissionError(
            f"context.subject.version ({context.subject['version']!r}) does not match "
            f"reported implementation_version ({impl_version!r})"
        )
    # Environment manifest bytes verification
    if context.environment_manifest is not None:
        _verify_environment_manifest(context.environment_manifest, context.artifact_root)
    # Report finished_at is strict RFC 3339 (evidence_observed_at derives from it)
    _validate_rfc3339(session.finished_at, "report.finished_at")
    # Source-state binding: refuse dirty native-source paths
    ss = session.source_state or {}
    if not ss.get("clean", False):
        modified = ss.get("modified_files") or ["<unknown>"]
        raise EvidenceEmissionError(
            "native emission refused: PAMSPEC source tree is not clean in "
            "native-source paths (%s). Commit or stash changes before emitting "
            "native evidence. Modified: %s" % (
                ", ".join(NATIVE_SOURCE_PATHS),
                "; ".join(modified[:10]),
            )
        )


# --------------------------------------------------------------------------- #
# Native emission (internal; requires ExecutionSession)
# --------------------------------------------------------------------------- #

def _emit_native_evidence(
    session: ExecutionSession,
    emission_jsonl_path: Path,
    context: EmissionContext,
    case_registry: dict[str, CaseAssessment],
) -> list[dict]:
    """Emit native EvidenceRecords bound to an ExecutionSession that
    only run_and_emit() constructs. Not callable from tests or external
    scripts without a session — origin='native_emission' cannot escape
    the integrated path.

    Fail-closed on: unregistered case, profile mismatch, commit
    mismatch, adapter identity mismatch, subject identity mismatch
    (subprocess only), env-manifest bytes mismatch, schema failure on
    proposed OR existing records, chain invariant failure, lock
    contention, atomic-write failure.
    """
    emission_jsonl_path = Path(emission_jsonl_path)

    # Provenance binding first (before anything is built)
    _bind_context_to_session(session, context)

    cases = session.report_dict.get("cases")
    if not isinstance(cases, list):
        raise EvidenceEmissionError("report.cases missing or not a list")

    unnamed = [i for i, c in enumerate(cases) if not isinstance(c.get("name"), str)]
    if unnamed:
        raise EvidenceEmissionError(f"case(s) missing a name at index: {unnamed}")
    missing = sorted({c["name"] for c in cases if c["name"] not in case_registry})
    if missing:
        raise EvidenceEmissionError(
            "conformance emission requires an explicit CaseAssessment for every "
            "reported case; missing assessments for: " + ", ".join(missing)
        )

    portable_ref = _portable_reference(session.report_path, context.artifact_root)
    sem_sha = _semantic_hash_from_session(session)
    now_ts = _rfc3339_now_utc()
    evidence_observed_at = session.finished_at

    subject = dict(context.subject)
    adapter = dict(context.adapter) if context.adapter else None

    records: list[dict] = []
    for case in cases:
        name = case["name"]
        assessment = case_registry[name]
        outcome_kind = session.outcome_kinds.get(name, "execution_error")
        classification, claim_status = assessment.action_for(outcome_kind)

        limitations = [DEFAULT_ADAPTER_LIMITATION]
        limitations.extend(context.extra_limitations)
        limitations.extend(assessment.extra_limitations)
        if outcome_kind == "missing_feature":
            limitations.append(f"structured outcome: {outcome_kind}")
        elif outcome_kind in ("assertion_failure", "execution_error"):
            limitations.append(f"structured outcome: {outcome_kind}")

        record = {
            "record_id": f"{context.profile}.{name}.{context.harness_commit[:12]}.{context.run_id}",
            "recorded_at": now_ts,
            "evidence_observed_at": evidence_observed_at,
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
                "sha256": session.report_sha256,
            },
            "evidence_commit": context.evidence_commit,
            "limitations": limitations,
            "observed_evidence": {
                "passed": case.get("passed"),
                "duration_ms": case.get("duration_ms"),
                "outcome_kind": outcome_kind,
                "failure_code": FAILURE_CODES.get(outcome_kind),
                "error_summary": _error_summary(outcome_kind, case.get("error")),
                "semantic_results_sha256": sem_sha,
            },
        }
        records.append(record)

    # Preflight: schema-validate proposed AND existing, then chain-validate combined
    schema_validator = _load_schema_validator()
    _validate_records_or_raise(records, schema_validator, "proposed")

    with _EmissionLock(emission_jsonl_path):
        existing_records = _load_existing_chain_records(emission_jsonl_path)
        _validate_records_or_raise(existing_records, schema_validator, "existing")
        combined = existing_records + records
        _validate_chain_or_raise(combined)
        existing_bytes = emission_jsonl_path.read_bytes() if emission_jsonl_path.exists() else b""
        _atomic_write(emission_jsonl_path, existing_bytes, records)

    return records


# --------------------------------------------------------------------------- #
# Retrospective constructor (R6.3 preview; not native)
# --------------------------------------------------------------------------- #

def build_retrospective_record(
    *,
    record_id: str,
    evidence_observed_at: str,
    test_kind: str,
    requirement_id: str,
    subject: dict[str, str],
    adapter: dict[str, str] | None,
    spec_commit: str,
    profile: str | None,
    profile_version: str | None,
    classification: str,
    claim_status: str,
    evidence_commit: str,
    evidence_source: list[str],
    limitations: list[str],
    observed_evidence: dict,
    control_design: dict | None = None,
    environment_manifest: dict | None = None,
    results_artifact: dict | None = None,
    sub_requirements: list[dict] | None = None,
    revises: dict | None = None,
    conclusion_narrative: str | None = None,
) -> dict:
    """Explicit constructor for origin='retrospective_reconstruction'
    records. harness_commit is FORCED to null (a retrospective record
    cannot falsely attribute its evidence to an R7 harness run).

    This function cannot produce a native record. Native emission is
    only available through run_and_emit()."""
    if not SHA40_RE.match(spec_commit):
        raise ValueError(f"spec_commit MUST be a 40-char hex SHA: {spec_commit!r}")
    if not SHA40_RE.match(evidence_commit):
        raise ValueError(f"evidence_commit MUST be a 40-char hex SHA: {evidence_commit!r}")
    _validate_rfc3339(evidence_observed_at, "evidence_observed_at")
    if classification not in VALID_CLASSIFICATIONS:
        raise ValueError(f"classification invalid: {classification!r}")
    if claim_status not in VALID_CLAIM_STATUSES:
        raise ValueError(f"claim_status invalid: {claim_status!r}")
    rec = {
        "record_id": record_id,
        "recorded_at": _rfc3339_now_utc(),
        "evidence_observed_at": evidence_observed_at,
        "origin": "retrospective_reconstruction",
        "test_kind": test_kind,
        "requirement_id": requirement_id,
        "subject": subject,
        "adapter": adapter,
        "pamspec_context": {
            "spec_commit": spec_commit,
            "profile": profile,
            "profile_version": profile_version,
            "harness_commit": None,
        },
        "classification": classification,
        "claim_status": claim_status,
        "sub_requirements": list(sub_requirements or []),
        "evidence_source": list(evidence_source),
        "revises": revises,
        "control_design": control_design,
        "environment_manifest": environment_manifest,
        "results_artifact": results_artifact,
        "evidence_commit": evidence_commit,
        "limitations": list(limitations),
        "observed_evidence": dict(observed_evidence),
    }
    if conclusion_narrative is not None:
        rec["conclusion_narrative"] = conclusion_narrative
    return rec


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
    source_state: dict | None = None,
) -> tuple[Any, list[dict] | None]:
    """One harness invocation, optionally producing both artifacts.

    Legacy behavior: with evidence_output_path=None this function only
    runs the profile and writes the legacy report.

    Integrated behavior: with evidence_output_path AND context AND
    case_registry, this constructs an ExecutionSession bound to this
    invocation and emits native evidence through the internal
    _emit_native_evidence(). origin='native_emission' is only produced
    via this path.

    source_state:
      When None (default), the emitter captures the PAMSPEC repository
      state via capture_source_state(REPO_ROOT). The bind step then
      refuses native emission if native-source paths are dirty.
      Tests may pass a dict here to inject a specific state without
      depending on the actual worktree.
    """
    from . import runner
    report = runner.run_profile(profile, factory)

    report_output_path = Path(report_output_path)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(report.to_json(), encoding="utf-8")

    if evidence_output_path is None:
        return report, None
    if context is None or case_registry is None:
        raise EvidenceEmissionError(
            "run_and_emit(): evidence emission requires both context and "
            "case_registry"
        )

    report_bytes = report_output_path.read_bytes()
    session = ExecutionSession(
        report_dict=report.to_dict(),
        report_bytes=report_bytes,
        report_path=report_output_path,
        report_sha256=_sha256_bytes(report_bytes),
        outcome_kinds={c.name: c.outcome_kind for c in report.cases},
        suite_commit=report.suite_commit,
        adapter_class=report.adapter_class,
        adapter_info=report.adapter_info or {},
        profile=report.profile,
        started_at=report.started_at,
        finished_at=report.finished_at,
        source_state=source_state if source_state is not None else capture_source_state(ROOT),
    )
    records = _emit_native_evidence(session, Path(evidence_output_path), context, case_registry)
    return report, records


# --------------------------------------------------------------------------- #
# Determinism helper
# --------------------------------------------------------------------------- #

def normalize_for_determinism(record: dict) -> dict:
    """Mask wall-clock and per-run fields for cross-run comparison.
    The semantic_results_sha256 field is intentionally NOT masked; it
    IS the deterministic signal."""
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
    """Return the current git HEAD SHA of the PAMSPEC repository (not
    the process cwd). R6.2c always runs against REPO_ROOT."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=2.0,
            cwd=str(ROOT),
        )
        return out.stdout.strip()
    except Exception:
        return ""


# --------------------------------------------------------------------------- #
# R6.2c: source-state capture and clean-source binding
# --------------------------------------------------------------------------- #

# Tracked paths whose dirty state MUST reject native evidence emission.
# Anything that changes the semantics of what evidence claims lives here.
NATIVE_SOURCE_PATHS = (
    "conformance",
    "scripts/validate_evidence.py",
)


def capture_source_state(repo_root: Path = ROOT) -> dict:
    """Snapshot the PAMSPEC repository state at capture time.

    Returns {head, clean, modified_files}. `clean` is True only when
    every tracked path in NATIVE_SOURCE_PATHS is clean; other paths
    (unrelated test artifacts, generated reports) are ignored so a
    fresh evidence JSONL does not itself mark the tree dirty.
    """
    head = ""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=2.0,
            cwd=str(repo_root),
        ).stdout.strip()
    except Exception:
        return {"head": "", "clean": False, "modified_files": ["<git rev-parse failed>"]}

    modified: list[str] = []
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--", *NATIVE_SOURCE_PATHS],
            capture_output=True, text=True, check=True, timeout=5.0,
            cwd=str(repo_root),
        )
        for line in result.stdout.splitlines():
            line = line.rstrip("\r")
            if line.strip():
                modified.append(line)
    except Exception as e:
        return {"head": head, "clean": False, "modified_files": [f"<git status failed: {e}>"]}

    return {"head": head, "clean": len(modified) == 0, "modified_files": modified}


# --------------------------------------------------------------------------- #
# R6.2c: error-summary redaction (traceback disclosure control)
# --------------------------------------------------------------------------- #

FAILURE_CODES = {
    "passed": None,
    "assertion_failure": "ASSERTION_FAILURE",
    "missing_feature": "MISSING_FEATURE",
    "execution_error": "HARNESS_EXECUTION_ERROR",
}


def _redact_paths(s: str) -> str:
    """Replace absolute paths with a stable placeholder so evidence
    records do not leak workstation directory layouts.

    Handles the common shapes:
      - Windows drive-letter paths: C:\\Users\\..., D:/Users/...
      - POSIX absolute paths: /tmp/..., /home/...
    """
    s = re.sub(r"[A-Za-z]:[\\/][^\s\)\"'<>]+", "<redacted-path>", s)
    s = re.sub(r"(?<![A-Za-z0-9_])/(?:[^\s\)\"'<>/]+/)+[^\s\)\"'<>]*", "<redacted-path>", s)
    return s


def _error_summary(outcome_kind: str, raw_error: str | None, max_len: int = 200) -> str | None:
    """Produce a short, path-redacted summary suitable for embedding
    in the EvidenceRecord. The full raw error remains available
    through the pinned results_artifact."""
    if not raw_error:
        return None
    if outcome_kind == "execution_error":
        # Never inline traceback text; the pinned result artifact has it.
        return "Runtime execution failed; inspect the pinned result artifact."
    if outcome_kind == "missing_feature":
        prefix = "adapter missing feature:"
        core = raw_error[len(prefix):].strip() if raw_error.startswith(prefix) else raw_error
        return _redact_paths(core)[:max_len]
    if outcome_kind == "assertion_failure":
        prefix = "assertion failed:"
        core = raw_error[len(prefix):].strip() if raw_error.startswith(prefix) else raw_error
        return _redact_paths(core)[:max_len]
    return _redact_paths(raw_error)[:max_len]
