"""Portable behavioral conformance cases for Delegation Object enforcement."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from conformance.harness.adapter import Adapter, expect_error


SCOPE = "workspace:conformance-del"
SUP = {"actor_id": "actor:agent:supervisor", "actor_kind": "agent"}
WRK = {"actor_id": "actor:agent:worker", "actor_kind": "agent"}


def _iso(offset_seconds: int = 0) -> str:
    return (
        (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds))
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def case_grant_and_check_permits_matching_operation(a: Adapter) -> None:
    grant = a.grant_delegation(
        scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
        granted_operations=["read", "query"],
        policy_basis="policy:conformance",
        not_before=_iso(-1), not_after=_iso(3600),
    )
    result = a.check_delegation(
        delegation_id=grant["delegation_id"],
        scope_id=SCOPE, delegated_actor_id=WRK["actor_id"],
        operation="read",
    )
    assert result["delegation_id"] == grant["delegation_id"]


def case_check_denies_ungranted_operation(a: Adapter) -> None:
    grant = a.grant_delegation(
        scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
        granted_operations=["read"],
        policy_basis="policy:conformance",
        not_before=_iso(-1), not_after=_iso(3600),
    )
    with expect_error("access_denied"):
        a.check_delegation(
            delegation_id=grant["delegation_id"],
            scope_id=SCOPE, delegated_actor_id=WRK["actor_id"],
            operation="delete",
        )


def case_check_denies_outside_time_window(a: Adapter) -> None:
    grant = a.grant_delegation(
        scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
        granted_operations=["read"],
        policy_basis="policy:conformance",
        not_before=_iso(3600), not_after=_iso(7200),
    )
    with expect_error("access_denied"):
        a.check_delegation(
            delegation_id=grant["delegation_id"],
            scope_id=SCOPE, delegated_actor_id=WRK["actor_id"],
            operation="read",
        )


def case_grant_with_inverted_window_rejected(a: Adapter) -> None:
    with expect_error("policy_denied"):
        a.grant_delegation(
            scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
            granted_operations=["read"],
            policy_basis="policy:conformance",
            not_before=_iso(3600), not_after=_iso(-1),
        )


def case_usage_limit_exhausted(a: Adapter) -> None:
    grant = a.grant_delegation(
        scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
        granted_operations=["read"],
        policy_basis="policy:conformance",
        not_before=_iso(-1), not_after=_iso(3600),
        usage_limit=2,
    )
    a.check_delegation(
        delegation_id=grant["delegation_id"], scope_id=SCOPE,
        delegated_actor_id=WRK["actor_id"], operation="read",
    )
    a.check_delegation(
        delegation_id=grant["delegation_id"], scope_id=SCOPE,
        delegated_actor_id=WRK["actor_id"], operation="read",
    )
    with expect_error("access_denied"):
        a.check_delegation(
            delegation_id=grant["delegation_id"], scope_id=SCOPE,
            delegated_actor_id=WRK["actor_id"], operation="read",
        )


def case_revoked_delegation_denies(a: Adapter) -> None:
    grant = a.grant_delegation(
        scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
        granted_operations=["read"],
        policy_basis="policy:conformance",
        not_before=_iso(-1), not_after=_iso(3600),
    )
    a.revoke_delegation(grant["delegation_id"])
    with expect_error("access_denied"):
        a.check_delegation(
            delegation_id=grant["delegation_id"], scope_id=SCOPE,
            delegated_actor_id=WRK["actor_id"], operation="read",
        )


def case_object_id_restriction(a: Adapter) -> None:
    grant = a.grant_delegation(
        scope_id=SCOPE, granting_actor=SUP, delegated_actor=WRK,
        granted_operations=["read"],
        policy_basis="policy:conformance",
        not_before=_iso(-1), not_after=_iso(3600),
        granted_object_ids=["mem:permitted:001"],
    )
    a.check_delegation(
        delegation_id=grant["delegation_id"], scope_id=SCOPE,
        delegated_actor_id=WRK["actor_id"], operation="read",
        object_id="mem:permitted:001",
    )
    with expect_error("access_denied"):
        a.check_delegation(
            delegation_id=grant["delegation_id"], scope_id=SCOPE,
            delegated_actor_id=WRK["actor_id"], operation="read",
            object_id="mem:not-permitted:001",
        )
