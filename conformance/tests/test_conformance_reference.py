"""Run the conformance suite against the reference Python adapter.

If PAMSPEC ever gains a second implementation, copy this file and
swap the factory — no other code changes needed.
"""

import pytest

from conformance.adapters.reference_python import ReferencePythonAdapter
from conformance.harness.runner import run_profile


def _factory():
    return ReferencePythonAdapter(":memory:")


@pytest.mark.parametrize("profile", ["PAMSPEC-Lite", "PAMSPEC-Delegation", "PAMSPEC-Subscribe"])
def test_reference_python_conforms_to(profile):
    report = run_profile(profile, _factory)
    assert report.total > 0, f"no cases discovered for profile {profile}"
    if not report.passed:
        pytest.fail("\n" + report.summary(), pytrace=False)


def test_report_summary_printable(capsys):
    report = run_profile("PAMSPEC-Lite", _factory)
    print(report.summary())
    captured = capsys.readouterr()
    assert "PAMSPEC Conformance Report" in captured.out
    assert "Profile: PAMSPEC-Lite" in captured.out
