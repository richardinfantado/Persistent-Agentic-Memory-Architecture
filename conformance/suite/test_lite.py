"""Portable PAMSPEC-Lite behavioral conformance cases.

Every function named case_* MUST use only the Adapter interface,
never implementation internals. The runner discovers and executes
these against any Adapter.
"""

from __future__ import annotations

import json

from conformance.harness.adapter import Adapter, PamspecErrorLike, expect_error


ACTOR = {"actor_id": "actor:test:conformance", "actor_kind": "human"}
PROV = {
    "provenance_id": "prov:conformance:1",
    "actor": ACTOR,
    "activity": "created",
    "recorded_at": "2026-07-17T00:00:00Z",
}
SCOPE = "workspace:conformance"


def _mk(a: Adapter, **overrides):
    args = dict(
        scope_id=SCOPE,
        object_type="claim",
        canonical_content={"statement": "hello"},
        actor=ACTOR,
        provenance=PROV,
    )
    args.update(overrides)
    return a.create(**args)


def case_create_returns_object_and_version_ids(a: Adapter) -> None:
    r = _mk(a)
    assert "object_id" in r and r["object_id"]
    assert "version_id" in r and r["version_id"]
    assert r.get("sequence") == 1


def case_read_returns_current_envelope(a: Adapter) -> None:
    r = _mk(a)
    env = a.read(scope_id=SCOPE, object_id=r["object_id"])
    assert env["object_id"] == r["object_id"]
    assert env["version_id"] == r["version_id"]
    assert env["object_type"] == "claim"
    assert env["scope_id"] == SCOPE


def case_read_specific_version(a: Adapter) -> None:
    r1 = _mk(a)
    r2 = a.update(
        scope_id=SCOPE, object_id=r1["object_id"],
        expected_version_id=r1["version_id"],
        canonical_content={"statement": "v2"},
        actor=ACTOR, provenance=PROV,
    )
    env_v1 = a.read(scope_id=SCOPE, object_id=r1["object_id"], version_id=r1["version_id"])
    assert env_v1["version_id"] == r1["version_id"]
    env_v2 = a.read(scope_id=SCOPE, object_id=r1["object_id"], version_id=r2["version_id"])
    assert env_v2["version_id"] == r2["version_id"]


def case_update_creates_new_version(a: Adapter) -> None:
    r1 = _mk(a)
    r2 = a.update(
        scope_id=SCOPE, object_id=r1["object_id"],
        expected_version_id=r1["version_id"],
        canonical_content={"statement": "v2"},
        actor=ACTOR, provenance=PROV,
    )
    assert r2["object_id"] == r1["object_id"]
    assert r2["version_id"] != r1["version_id"]
    assert r2["sequence"] == 2


def case_stale_expected_version_raises_version_conflict(a: Adapter) -> None:
    r1 = _mk(a)
    a.update(
        scope_id=SCOPE, object_id=r1["object_id"],
        expected_version_id=r1["version_id"],
        canonical_content={"statement": "v2"},
        actor=ACTOR, provenance=PROV,
    )
    with expect_error("version_conflict") as box:
        a.update(
            scope_id=SCOPE, object_id=r1["object_id"],
            expected_version_id=r1["version_id"],
            canonical_content={"statement": "v3"},
            actor=ACTOR, provenance=PROV,
        )
    assert box["error"].retryable is True


def case_missing_object_raises_object_not_found(a: Adapter) -> None:
    with expect_error("object_not_found"):
        a.read(scope_id=SCOPE, object_id="mem:does:not:exist")


def case_scope_isolation(a: Adapter) -> None:
    r = _mk(a)
    with expect_error("object_not_found"):
        a.read(scope_id="workspace:other-scope", object_id=r["object_id"])


def case_idempotent_create_returns_same_result(a: Adapter) -> None:
    r1 = _mk(a, idempotency_key="conformance-key-A")
    r2 = _mk(a, idempotency_key="conformance-key-A")
    assert r1["object_id"] == r2["object_id"]
    assert r1["version_id"] == r2["version_id"]


def case_idempotent_key_reuse_with_different_body_fails(a: Adapter) -> None:
    _mk(a, idempotency_key="conformance-key-B", canonical_content={"statement": "one"})
    with expect_error("duplicate_operation"):
        _mk(a, idempotency_key="conformance-key-B", canonical_content={"statement": "two"})


def case_delete_creates_tombstone_and_blocks_default_read(a: Adapter) -> None:
    r = _mk(a)
    a.delete(
        scope_id=SCOPE, object_id=r["object_id"],
        expected_version_id=r["version_id"],
        actor=ACTOR, provenance=PROV,
    )
    with expect_error("object_deleted"):
        a.read(scope_id=SCOPE, object_id=r["object_id"])


def case_lifecycle_transition_active_to_archived(a: Adapter) -> None:
    r = _mk(a)
    res = a.transition(
        scope_id=SCOPE, object_id=r["object_id"],
        expected_version_id=r["version_id"],
        dimension="lifecycle", target_state="archived",
        actor=ACTOR, provenance=PROV,
    )
    assert res["envelope"]["lifecycle_state"] == "archived"
    assert res["sequence"] == 2


