import pytest
from pamspec_ref import MemoryService
from pamspec_mcp_server import PamspecMcpAdapter


ACTOR = {"actor_id": "actor:test", "actor_kind": "human"}
PROV = {
    "provenance_id": "prov:test:1",
    "actor": ACTOR,
    "activity": "created",
    "recorded_at": "2026-07-17T00:00:00Z",
}


@pytest.fixture
def adapter():
    svc = MemoryService(":memory:")
    yield PamspecMcpAdapter(svc)
    svc.close()


def test_manifest_lists_supported_operations(adapter):
    m = adapter.manifest()
    assert m["spec_version"] == "0.1.0-draft"
    assert m["binding_version"] == "0.1.0-draft"
    assert "PAMSPEC-Lite" in m["profiles"]
    assert "create" in m["operations"]
    assert "read" in m["operations"]


def test_dispatch_create_returns_envelope(adapter):
    resp = adapter.dispatch("pamspec.create", {
        "scope_id": "workspace:t",
        "object_type": "claim",
        "canonical_content": {"statement": "hi"},
        "actor": ACTOR,
        "provenance": PROV,
    })
    assert "result" in resp
    assert resp["result"]["envelope"]["object_type"] == "claim"


def test_unknown_tool_returns_error_envelope_not_exception(adapter):
    resp = adapter.dispatch("pamspec.does_not_exist", {"operation_id": "op:x"})
    assert "error" in resp
    assert resp["error"]["code"] == "invalid_request"
    assert resp["error"]["operation_id"] == "op:x"


def test_version_conflict_returns_pamspec_error_envelope(adapter):
    r1 = adapter.dispatch("pamspec.create", {
        "scope_id": "workspace:t",
        "object_type": "claim",
        "canonical_content": {"s": "v1"},
        "actor": ACTOR, "provenance": PROV,
    })
    obj_id = r1["result"]["object_id"]
    ver_id = r1["result"]["version_id"]

    adapter.dispatch("pamspec.update", {
        "scope_id": "workspace:t",
        "object_id": obj_id,
        "expected_version_id": ver_id,
        "canonical_content": {"s": "v2"},
        "actor": ACTOR, "provenance": PROV,
    })

    conflict = adapter.dispatch("pamspec.update", {
        "scope_id": "workspace:t",
        "object_id": obj_id,
        "expected_version_id": ver_id,
        "canonical_content": {"s": "v3"},
        "actor": ACTOR, "provenance": PROV,
    })
    assert "error" in conflict
    assert conflict["error"]["code"] == "version_conflict"
    assert conflict["error"]["retryable"] is True


def test_query_default_returns_only_corroborated_active(adapter):
    adapter.dispatch("pamspec.create", {
        "scope_id": "workspace:q",
        "object_type": "claim",
        "canonical_content": {"s": "unverified"},
        "actor": ACTOR, "provenance": PROV,
    })
    corroborated = adapter.dispatch("pamspec.create", {
        "scope_id": "workspace:q",
        "object_type": "claim",
        "canonical_content": {"s": "corroborated"},
        "validation_state": "corroborated",
        "actor": ACTOR, "provenance": PROV,
    })
    resp = adapter.dispatch("pamspec.query", {"scope_id": "workspace:q"})
    ids = {o["object_id"] for o in resp["result"]["objects"]}
    assert corroborated["result"]["object_id"] in ids


def test_inspect_history_returns_versions(adapter):
    r1 = adapter.dispatch("pamspec.create", {
        "scope_id": "workspace:h",
        "object_type": "claim",
        "canonical_content": {"s": "v1"},
        "actor": ACTOR, "provenance": PROV,
    })
    adapter.dispatch("pamspec.update", {
        "scope_id": "workspace:h",
        "object_id": r1["result"]["object_id"],
        "expected_version_id": r1["result"]["version_id"],
        "canonical_content": {"s": "v2"},
        "actor": ACTOR, "provenance": PROV,
    })
    resp = adapter.dispatch("pamspec.inspect_history", {
        "scope_id": "workspace:h",
        "object_id": r1["result"]["object_id"],
    })
    assert [v["sequence"] for v in resp["result"]["versions"]] == [1, 2]
