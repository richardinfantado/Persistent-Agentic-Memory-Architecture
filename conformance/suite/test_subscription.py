"""Portable behavioral conformance cases for Subscribe."""

from __future__ import annotations

from conformance.harness.adapter import Adapter


SCOPE = "workspace:conformance-sub"
ACTOR = {"actor_id": "actor:agent:observer", "actor_kind": "agent"}
PROV = {
    "provenance_id": "prov:sub-conformance:1",
    "actor": ACTOR,
    "activity": "created",
    "recorded_at": "2026-07-17T00:00:00Z",
}


def _make_claim(a: Adapter, statement: str) -> dict:
    return a.create(
        scope_id=SCOPE,
        object_type="claim",
        canonical_content={"statement": statement},
        actor=ACTOR,
        provenance=PROV,
    )


def case_subscription_delivers_matching_events(a: Adapter) -> None:
    sub = a.subscribe(
        scope_id=SCOPE, actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
    )
    _make_claim(a, "one")
    _make_claim(a, "two")
    delivered = a.poll_subscription(sub)
    assert len(delivered) == 2
    assert all(e["event_type"] == "object_created" for e in delivered)


def case_subscription_filter_excludes_non_matching(a: Adapter) -> None:
    sub = a.subscribe(
        scope_id=SCOPE, actor=ACTOR,
        filter_spec={"event_classes": ["object_deleted"]},
    )
    _make_claim(a, "unfiltered create")
    assert a.poll_subscription(sub) == []


def case_subscription_cursor_advances(a: Adapter) -> None:
    sub = a.subscribe(
        scope_id=SCOPE, actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
    )
    _make_claim(a, "first")
    first = a.poll_subscription(sub)
    assert len(first) == 1
    second = a.poll_subscription(sub)
    assert second == [], "no new events should be delivered on second poll"
    _make_claim(a, "second")
    third = a.poll_subscription(sub)
    assert len(third) == 1


def case_close_stops_delivery(a: Adapter) -> None:
    sub = a.subscribe(
        scope_id=SCOPE, actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
    )
    a.close_subscription(sub, reason="conformance_test")
    _make_claim(a, "after close")
    assert a.poll_subscription(sub) == []
