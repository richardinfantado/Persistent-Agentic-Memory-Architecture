import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from pamspec_ref import MemoryService, PamspecError

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "schemas" / "0.1-draft"


@pytest.fixture
def schema_registry():
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


@pytest.fixture
def obj_validator(schema_registry):
    schema = json.loads((SCHEMA_DIR / "memory-object.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, registry=schema_registry)


@pytest.fixture
def svc():
    s = MemoryService(":memory:")
    yield s
    s.close()


ACTOR = {"actor_id": "actor:test", "actor_kind": "human"}
PROV = {
    "provenance_id": "prov:test:1",
    "actor": ACTOR,
    "activity": "created",
    "recorded_at": "2026-07-17T00:00:00.000000Z",
}


def test_create_produces_conforming_envelope(svc, obj_validator):
    result = svc.create(
        scope_id="workspace:test",
        object_type="claim",
        canonical_content={"statement": "hello"},
        actor=ACTOR,
        provenance=PROV,
    )
    obj_validator.validate(result["envelope"])
    assert result["envelope"]["sequence"] == 1
    assert result["envelope"]["validation_state"] == "unverified"


def test_read_returns_current_version(svc):
    created = svc.create(
        scope_id="workspace:test",
        object_type="claim",
        canonical_content={"statement": "hello"},
        actor=ACTOR,
        provenance=PROV,
    )
    got = svc.read("workspace:test", created["object_id"])
    assert got["version_id"] == created["version_id"]


def test_update_with_expected_version_creates_new_version(svc):
    created = svc.create(
        scope_id="workspace:test",
        object_type="claim",
        canonical_content={"statement": "v1"},
        actor=ACTOR,
        provenance=PROV,
    )
    updated = svc.update(
        scope_id="workspace:test",
        object_id=created["object_id"],
        expected_version_id=created["version_id"],
        canonical_content={"statement": "v2"},
        actor=ACTOR,
        provenance=PROV,
    )
    assert updated["sequence"] == 2
    assert updated["version_id"] != created["version_id"]
    history = svc.history("workspace:test", created["object_id"])
    assert [h["sequence"] for h in history] == [1, 2]


def test_stale_expected_version_raises_version_conflict(svc):
    created = svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "v1"}, actor=ACTOR, provenance=PROV,
    )
    svc.update(
        scope_id="workspace:test", object_id=created["object_id"],
        expected_version_id=created["version_id"],
        canonical_content={"statement": "v2"}, actor=ACTOR, provenance=PROV,
    )
    with pytest.raises(PamspecError) as excinfo:
        svc.update(
            scope_id="workspace:test", object_id=created["object_id"],
            expected_version_id=created["version_id"],
            canonical_content={"statement": "v3"}, actor=ACTOR, provenance=PROV,
        )
    assert excinfo.value.code == "version_conflict"
    assert excinfo.value.retryable is True


def test_idempotent_create_returns_same_result(svc):
    r1 = svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "x"}, actor=ACTOR, provenance=PROV,
        idempotency_key="k1",
    )
    r2 = svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "x"}, actor=ACTOR, provenance=PROV,
        idempotency_key="k1",
    )
    assert r1["version_id"] == r2["version_id"]


def test_idempotent_create_different_body_raises_duplicate_operation(svc):
    svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "x"}, actor=ACTOR, provenance=PROV,
        idempotency_key="k2",
    )
    with pytest.raises(PamspecError) as excinfo:
        svc.create(
            scope_id="workspace:test", object_type="claim",
            canonical_content={"statement": "y"}, actor=ACTOR, provenance=PROV,
            idempotency_key="k2",
        )
    assert excinfo.value.code == "duplicate_operation"


def test_delete_creates_tombstone_and_blocks_read_by_default(svc):
    created = svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "hello"}, actor=ACTOR, provenance=PROV,
    )
    svc.delete(
        scope_id="workspace:test", object_id=created["object_id"],
        expected_version_id=created["version_id"], actor=ACTOR, provenance=PROV,
    )
    with pytest.raises(PamspecError) as excinfo:
        svc.read("workspace:test", created["object_id"])
    assert excinfo.value.code == "object_deleted"


def test_lifecycle_transition_active_to_archived(svc):
    created = svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "hello"}, actor=ACTOR, provenance=PROV,
    )
    res = svc.transition(
        scope_id="workspace:test", object_id=created["object_id"],
        expected_version_id=created["version_id"],
        dimension="lifecycle", target_state="archived",
        actor=ACTOR, provenance=PROV,
    )
    assert res["envelope"]["lifecycle_state"] == "archived"


def test_invalid_lifecycle_transition_rejected(svc):
    created = svc.create(
        scope_id="workspace:test", object_type="claim",
        canonical_content={"statement": "hello"}, actor=ACTOR, provenance=PROV,
        lifecycle_state="archived",
    )
    with pytest.raises(PamspecError) as excinfo:
        svc.transition(
            scope_id="workspace:test", object_id=created["object_id"],
            expected_version_id=created["version_id"],
            dimension="lifecycle", target_state="superseded",
            actor=ACTOR, provenance=PROV,
        )
    assert excinfo.value.code == "invalid_state_transition"


def test_query_default_filters_apply(svc):
    a = svc.create(
        scope_id="workspace:q", object_type="claim",
        canonical_content={"s": "unverified"}, actor=ACTOR, provenance=PROV,
    )
    b = svc.create(
        scope_id="workspace:q", object_type="claim",
        canonical_content={"s": "corroborated"}, actor=ACTOR, provenance=PROV,
        validation_state="corroborated",
    )
    default = svc.query(scope_id="workspace:q")
    ids = {r["object_id"] for r in default}
    assert b["object_id"] in ids
    assert a["object_id"] not in ids

    all_states = svc.query(scope_id="workspace:q", validation_state=None)
    assert {r["object_id"] for r in all_states} >= {a["object_id"], b["object_id"]}


def test_scope_isolation(svc):
    a = svc.create(
        scope_id="workspace:a", object_type="claim",
        canonical_content={"s": "in a"}, actor=ACTOR, provenance=PROV,
    )
    with pytest.raises(PamspecError):
        svc.read("workspace:b", a["object_id"])


def test_event_ledger_records_operations(svc):
    created = svc.create(
        scope_id="workspace:e", object_type="claim",
        canonical_content={"s": "x"}, actor=ACTOR, provenance=PROV,
    )
    svc.update(
        scope_id="workspace:e", object_id=created["object_id"],
        expected_version_id=created["version_id"],
        canonical_content={"s": "y"}, actor=ACTOR, provenance=PROV,
    )
    events = list(svc.events(scope_id="workspace:e"))
    types = [e["event_type"] for e in events]
    assert types == ["object_created", "object_updated"]
    seqs = [e["ledger_sequence"] for e in events]
    assert seqs == sorted(set(seqs)) and len(set(seqs)) == len(seqs)
