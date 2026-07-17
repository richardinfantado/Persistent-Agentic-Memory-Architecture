"""Parity tests: the same conformance suite passes against both
the in-process reference adapter AND the subprocess wrapper around
the same reference implementation.

If these tests pass but the in-process suite passes, then the
subprocess protocol is a lossless transport for the operation
surface currently exercised by the suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conformance.adapters.reference_python import ReferencePythonAdapter
from conformance.harness.runner import run_profile
from conformance.harness.subprocess_adapter import SubprocessAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
REF_PY_PATH = REPO_ROOT / "implementations" / "reference-python"

WRAPPER_ARGV = [
    sys.executable,
    "-m", "conformance.adapters.reference_python_subprocess",
]


def _subprocess_factory():
    import os
    env = os.environ.copy()
    # Make both `pamspec_ref` and `conformance` importable in the child.
    pypath = os.pathsep.join([str(REF_PY_PATH), str(REPO_ROOT)])
    env["PYTHONPATH"] = pypath + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return SubprocessAdapter(WRAPPER_ARGV, env=env, cwd=str(REPO_ROOT))


def _in_process_factory():
    return ReferencePythonAdapter(":memory:")


@pytest.mark.parametrize("profile", ["PAMSPEC-Lite", "PAMSPEC-Delegation", "PAMSPEC-Subscribe"])
def test_subprocess_adapter_passes_same_suite_as_in_process(profile):
    subproc_report = run_profile(profile, _subprocess_factory)
    if not subproc_report.passed:
        pytest.fail("subprocess adapter failed conformance:\n" + subproc_report.summary(), pytrace=False)


@pytest.mark.parametrize("profile", ["PAMSPEC-Lite", "PAMSPEC-Delegation", "PAMSPEC-Subscribe"])
def test_subprocess_report_case_names_match_in_process(profile):
    """Beyond both passing, the two adapters must exercise the same
    cases. If the subprocess adapter is silently skipping any case
    (e.g. via NotImplementedError being swallowed elsewhere), this
    test catches it."""
    subproc = run_profile(profile, _subprocess_factory)
    inproc = run_profile(profile, _in_process_factory)
    assert [c.name for c in subproc.cases] == [c.name for c in inproc.cases]
    assert subproc.total == inproc.total > 0


def test_subprocess_adapter_hello_metadata_is_populated():
    adapter = _subprocess_factory()
    try:
        info = adapter.info
        assert info.protocol_version == 1
        assert info.adapter_name == "reference-python-subprocess"
        assert info.implementation_name == "pamspec_ref"
        assert "PAMSPEC-Lite" in info.profiles_supported
    finally:
        adapter.close()


def test_subprocess_adapter_closes_cleanly():
    adapter = _subprocess_factory()
    adapter.close()
    # Double-close must be a no-op.
    adapter.close()
