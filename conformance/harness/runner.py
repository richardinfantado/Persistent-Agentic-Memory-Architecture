"""Conformance suite runner.

Discovers suite modules by profile, executes their test functions
against a provided Adapter factory, and produces a ConformanceReport.

Each test function receives a fresh Adapter (constructed via the
factory) so state does not leak between cases.
"""

from __future__ import annotations

import importlib
import inspect
import time
import traceback
from dataclasses import dataclass, field
from typing import Callable

from .adapter import Adapter


PROFILE_SUITE_MODULES = {
    "PAMSPEC-Lite": "conformance.suite.test_lite",
    "PAMSPEC-Delegation": "conformance.suite.test_delegation",
    "PAMSPEC-Subscribe": "conformance.suite.test_subscription",
}


@dataclass
class CaseResult:
    name: str
    passed: bool
    duration_ms: float
    error: str | None = None


@dataclass
class ConformanceReport:
    profile: str
    adapter_class: str
    cases: list[CaseResult] = field(default_factory=list)

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


def run_profile(profile: str, factory: Callable[[], Adapter]) -> ConformanceReport:
    """Run every case_* function in the profile's suite module against
    a fresh Adapter produced by `factory`. Returns a ConformanceReport.
    """
    module_name = PROFILE_SUITE_MODULES.get(profile)
    if module_name is None:
        raise ValueError(f"unknown profile: {profile}")
    module = importlib.import_module(module_name)

    probe = factory()
    adapter_class = probe.__class__.__name__
    probe.close()

    report = ConformanceReport(profile=profile, adapter_class=adapter_class)
    for name, fn in sorted(inspect.getmembers(module, inspect.isfunction)):
        if not name.startswith("case_"):
            continue
        adapter = factory()
        started = time.perf_counter()
        error: str | None = None
        try:
            fn(adapter)
            passed = True
        except NotImplementedError as e:
            passed = False
            error = f"adapter missing feature: {e}"
        except AssertionError as e:
            passed = False
            error = f"assertion failed: {e}"
        except Exception:
            passed = False
            error = traceback.format_exc()
        finally:
            try:
                adapter.close()
            except Exception:
                pass
        elapsed_ms = (time.perf_counter() - started) * 1000
        report.cases.append(CaseResult(name=name, passed=passed, duration_ms=elapsed_ms, error=error))

    return report