def case_invalid_lifecycle_transition_rejected(a: Adapter) -> None:
    r = _mk(a, lifecycle_state="archived")
    with expect_error("invalid_state_transition"):
        a.transition(
            scope_id=SCOPE, object_id=r["object_id"],
            expected_version_id=r["version_id"],
            dimension="lifecycle", target_state="superseded",
            actor=ACTOR, provenance=PROV,
        )


def case_query_default_filters_apply(a: Adapter) -> None:
    unverified = _mk(a, canonical_content={"s": "u"})
    corroborated = _mk(a, canonical_content={"s": "c"}, validation_state="corroborated")
    default = a.query(scope_id=SCOPE)
    ids = {r["object_id"] for r in default}
    assert corroborated["object_id"] in ids
    assert unverified["object_id"] not in ids


def case_history_is_monotonic(a: Adapter) -> None:
    r1 = _mk(a)
    a.update(
        scope_id=SCOPE, object_id=r1["object_id"],
        expected_version_id=r1["version_id"],
        canonical_content={"s": "v2"},
        actor=ACTOR, provenance=PROV,
    )
    hist = a.history(scope_id=SCOPE, object_id=r1["object_id"])
    seqs = [v["sequence"] for v in hist]
    assert seqs == sorted(set(seqs)), f"sequences must be strictly increasing, got {seqs}"
    assert len(seqs) == 2


def case_unknown_extension_fields_preserved_on_read(a: Adapter) -> None:
    """An extension field placed inside canonical_content MUST survive
    a round-trip through create + read. Implementations that strip
    unknown keys break forward compatibility with future PAMSPEC
    extensions.
    """
    r = _mk(a, canonical_content={"statement": "hi", "x-experimental-ext": {"nested": [1, 2, 3]}})
    env = a.read(scope_id=SCOPE, object_id=r["object_id"])
    cc = env["canonical_content"]
    assert "x-experimental-ext" in cc, f"unknown extension key was stripped; got keys {list(cc)}"
    assert cc["x-experimental-ext"] == {"nested": [1, 2, 3]}, (
        f"unknown extension value corrupted; got {cc['x-experimental-ext']!r}"
    )


def case_scope_mutation_rejected(a: Adapter) -> None:
    """CR-2: scope MUST NOT change after creation.

    A valid update in the correct scope MUST preserve the scope field
    in the stored envelope. An update addressed to a different scope
    MUST NOT succeed — scope isolation guarantees the object is
    invisible outside its assigned scope, so the error MUST be either
    object_not_found (object invisible in the other scope) or
    scope_immutable (explicit scope-mutation detection).
    """
    r1 = _mk(a)
    r2 = a.update(
        scope_id=SCOPE, object_id=r1["object_id"],
        expected_version_id=r1["version_id"],
        canonical_content={"statement": "v2"},
        actor=ACTOR, provenance=PROV,
    )
    # scope must be unchanged in the stored envelope after a valid update
    env = a.read(scope_id=SCOPE, object_id=r1["object_id"])
    assert env["scope_id"] == SCOPE, (
        f"scope changed after update; expected {SCOPE!r}, got {env['scope_id']!r}"
    )
    # cross-scope update MUST be rejected
    try:
        a.update(
            scope_id="workspace:other-scope",
            object_id=r1["object_id"],
            expected_version_id=r2["version_id"],
            canonical_content={"statement": "v3"},
            actor=ACTOR, provenance=PROV,
        )
        raise AssertionError(
            "cross-scope update must be rejected; no error was raised"
        )
    except PamspecErrorLike as exc:
        assert exc.code in ("object_not_found", "scope_immutable"), (
            f"cross-scope update raised unexpected error code {exc.code!r}; "
            f"expected object_not_found or scope_immutable"
        )


def case_bundle_output_is_deterministic(a: Adapter) -> None:
    """CR-7 (provisional): serializing the same object set MUST produce
    identical normalized output on repeated calls.

    Tested by: creating N objects, querying twice, sorting both result
    sets by object_id, and asserting the normalized JSON representations
    are byte-for-byte identical. Non-deterministic fields (e.g. timestamps)
    that vary between calls would cause this assertion to fail.
    """
    for i in range(3):
        _mk(a, canonical_content={"item": i}, validation_state="corroborated")

    def _normalize(results: list) -> str:
        return json.dumps(
            sorted(results, key=lambda r: r["object_id"]),
            sort_keys=True,
            ensure_ascii=True,
        )

    run1 = _normalize(a.query(scope_id=SCOPE))
    run2 = _normalize(a.query(scope_id=SCOPE))
    assert run1 == run2, (
        "repeated query+sort+serialize produced different output; "
        "implementation must not introduce non-deterministic fields "
        "such as per-call timestamps in query results"
    )
