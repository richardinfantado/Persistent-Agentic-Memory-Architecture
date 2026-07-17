"""Negative-control tests.

For each broken adapter, the harness MUST FAIL the designated
suite case. If the harness passes a broken adapter that violates
a property, then the suite's assertion for that property is a
no-op and the harness has a blind spot.

This test asserts that:
  1. Each broken adapter is caught by the designated case (case fails).
  2. Each broken adapter is caught EARLIER than all other cases the
     harness would run — meaning the specific violation drives the
     failure, not incidental flakiness.

Do NOT relax these assertions to make a broken adapter pass. If a
case designation drifts, update the mapping below to name the new
correct case and understand why the old case no longer catches the
violation.
"""

from __future__ import annotations

import pytest

from conformance.adapters.broken import (
    BrokenIgnoresScopeAdapter,
    BrokenSilentOverwriteAdapter,
    BrokenNonMonotonicSequenceAdapter,
    BrokenAcceptsStaleExpectedVersionAdapter,
    BrokenReusesIdempotencyKeyAdapter,
    BrokenReadsDeletedObjectAdapter,
    BrokenLosesUnknownExtensionFieldsAdapter,
)
from conformance.harness.runner import run_profile


# (adapter class, profile, designated case name)
BROKEN_ADAPTER_MATRIX = [
    (BrokenIgnoresScopeAdapter,               "PAMSPEC-Lite", "case_scope_isolation"),
    (BrokenSilentOverwriteAdapter,            "PAMSPEC-Lite", "case_update_creates_new_version"),
    (BrokenNonMonotonicSequenceAdapter,       "PAMSPEC-Lite", "case_history_is_monotonic"),
    (BrokenAcceptsStaleExpectedVersionAdapter,"PAMSPEC-Lite", "case_stale_expected_version_raises_version_conflict"),
    (BrokenReusesIdempotencyKeyAdapter,       "PAMSPEC-Lite", "case_idempotent_key_reuse_with_different_body_fails"),
    (BrokenReadsDeletedObjectAdapter,         "PAMSPEC-Lite", "case_delete_creates_tombstone_and_blocks_default_read"),
    (BrokenLosesUnknownExtensionFieldsAdapter,"PAMSPEC-Lite", "case_unknown_extension_fields_preserved_on_read"),
]


@pytest.mark.parametrize("cls,profile,designated_case", BROKEN_ADAPTER_MATRIX,
                         ids=[cls.__name__ for cls, _, _ in BROKEN_ADAPTER_MATRIX])
def test_broken_adapter_fails_designated_case(cls, profile, designated_case):
    report = run_profile(profile, cls)
    named = {c.name: c for c in report.cases}
    assert designated_case in named, (
        f"designated case {designated_case!r} not found in profile {profile}; "
        f"present cases: {sorted(named)}"
    )
    assert named[designated_case].passed is False, (
        f"{cls.__name__} was expected to FAIL {designated_case!r} but it PASSED. "
        f"Either the adapter no longer violates the property, or the suite case "
        f"no longer asserts it. Adapter output for that case:\n"
        f"{named[designated_case].error!r}"
    )


@pytest.mark.parametrize("cls,profile,designated_case", BROKEN_ADAPTER_MATRIX,
                         ids=[cls.__name__ for cls, _, _ in BROKEN_ADAPTER_MATRIX])
def test_broken_adapter_report_is_json_serializable(cls, profile, designated_case):
    """The harness must produce a machine-readable JSON report even
    when cases fail (needed for CI upload and implementation reports)."""
    import json
    report = run_profile(profile, cls)
    payload = report.to_json()
    parsed = json.loads(payload)
    assert parsed["report_format_version"] == 1
    assert parsed["profile"] == profile
    assert parsed["adapter_class"] == cls.__name__
    assert parsed["totals"]["failed"] >= 1
    assert any(c["name"] == designated_case and c["passed"] is False for c in parsed["cases"])
