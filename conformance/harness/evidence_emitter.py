"""R6.2 EvidenceRecord emission for the R7 conformance harness.

Emits one EvidenceRecord per suite case in a ConformanceReport, appending
to a caller-specified JSONL file. Each emitted record conforms to
`conformance/schemas/0.1-draft/evidence-record.schema.json` (R6.1c) and
uses:

  origin           = native_emission
  test_kind        = conformance
  evidence_source  includes "adapter"
  claim_status     in {confirmed, not_testable}

The legacy `ConformanceReport.to_json()` output is NOT modified in any
way by this module. The runner is not modified either. Callers persist
the legacy report, then invoke `emit_evidence_from_report(...)` to
produce a companion EvidenceRecord chain that references the legacy
report by (path, sha256).

Fail-closed: bad SHAs, missing profile, missing report file, or a
subject that cannot be identified all raise `ValueError` (or
`FileNotFoundError`) before any record is written.

R6.2 scope constraints observed:
  - does not replace or alter the legacy ConformanceReport
  - does not change test execution or pass/fail decisions
  - does not change adapter behavior
  - does not touch the Internet-Draft, memory schemas, MCP binding,
    or reference implementation
  - the harness itself is unchanged; this module is standalone
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

DEFAULT_ADAPTER_LIMITATION = (
    "evidence_source only includes 'adapter'; no independent probe of "
    "the subject was performed as part of this conformance run"
)


@dataclass
class EmissionContext:
    """Everything the emitter needs to produce records that satisfy the
    R6.1c schema and chain-level invariants.

    All commit SHAs MUST be full 40-character git hashes. Failure to
    supply valid values raises ValueError at construction time.
    """
    spec_commit: str
    harness_commit: str
    profile: str
    profile_version: str
    subject: dict[str, str] | None = None
    adapter: dict[str, str] | None = None
    environment_manifest: dict[str, Any] | None = None
    requirement_id_prefix: str | None = None
    extra_limitations: list[str] = field(default_factory=list)
    run_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.spec_commit, str) or not SHA40_RE.match(self.spec_commit):
            raise ValueError(
                f"spec_commit MUST be a 40-char lowercase hex SHA: {self.spec_commit!r}"
            )
        if not isinstance(self.harness_commit, str) or not SHA40_RE.match(self.harness_commit):
            raise ValueError(
                f"harness_commit MUST be a 40-char lowercase hex SHA: {self.harness_commit!r}"
            )
        if not isinstance(self.profile, str) or not self.profile:
            raise ValueError("profile MUST be a non-empty string")
        if not isinstance(self.profile_version, str) or not self.profile_version:
            raise ValueError("profile_version MUST be a non-empty string")
        if self.subject is not None:
            _validate_subject(self.subject)
        if self.adapter is not None:
            _validate_adapter(self.adapter)
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


def _rfc3339_now_utc() -> str:
    """Strict RFC 3339 with 'Z' zulu form, matching the harness's own
    _iso_utc_now() choice. Passes the R6.1c strict validator."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _classify(case: dict) -> tuple[str, str, list[str]]:
    """Map a legacy case result to (classification, claim_status, extra_limitations).

    Rules (see EmissionContext limitations note): a passing case against a
    subject we control (reference implementation) is 'native' + 'confirmed'.
    A failing case is 'gap' + 'confirmed'. An "adapter missing feature"
    error is 'not_testable' + 'not_testable'.

    For adapters wrapping frameworks whose native behavior is unknown,
    'native' is a misclassification without a separate probe record —
    callers testing such subjects should NOT use this emitter unmodified;
    they should override classification per case (a future R6.2.x extension).
    """
    error = case.get("error")
    passed = case.get("passed")
    if error and "adapter missing feature" in str(error):
        return ("not_testable", "not_testable", [f"adapter missing feature: {error}"])
    if passed is True:
        return ("native", "confirmed", [])
    if passed is False:
        return ("gap", "confirmed", [f"case failed: {error}" if error else "case failed"])
    return (
        "questionable",
        "inconclusive",
        [f"unexpected case state: passed={passed!r}, error={error!r}"],
    )


