import pytest

from pamspec_ref import MemoryService


ACTOR = {"actor_id": "actor:test", "actor_kind": "human"}
PROV = {
    "provenance_id": "prov:test:1",
    "actor": ACTOR,
    "activity": "created",
    "recorded_at": "2026-07-17T00:00:00Z",
}


@pytest.fixture
def svc():
    s = MemoryService(":memory:")
    yield s
    s.close()


def test_subscription_receives_matching_events(svc):
    sub = svc.subscribe(
        scope_id="workspace:sub",
        actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
    )
    svc.create(
        scope_id="workspace:sub", object_type="claim",
        canonical_content={"s": "one"}, actor=ACTOR, provenance=PROV,
    )
    svc.create(
        scope_id="workspace:sub", object_type="claim",
        canonical_content={"s": "two"}, actor=ACTOR, provenance=PROV,
    )
    delivered = sub.poll()
    assert len(delivered) == 2
    assert all(e["event_type"] == "object_created" for e in delivered)


def test_subscription_filter_excludes_non_matching(svc):
    sub = svc.subscribe(
        scope_id="workspace:filter",
        actor=ACTOR,
        filter_spec={"event_classes": ["object_deleted"]},
    )
    svc.create(
        scope_id="workspace:filter", object_type="claim",
        canonical_content={"s": "x"}, actor=ACTOR, provenance=PROV,
    )
    delivered = sub.poll()
    assert delivered == []


def test_subscription_per_event_authorization(svc):
    def deny_second(actor, event):
        return "one" not in str(event.get("payload", {}))

    sub = svc.subscribe(
        scope_id="workspace:auth",
        actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
        authorize=lambda actor, event: True,  # simple accept-all
    )
    r1 = svc.create(
        scope_id="workspace:auth", object_type="claim",
        canonical_content={"s": "one"}, actor=ACTOR, provenance=PROV,
    )
    r2 = svc.create(
        scope_id="workspace:auth", object_type="claim",
        canonical_content={"s": "two"}, actor=ACTOR, provenance=PROV,
    )
    delivered = sub.poll()
    ids = {e["object_id"] for e in delivered}
    assert r1["object_id"] in ids and r2["object_id"] in ids


def test_subscription_cursor_advances_across_polls(svc):
    sub = svc.subscribe(
        scope_id="workspace:cur", actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
    )
    svc.create(
        scope_id="workspace:cur", object_type="claim",
        canonical_content={"s": "a"}, actor=ACTOR, provenance=PROV,
    )
    first = sub.poll()
    assert len(first) == 1
    second = sub.poll()
    assert second == []
    svc.create(
        scope_id="workspace:cur", object_type="claim",
        canonical_content={"s": "b"}, actor=ACTOR, provenance=PROV,
    )
    third = sub.poll()
    assert len(third) == 1


def test_close_stops_delivery(svc):
    sub = svc.subscribe(
        scope_id="workspace:close", actor=ACTOR,
        filter_spec={"event_classes": ["object_created"]},
    )
    sub.close("test_close")
    svc.create(
        scope_id="workspace:close", object_type="claim",
        canonical_content={"s": "after close"}, actor=ACTOR, provenance=PROV,
    )
    assert sub.poll() == []
    assert sub.close_reason == "test_close"
