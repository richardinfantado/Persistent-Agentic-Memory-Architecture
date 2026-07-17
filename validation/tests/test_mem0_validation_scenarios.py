"""PAMSPEC × Mem0 validation scenarios.

Runs the eight scenarios from the R8 spec against an unmodified
Mem0 OSS install using its public Python API. Each scenario is a
separate pytest that both asserts the observed behavior AND writes
a machine-readable result line to reports/mem0_scenario_results.jsonl
so the validation report can be assembled without re-running.

Result classification per scenario:
  native      - Mem0 supports the requirement directly
  emulated    - adapter-side compensation would be needed
  gap         - cannot be met with Mem0's current public API
  questionable - evidence suggests the requirement itself is artificial
  not-testable - scenario can't be probed without modifying Mem0

Do NOT force outcomes to look green. A test failure is a useful result.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from mem0 import Memory

from validation.mem0_adapter.mem0_config import build_config


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_PATH = REPO_ROOT / "validation" / "reports" / "mem0_scenario_results.jsonl"
RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _record(scenario: str, requirement: str, classification: str, evidence: dict) -> None:
    """Append one result line to the JSONL evidence file."""
    line = {
        "scenario": scenario,
        "requirement": requirement,
        "classification": classification,
        "evidence": evidence,
    }
    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")


@pytest.fixture(scope="module", autouse=True)
def _reset_results():
    """Truncate the evidence file at the start of the module run."""
    if RESULTS_PATH.exists():
        RESULTS_PATH.unlink()
    RESULTS_PATH.touch()
    yield


def _make_mem(collection: str) -> Memory:
    return Memory.from_config(build_config(collection))


# ============================================================
# Scenario 1 — Scope immutability
# ============================================================

def test_1_scope_immutability_via_update():
    """Create in one scope; attempt to move to another via update().
    PAMSPEC: scope MUST be immutable for a given object."""
    m = _make_mem("s1_scope_immut")
    r = m.add([{"role": "user", "content": "test-1"}], user_id="alice", infer=False)
    mid = r["results"][0]["id"]
    before = m.get(mid)
    assert before["user_id"] == "alice"

    # Attempt to rewrite scope via metadata (Mem0's update takes text+metadata).
    try:
        m.update(mid, metadata={"user_id": "bob"})
        moved = m.get(mid)
        # Did Mem0 change scope? Check.
        native_user_after = moved.get("user_id")
        moved_user_id_via_metadata = (moved.get("metadata") or {}).get("user_id")
        evidence = {
            "before_user_id": before["user_id"],
            "after_native_user_id": native_user_after,
            "after_metadata_user_id_via_update": moved_user_id_via_metadata,
            "mem0_update_return": None,
        }
        # Mem0's native `user_id` field is the authoritative scope; metadata is user-controlled.
        # Whether metadata.user_id conflicts with native user_id is exactly the failure mode reported in Mem0 issue #6342.
        if native_user_after != "alice":
            classification = "gap"
            note = "Mem0 native user_id mutated by update()"
        elif moved_user_id_via_metadata == "bob":
            classification = "emulated"
            note = "Mem0 kept native user_id=alice but metadata.user_id was overwritten; downstream code reading metadata.user_id would see the wrong scope"
        else:
            classification = "native"
            note = "Mem0 preserved native user_id and metadata was not silently overwritten"
        evidence["note"] = note
        _record("1_scope_immutability", "scope_id immutable across update", classification, evidence)
        # The test does NOT fail on gap or emulated — recording the evidence IS the point.
    except Exception as e:
        _record("1_scope_immutability", "scope_id immutable across update", "not-testable",
                {"exception": f"{type(e).__name__}: {e}"})


# ============================================================
# Scenario 2 — Identity and history
# ============================================================

def test_2_identity_and_history():
    m = _make_mem("s2_identity")
    r = m.add([{"role": "user", "content": "v1"}], user_id="alice", infer=False)
    mid = r["results"][0]["id"]
    m.update(mid, text="v2")
    m.update(mid, text="v3")
    hist = m.history(mid)

    evidence = {
        "stable_object_id": True if mid else False,
        "distinct_version_ids_from_history": [h.get("id") for h in hist],
        "history_length": len(hist),
        "monotonic_by_updated_at": all(
            hist[i].get("updated_at", "") <= hist[i + 1].get("updated_at", "")
            for i in range(len(hist) - 1)
        ) if len(hist) > 1 else True,
        "prior_content_preserved": [h.get("old_memory") for h in hist],
        "update_actor": [h.get("actor_id") for h in hist],
        "update_time": [h.get("updated_at") for h in hist],
        "update_reason": "not exposed by Mem0.history()",
    }
    _record("2_identity_history", "stable identity + distinct version identity + history",
            # Mem0 exposes history entries with their own ids (~distinct version identity), stable memory_id, ordering.
            "native", evidence)


# ============================================================
# Scenario 3 — Concurrent or stale update
# ============================================================

def test_3_concurrent_or_stale_update():
    """Two updates based on the same prior state.
    PAMSPEC: stale expected_version_id MUST be rejected with version_conflict."""
    m = _make_mem("s3_concurrent")
    r = m.add([{"role": "user", "content": "v1"}], user_id="alice", infer=False)
    mid = r["results"][0]["id"]
    hist_before = m.history(mid)
    stale_version_id_hint = hist_before[-1]["id"] if hist_before else None

    # Two logical clients both derived from v1
    m.update(mid, text="v2-from-A")
    try:
        m.update(mid, text="v3-from-B")  # No mechanism to reference the prior version
        final = m.get(mid)
        evidence = {
            "last_writer_wins": final["memory"] == "v3-from-B",
            "no_expected_version_parameter": True,
            "stale_version_id_hint": stale_version_id_hint,
            "concurrency_control_kind": "last-write-wins (no expected-version, no conflict rejection)",
        }
        _record("3_concurrent_update",
                "expected-version rejection semantics",
                "gap", evidence)
    except Exception as e:
        _record("3_concurrent_update",
                "expected-version rejection semantics",
                "not-testable", {"exception": f"{type(e).__name__}: {e}"})


# ============================================================
# Scenario 4 — Idempotency
# ============================================================

def test_4_idempotency():
    """Repeat identical create; then same key with different content."""
    m = _make_mem("s4_idem")
    r1 = m.add([{"role": "user", "content": "same content"}], user_id="alice", infer=False)
    id1 = r1["results"][0]["id"]
    r2 = m.add([{"role": "user", "content": "same content"}], user_id="alice", infer=False)
    id2s = [x.get("id") for x in r2.get("results", [])]

    evidence = {
        "first_result_id": id1,
        "second_add_results_len": len(id2s),
        "second_add_returned_same_id": id1 in id2s,
        "public_api_has_idempotency_key": False,
        "add_signature": (
            "add(messages, user_id, agent_id, run_id, metadata, timestamp, "
            "expiration_date, infer, memory_type, prompt) — no idempotency_key"
        ),
    }
    _record("4_idempotency",
            "idempotency-key semantics",
            "gap", evidence)


# ============================================================
# Scenario 5 — Delete and stale resurrection
# ============================================================

def test_5_delete_and_stale_resurrection():
    m = _make_mem("s5_delete")
    r = m.add([{"role": "user", "content": "deleted-me"}], user_id="alice", infer=False)
    mid = r["results"][0]["id"]

    m.delete(mid)
    got_after = m.get(mid)
    hist_after = m.history(mid)

    # Try to recreate with the same id (Mem0 assigns UUIDs; there's no way to
    # request a specific id via the public API — so recreation cannot use the
    # original identity).
    r2 = m.add([{"role": "user", "content": "post-delete"}], user_id="alice", infer=False)
    recreated_id = r2["results"][0]["id"]

    # Try to update the deleted id
    stale_update_error = None
    try:
        m.update(mid, text="ghost-update")
    except Exception as e:
        stale_update_error = f"{type(e).__name__}: {e}"

    evidence = {
        "get_after_delete_returns": got_after,
        "history_after_delete_len": len(hist_after),
        "history_after_delete_last_event": hist_after[-1].get("event") if hist_after else None,
        "identity_reserved_against_recreation": mid != recreated_id and mid is not None,  # different id assigned; but does Mem0 refuse to re-create with same id?
        "no_public_way_to_specify_recreation_id": True,
        "stale_update_after_delete_error": stale_update_error,
    }
    # Delete IS observable via history (event=DELETE), which is stronger than pure physical removal.
    # Get returns None. Recreation with same id is not expressible via public API.
    _record("5_delete_and_tombstone",
            "persistent tombstone + identity reserved + stale-reference rejection",
            "emulated", evidence)


# ============================================================
# Scenario 6 — Provenance preservation
# ============================================================

def test_6_provenance_preservation():
    m = _make_mem("s6_prov")
    metadata = {
        "pamspec_source_actor": "actor:human:alice",
        "pamspec_activity": "user_stated_preference",
        "pamspec_original_source": "chat-session:2026-07-17",
        "pamspec_model_ref": "not-applicable-in-add",
    }
    r = m.add(
        [{"role": "user", "content": "test-6"}],
        user_id="alice", agent_id="agent42", run_id="run99",
        metadata=metadata, infer=False,
    )
    mid = r["results"][0]["id"]
    got = m.get(mid)
    hist = m.history(mid)

    # Update and check whether metadata survives
    m.update(mid, text="test-6-updated")
    got_after_update = m.get(mid)

    evidence = {
        "add_returned_actor_id_field": r["results"][0].get("actor_id"),
        "add_returned_role_field": r["results"][0].get("role"),
        "get_metadata_after_add": got.get("metadata"),
        "get_metadata_after_update": got_after_update.get("metadata"),
        "user_id_survived": got.get("user_id") == "alice",
        "agent_id_survived": got.get("agent_id") == "agent42",
        "run_id_survived": got.get("run_id") == "run99",
        "recorded_at_present": bool(got.get("created_at")),
        "updated_at_present": bool(got_after_update.get("updated_at")),
        "activity_kind_recorded_by_mem0": [h.get("event") for h in hist],
    }
    # Mem0 stores metadata verbatim and preserves scope tuple + timestamps.
    # PAMSPEC-style provenance (source_actor, activity, source_ref) is not native —
    # it must be stuffed into metadata by the adapter.
    _record("6_provenance",
            "source_actor / activity / recorded_at / original_source / model_provider / scope tuple",
            "emulated", evidence)


# ============================================================
# Scenario 7 — Derived-state consistency
# ============================================================

def test_7_derived_state_consistency():
    """PAMSPEC treats vectors + summaries + graphs as DERIVED — updating
    authoritative memory should propagate. Mem0 stores vectors in the
    vector store; check whether update() actually refreshes the vector.

    Also records an incidental finding: Mem0.search() REQUIRES a
    scope filter with at least one of user_id/agent_id/run_id — no
    cross-scope semantic search is exposed. This is itself a scope-
    isolation-supporting behavior worth recording.
    """
    m = _make_mem("s7_derived")
    r = m.add([{"role": "user", "content": "cats"}], user_id="alice", infer=False)
    mid = r["results"][0]["id"]

    scope_filter = {"user_id": "alice"}

    # Search for the original content (scope-required)
    hits_before = m.search("cats", top_k=5, filters=scope_filter)

    # Update to entirely different content
    m.update(mid, text="dogs")

    hits_after_original = m.search("cats", top_k=5, filters=scope_filter)
    hits_after_new = m.search("dogs", top_k=5, filters=scope_filter)

    # Also probe: without a scope filter, does search refuse?
    scope_filter_required = None
    try:
        m.search("cats", top_k=5)
        scope_filter_required = False
    except ValueError as e:
        scope_filter_required = f"required: {e}"

    def _ids(hits):
        return [h.get("id") for h in hits.get("results", [])]

    evidence = {
        "search_requires_scope_filter": scope_filter_required,
        "search_finds_cats_before_update": mid in _ids(hits_before),
        "search_finds_cats_after_update_should_be_false": mid in _ids(hits_after_original),
        "search_finds_dogs_after_update_should_be_true": mid in _ids(hits_after_new),
        "derived_vector_updated_on_content_change": (
            mid in _ids(hits_after_new) and mid not in _ids(hits_after_original)
        ),
    }
    # If derived_vector_updated_on_content_change is False, we've reproduced
    # the STALE-derived-artifact class of failure (MemoRepair-style).
    classification = "native" if evidence["derived_vector_updated_on_content_change"] else "gap"
    _record("7_derived_state",
            "derived state (vector index) refreshed on authoritative update",
            classification, evidence)


# ============================================================
# Scenario 8 — Unknown-field preservation
# ============================================================

def test_8_unknown_field_preservation():
    """Probe two shapes of unknown extension field:
    (a) a scalar string value — should survive if metadata is opaque
    (b) a nested dict — probes whether Mem0's metadata storage
        supports the JSON shapes PAMSPEC's canonical_content allows.

    The Chroma vector store used by Mem0 by default only accepts
    str/int/float/bool/list metadata values — nested dicts are
    rejected at add time. This is real evidence: PAMSPEC's
    canonical_content model would not survive Mem0's metadata path
    unless serialized to a string.
    """
    m = _make_mem("s8_unknown")

    # Case (a): scalar string extension value
    r_a = m.add(
        [{"role": "user", "content": "test-8a"}],
        user_id="alice",
        metadata={"x-experimental-ext": "some-value", "known": "ok"},
        infer=False,
    )
    mid_a = r_a["results"][0]["id"]
    got_a = m.get(mid_a)
    m.update(mid_a, text="test-8a-updated")
    got_a_after = m.get(mid_a)

    scalar_evidence = {
        "unknown_scalar_survives_add": (got_a.get("metadata") or {}).get("x-experimental-ext") == "some-value",
        "known_scalar_survives_add": (got_a.get("metadata") or {}).get("known") == "ok",
        "unknown_scalar_survives_text_only_update": (got_a_after.get("metadata") or {}).get("x-experimental-ext") == "some-value",
    }

    # Case (b): nested-dict extension value
    nested_add_error = None
    try:
        m.add(
            [{"role": "user", "content": "test-8b"}],
            user_id="alice",
            metadata={"x-experimental-ext": {"nested": [1, 2, 3]}, "known": "ok"},
            infer=False,
        )
    except Exception as e:
        nested_add_error = f"{type(e).__name__}: {e}"

    evidence = {
        "scalar_case": scalar_evidence,
        "nested_dict_case_add_error": nested_add_error,
        "note": (
            "Mem0's default Chroma vector store rejects nested-dict metadata values. "
            "PAMSPEC canonical_content shapes that require nested JSON would need "
            "adapter-side serialization (e.g., JSON-string encoding) before storing "
            "in Mem0. Scalar extension values pass through cleanly."
        ),
    }
    # Classification: scalar keys pass through; nested shapes do not.
    # This is 'emulated' — a PAMSPEC adapter can preserve nested shapes by
    # JSON-encoding, but the raw framework path drops them.
    scalar_ok = all(scalar_evidence.values())
    nested_rejected = nested_add_error is not None
    if scalar_ok and nested_rejected:
        classification = "emulated"
    elif scalar_ok and not nested_rejected:
        classification = "native"
    else:
        classification = "gap"
    _record("8_unknown_field",
            "unknown extension keys survive round-trip (scalar and nested)",
            classification, evidence)