def _derive_subject(adapter_info: dict) -> dict[str, str]:
    """Fallback subject derivation when the caller does not provide one.

    Prefers subprocess-reported implementation identity (from R7 hello).
    For in-process adapters without that info, raises ValueError so the
    caller supplies an explicit subject rather than letting an
    unidentified emission escape.
    """
    sub = adapter_info.get("subprocess") if adapter_info else None
    if isinstance(sub, dict):
        impl_name = sub.get("implementation_name")
        impl_ver = sub.get("implementation_version")
        if impl_name and impl_ver:
            return {"kind": "implementation", "name": impl_name, "version": impl_ver}
    raise ValueError(
        "cannot derive subject from adapter_info; supply EmissionContext.subject "
        "for in-process adapters that do not self-report an implementation identity"
    )


def _derive_adapter(adapter_info: dict) -> dict[str, str]:
    """Fallback adapter derivation. Prefers subprocess-reported values;
    otherwise uses the class_name and 'unknown' version."""
    sub = adapter_info.get("subprocess") if adapter_info else None
    if isinstance(sub, dict):
        name = sub.get("adapter_name")
        version = sub.get("adapter_version")
        if name and version:
            return {"name": name, "version": version}
    class_name = adapter_info.get("class_name") if adapter_info else None
    if not class_name:
        raise ValueError("cannot derive adapter from adapter_info")
    return {"name": class_name, "version": "unknown"}


def _case_name_short(name: str) -> str:
    return name.removeprefix("case_")


def emit_evidence_from_report(
    report_dict: dict,
    report_json_path: Path,
    emission_jsonl_path: Path,
    context: EmissionContext,
) -> list[dict]:
    """Build one EvidenceRecord per suite case in `report_dict`, append
    them to `emission_jsonl_path` as JSONL, and return the list.

    - `report_dict` is the ConformanceReport.to_dict() shape.
    - `report_json_path` is the file where the legacy report is persisted.
      The file MUST exist so its sha256 can pin `results_artifact.sha256`.
    - `emission_jsonl_path` receives newly appended records; earlier lines
      are never touched (per R6.1c invariant 7).
    """
    if not isinstance(report_dict, dict):
        raise ValueError("report_dict must be a dict (ConformanceReport.to_dict())")
    if "cases" not in report_dict or not isinstance(report_dict["cases"], list):
        raise ValueError("report_dict.cases missing or not a list")
    report_json_path = Path(report_json_path)
    if not report_json_path.exists():
        raise FileNotFoundError(f"report_json_path does not exist: {report_json_path}")
    emission_jsonl_path = Path(emission_jsonl_path)

    report_sha256 = _sha256_file(report_json_path)
    adapter_info = report_dict.get("adapter_info") or {}
    subject = context.subject or _derive_subject(adapter_info)
    adapter = context.adapter or _derive_adapter(adapter_info)
    _validate_subject(subject)
    _validate_adapter(adapter)

    profile = report_dict.get("profile") or context.profile
    prefix = context.requirement_id_prefix or f"PAMSPEC.{profile}"
    ts = _rfc3339_now_utc()

    records: list[dict] = []
    for case in report_dict["cases"]:
        name = case.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"case missing 'name': {case!r}")
        case_short = _case_name_short(name)
        requirement_id = f"{prefix}.{case_short}"

        classification, claim_status, extra_from_case = _classify(case)

        limitations = [DEFAULT_ADAPTER_LIMITATION]
        limitations.extend(context.extra_limitations)
        limitations.extend(extra_from_case)

        record = {
            "record_id": f"{profile}.{case_short}.{context.harness_commit[:12]}.{context.run_id}",
            "recorded_at": ts,
            "evidence_observed_at": ts,
            "origin": "native_emission",
            "test_kind": "conformance",
            "requirement_id": requirement_id,
            "subject": dict(subject),
            "adapter": dict(adapter),
            "pamspec_context": {
                "spec_commit": context.spec_commit,
                "profile": context.profile,
                "profile_version": context.profile_version,
                "harness_commit": context.harness_commit,
            },
            "classification": classification,
            "claim_status": claim_status,
            "sub_requirements": [],
            "evidence_source": ["adapter"],
            "revises": None,
            "control_design": None,
            "environment_manifest": context.environment_manifest,
            "results_artifact": {
                "reference": report_json_path.as_posix(),
                "sha256": report_sha256,
            },
            "evidence_commit": context.harness_commit,
            "limitations": limitations,
            "observed_evidence": {
                "passed": case.get("passed"),
                "duration_ms": case.get("duration_ms"),
                "error": case.get("error"),
            },
        }
        records.append(record)

    emission_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with emission_jsonl_path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    return records


def normalize_for_determinism(record: dict) -> dict:
    """Return a copy of `record` with wall-clock and per-run fields
    masked so two independent runs at the same commit can be compared
    for semantic stability.
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
