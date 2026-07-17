from datetime import datetime, timedelta, timezone

import pytest

from pamspec_ref import MemoryService, PamspecError


SUPERVISOR = {"actor_id": "actor:agent:supervisor", "actor_kind": "agent"}
WORKER = {"actor_id": "actor:agent:worker-01", "actor_kind": "agent"}


def _now_iso(offset_seconds=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat(timespec="microseconds").replace("+00:00", "Z")


@pytest.fixture
def svc():
    s = MemoryService(":memory:")
    yield s
    s.close()


def test_grant_and_check_permits_matching_operation(svc):
    delegations = svc.delegations()
    grant = delegations.grant(
        scope_id="workspace:test",
        granting_actor=SUPERVISOR,
        delegated_actor=WORKER,
        granted_operations=["read", "query"],
        policy_basis="policy:test",
        not_before=_now_iso(-1),
        not_after=_now_iso(3600),
    )
    env = delegations.check(
        delegation_id=grant["delegation_id"],
        scope_id="workspace:test",
        delegated_actor_id=WORKER["actor_id"],
        operation="read",
    )
    assert env["delegation_id"] == grant["delegation_id"]


def test_check_denies_ungranted_operation(svc):
    delegations = svc.delegations()
    grant = delegations.grant(
        scope_id="workspace:test",
        granting_actor=SUPERVISOR,
        delegated_actor=WORKER,
        granted_operations=["read"],
        policy_basis="policy:test",
        not_before=_now_iso(-1),
        not_after=_now_iso(3600),
    )
    with pytest.raises(PamspecError) as excinfo:
        delegations.check(
            delegation_id=grant["delegation_id"],
            scope_id="workspace:test",
            delegated_actor_id=WORKER["actor_id"],
            operation="delete",
        )
    assert excinfo.value.code == "access_denied"


def test_check_denies_outside_time_window(svc):
    delegations = svc.delegations()
    grant = delegations.grant(
        scope_id="workspace:test",
        granting_actor=SUPERVISOR,
        delegated_actor=WORKER,
        granted_operations=["read"],
        policy_basis="policy:test",
        not_before=_now_iso(3600),
        not_after=_now_iso(7200),
    )
    with pytest.raises(PamspecError) as excinfo:
        delegations.check(
            delegation_id=grant["delegation_id"],
            scope_id="workspace:test",
            delegated_actor_id=WORKER["actor_id"],
            operation="read",
        )
    assert excinfo.value.code == "access_denied"


def test_inverted_window_rejected_at_grant_time(svc):
    delegations = svc.delegations()
    with pytest.raises(PamspecError) as excinfo:
        delegations.grant(
            scope_id="workspace:test",
            granting_actor=SUPERVISOR,
            delegated_actor=WORKER,
            granted_operations=["read"],
            policy_basis="policy:test",
            not_before=_now_iso(3600),
            not_after=_now_iso(-1),
        )
    assert excinfo.value.code == "policy_denied"


def test_usage_limit_enforced(svc):
    delegations = svc.delegations()
    grant = delegations.grant(
        scope_id="workspace:test",
        granting_actor=SUPERVISOR,
        delegated_actor=WORKER,
        granted_operations=["read"],
        policy_basis="policy:test",
        not_before=_now_iso(-1),
        not_after=_now_iso(3600),
        usage_limit=2,
    )
    delegations.check(grant["delegation_id"], "workspace:test", WORKER["actor_id"], "read")
    delegations.check(grant["delegation_id"], "workspace:test", WORKER["actor_id"], "read")
    with pytest.raises(PamspecError) as excinfo:
        delegations.check(grant["delegation_id"], "workspace:test", WORKER["actor_id"], "read")
    assert excinfo.value.code == "access_denied"


def test_revoke_denies_subsequent_check(svc):
    delegations = svc.delegations()
    grant = delegations.grant(
        scope_id="workspace:test",
        granting_actor=SUPERVISOR,
        delegated_actor=WORKER,
        granted_operations=["read"],
        policy_basis="policy:test",
        not_before=_now_iso(-1),
        not_after=_now_iso(3600),
    )
    delegations.revoke(grant["delegation_id"])
    with pytest.raises(PamspecError) as excinfo:
        delegations.check(grant["delegation_id"], "workspace:test", WORKER["actor_id"], "read")
    assert excinfo.value.code == "access_denied"


def test_object_id_restriction(svc):
    delegations = svc.delegations()
    grant = delegations.grant(
        scope_id="workspace:test",
        granting_actor=SUPERVISOR,
        delegated_actor=WORKER,
        granted_operations=["read"],
        policy_basis="policy:test",
        not_before=_now_iso(-1),
        not_after=_now_iso(3600),
        granted_object_ids=["mem:claim:permitted"],
    )
    delegations.check(
        grant["delegation_id"], "workspace:test", WORKER["actor_id"], "read",
        object_id="mem:claim:permitted",
    )
    with pytest.raises(PamspecError):
        delegations.check(
            grant["delegation_id"], "workspace:test", WORKER["actor_id"], "read",
            object_id="mem:claim:not-permitted",
        )
