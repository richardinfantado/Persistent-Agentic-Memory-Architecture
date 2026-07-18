"""Conformance suite runner.

Discovers suite modules by profile, executes their test functions
against a provided Adapter factory, and produces a ConformanceReport.

Each test function receives a fresh Adapter (constructed via the
factory) so state does not leak between cases.

Reports are producible as human-readable text (summary()) and as
machine-readable JSON (to_json()). JSON reports include adapter and
implementation metadata plus suite/spec commit pinning; see
PROTOCOL.md for the source of the metadata.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import subprocess
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .adapter import Adapter


PROFILE_SUITE_MODULES = {
    "PAMSPEC-Lite": "conformance.suite.test_lite",
    "PAMSPEC-Delegation": "conformance.suite.test_delegation",
    "PAMSPEC-Subscribe": "conformance.suite.test_subscription",
}

REPORT_FORMAT_VERSION = 1

# R6.2c: always resolve git commands against the PAMSPEC repository
# root, not the process cwd. Otherwise `git rev-parse HEAD` returns
# the SHA of whichever repository the caller happens to be inside.
REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_head_commit() -> str:
    """Return the current git HEAD commit SHA of the PAMSPEC
    repository (NOT of the process cwd), or empty string on failure.
    R6.2c: always uses REPO_ROOT as the cwd so evidence attribution
    cannot be shifted to another repository by running the harness
    from inside a nested checkout.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=2.0,
            cwd=str(REPO_ROOT),
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class CaseResult:
    name: str
    passed: bool
    duration_ms: float
    error: str | None = None
    # R6.2b: structured outcome classification, DELIBERATELY NOT
    # serialized in to_dict() so the legacy JSON report shape is
    # unchanged. Consumed by the R6 evidence emitter through the
    # ExecutionSession returned from runner.run_profile() callers.
    # Values: 'passed' | 'assertion_failure' | 'missing_feature' |
    #         'execution_error'
    outcome_kind: str = "passed"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 3),
        }
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ConformanceReport:
    profile: str
    adapter_class: str
    cases: list[CaseResult] = field(default_factory=list)
    # Metadata (populated by run_profile; safe to leave blank when
    # constructing manually for testing).
    started_at: str = ""
    finished_at: str = ""
    suite_commit: str = ""
    adapter_info: dict[str, Any] | None = None
    report_format_version: int = REPORT_FORMAT_VERSION

    @property
    def passed(self) -> bool:
        return bool(self.cases) and all(c.passed for c in self.cases)

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    def summary(self) -> str:
        lines = [
            "PAMSPEC Conformance Report",
            f"Profile: {self.profile}",
            f"Adapter: {self.adapter_class}",
            f"Result:  {self.passed_count}/{self.total} passed",
            "",
        ]
        for c in self.cases:
            status = "PASS" if c.passed else "FAIL"
            lines.append(f"  [{status}] {c.name} ({c.duration_ms:.1f} ms)")
            if not c.passed and c.error:
                for line in c.error.splitlines():
                    lines.append(f"        {line}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_format_version": self.report_format_version,
            "profile": self.profile,
            "adapter_class": self.adapter_class,
            "adapter_info": self.adapter_info,
            "suite_commit": self.suite_commit,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "totals": {
                "total": self.total,
                "passed": self.passed_count,
                "failed": self.total - self.passed_count,
                "all_passed": self.passed,
            },
            "cases": [c.to_dict() for c in self.cases],
        }

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def _collect_adapter_info(adapter: Adapter) -> dict[str, Any]:
    """Extract adapter-and-implementation metadata for the report.
    Works for both in-process and subprocess adapters.

    R6.2c: also captures the adapter's evidence_identity() if the
    adapter defines one. Consumed by the R6 evidence emitter for
    in-process subject/version binding.
    """
    info: dict[str, Any] = {
        "class_name": adapter.__class__.__name__,
        "supported_profiles": list(adapter.supported_profiles()),
    }
    identity_getter = getattr(adapter, "evidence_identity", None)
    if callable(identity_getter):
        try:
            identity = identity_getter()
            if isinstance(identity, dict) and identity:
                info["evidence_identity"] = identity
        except Exception:
            pass
    subprocess_info = getattr(adapter, "info", None)
    if subprocess_info is not None:
        info["subprocess"] = {
            "protocol_version": getattr(subprocess_info, "protocol_version", None),
            "adapter_name": getattr(subprocess_info, "adapter_name", None),
            "adapter_version": getattr(subprocess_info, "adapter_version", None),
            "implementation_name": getattr(subprocess_info, "implementation_name", None),
            "implementation_version": getattr(subprocess_info, "implementation_version", None),
            "spec_commit": getattr(subprocess_info, "spec_commit", None),
        }
    return info


def run_profile(profile: str, factory: Callable[[], Adapter]) -> ConformanceReport:
    """Run every case_* function in the profile's suite module against
    a fresh Adapter produced by `factory`. Returns a ConformanceReport
    with metadata suitable for JSON serialization.
    """
    module_name = PROFILE_SUITE_MODULES.get(profile)
    if module_name is None:
        raise ValueError(f"unknown profile: {profile}")
    module = importlib.import_module(module_name)

    started_at = _iso_utc_now()
    probe = factory()
    adapter_class = probe.__class__.__name__
    adapter_info = _collect_adapter_info(probe)
    probe.close()

    report = ConformanceReport(
        profile=profile,
        adapter_class=adapter_class,
        adapter_info=adapter_info,
        suite_commit=_git_head_commit(),
        started_at=started_at,
    )
    for name, fn in sorted(inspect.getmembers(module, inspect.isfunction)):
        if not name.startswith("case_"):
            continue
        adapter = factory()
        started = time.perf_counter()
        error: str | None = None
        outcome_kind = "passed"
        try:
            fn(adapter)
            passed = True
        except NotImplementedError as e:
            passed = False
            outcome_kind = "missing_feature"
            error = f"adapter missing feature: {e}"
        except AssertionError as e:
            passed = False
            outcome_kind = "assertion_failure"
            error = f"assertion failed: {e}"
        except Exception:
            passed = False
            outcome_kind = "execution_error"
            error = traceback.format_exc()
        finally:
            try:
                adapter.close()
            except Exception:
                pass
        elapsed_ms = (time.perf_counter() - started) * 1000
        report.cases.append(CaseResult(
            name=name, passed=passed, duration_ms=elapsed_ms,
            error=error, outcome_kind=outcome_kind,
        ))

    report.finished_at = _iso_utc_now()
    return report
