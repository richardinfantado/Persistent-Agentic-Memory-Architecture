"""R6.2a explicit CaseAssessment registry for the PAMSPEC-Lite suite
against the reference-python subject.

Every case in `conformance/suite/test_lite.py` MUST have an entry here.
Missing entries cause R6.2a to fail closed at emission time.

Classification stance for this subject (reference-python via
ReferencePythonAdapter):
  - The adapter is a translation-only wrapper; it does not carry PAMSPEC
    semantics itself. Therefore a passing case is direct evidence that
    the reference implementation satisfies the requirement natively.
  - A failing case is direct evidence that the reference implementation
    does NOT satisfy the requirement. Because we own the reference
    implementation and treat any failed conformance case as a bug to fix,
    we record the failure as `gap` + `confirmed`. Other subjects
    (framework adapters) must NOT reuse these actions; they need their
    own registry with more conservative fail semantics.

Requirement IDs use the form `PAMSPEC-Lite.<AREA>.<REQ>` and are stable
across suite test function renames.
"""

from __future__ import annotations

from ..evidence_emitter import CaseAssessment


def _native_or_gap(requirement_id: str, extra_limitations: list[str] | None = None) -> CaseAssessment:
    return CaseAssessment(
        requirement_id=requirement_id,
        on_pass_classification="native",
        on_pass_claim_status="confirmed",
        on_fail_classification="gap",
        on_fail_claim_status="confirmed",
        on_missing_feature_classification="not_testable",
        on_missing_feature_claim_status="not_testable",
        evidence_source=["adapter"],
        extra_limitations=list(extra_limitations or []),
    )


REFERENCE_PYTHON_LITE_REGISTRY: dict[str, CaseAssessment] = {
    "case_create_returns_object_and_version_ids": _native_or_gap(
        "PAMSPEC-Lite.OBJECT.CREATE_RETURNS_IDS",
    ),
    "case_read_returns_current_envelope": _native_or_gap(
        "PAMSPEC-Lite.OBJECT.READ_CURRENT",
    ),
    "case_read_specific_version": _native_or_gap(
        "PAMSPEC-Lite.OBJECT.READ_SPECIFIC_VERSION",
    ),
    "case_update_creates_new_version": _native_or_gap(
        "PAMSPEC-Lite.MUTATION.UPDATE_APPENDS_VERSION",
    ),
    "case_stale_expected_version_raises_version_conflict": _native_or_gap(
        "PAMSPEC-Lite.MUTATION.EXPECTED_VERSION_REJECTS_STALE",
    ),
    "case_missing_object_raises_object_not_found": _native_or_gap(
        "PAMSPEC-Lite.OBJECT.MISSING_RAISES_OBJECT_NOT_FOUND",
    ),
    "case_scope_isolation": _native_or_gap(
        "PAMSPEC-Lite.SCOPE.CROSS_SCOPE_READ_ISOLATED",
    ),
    "case_idempotent_create_returns_same_result": _native_or_gap(
        "PAMSPEC-Lite.MUTATION.IDEMPOTENT_CREATE_SAME_RESULT",
    ),
    "case_idempotent_key_reuse_with_different_body_fails": _native_or_gap(
        "PAMSPEC-Lite.MUTATION.IDEMPOTENT_KEY_REUSE_DIFFERENT_BODY_REJECTED",
    ),
    "case_delete_creates_tombstone_and_blocks_default_read": _native_or_gap(
        "PAMSPEC-Lite.DELETION.TOMBSTONE_BLOCKS_READ",
    ),
    "case_lifecycle_transition_active_to_archived": _native_or_gap(
        "PAMSPEC-Lite.LIFECYCLE.ACTIVE_TO_ARCHIVED",
    ),
    "case_invalid_lifecycle_transition_rejected": _native_or_gap(
        "PAMSPEC-Lite.LIFECYCLE.INVALID_TRANSITION_REJECTED",
    ),
    "case_query_default_filters_apply": _native_or_gap(
        "PAMSPEC-Lite.QUERY.DEFAULT_FILTERS_APPLY",
    ),
    "case_history_is_monotonic": _native_or_gap(
        "PAMSPEC-Lite.HISTORY.MONOTONIC_ORDER",
    ),
    "case_unknown_extension_fields_preserved_on_read": _native_or_gap(
        "PAMSPEC-Lite.OBJECT.UNKNOWN_EXTENSIONS_PRESERVED",
    ),
}


REFERENCE_PYTHON_SUBJECT = {
    "kind": "implementation",
    "name": "reference-python",
    "version": "0.1-draft",
}

REFERENCE_PYTHON_ADAPTER = {
    "name": "ReferencePythonAdapter",
    "version": "translation-only",
}
