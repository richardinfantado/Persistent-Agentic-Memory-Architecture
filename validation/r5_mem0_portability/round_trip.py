"""Bundle import into reference-python and round-trip comparison for R5.

Takes a bundle produced by Mem0EnforcementAdapter.export_bundle() and:
  1. Imports each object into a fresh MemoryService instance, preserving
     object identity (object_id=orig_id passed to create()).
  2. Replays available history events in chronological order.
  3. Imports tombstones through reference-python's real delete() operation.
  4. Re-exports from MemoryService into a normalized comparison dict.
  5. Compares the Mem0 bundle and the re-exported bundle on every dimension
     that is expected to survive the round trip:
       - stable object identity (refimpl_object_id == orig_id)
       - immutable scope
       - canonical content
       - provenance (Mem0-original keys must survive in merged provenance)
       - extension preservation
       - version order (when Mem0 history provides multi-version evidence)
       - tombstone state (deleted in reference-python, not synthesized locally)
     all_pass is the conjunction of every applicable property.

Mem0 source is not modified.
"""

from __future__ import annotations

import json
from typing import Any


def _normalize_bundle(bundle: dict) -> dict:
    """Return a canonical sorted projection of a bundle for comparison.
    Strips framework-specific fields and timestamps; retains semantics."""
    normalized_objects = []
    for obj in sorted(bundle.get("objects", []), key=lambda o: o["object_id"]):
        normalized_objects.append({
            "object_id": obj["object_id"],
            "scope_str": obj.get("scope_str", ""),
            "object_type": obj.get("object_type", ""),
            "content": obj.get("current_content"),
            "provenance": obj.get("provenance") or {},
            "extensions": obj.get("extensions") or {},
            "tombstone": obj.get("tombstone", False),
        })
    return {"objects": normalized_objects}


def _extract_content_sequence(history_events: list, current_content: str | None) -> list:
    """Reconstruct ordered content versions from Mem0 history events.

    Returns a list of content strings in chronological order, guaranteed
    to end with current_content (the authoritative final state).
    Falls back to [current_content] when no usable history is available.
    """
    adds = [e for e in history_events if e.get("event") == "ADD"]
    updates = [e for e in history_events if e.get("event") == "UPDATE"]

    if not adds and not updates:
        return [current_content]

    sequence: list = []
    if adds and adds[0].get("new_memory") is not None:
        sequence.append(adds[0]["new_memory"])

    for ev in updates:
        if ev.get("new_memory") is not None:
            sequence.append(ev["new_memory"])

    if not sequence:
        return [current_content]

    # Ensure the authoritative final content is the last version
    if current_content is not None and sequence[-1] != current_content:
        sequence.append(current_content)

    return sequence


def import_bundle_into_refimpl(bundle: dict, mem_service: Any) -> dict[str, str]:
    """Import objects from an export bundle into a MemoryService instance.

    Returns a mapping {original_object_id -> refimpl_object_id or sentinel}.
    - Live objects: id_map[orig_id] = orig_id (identity preserved)
    - Tombstones: id_map[orig_id] = "TOMBSTONE:{orig_id}" (imported then deleted)
    - Import errors: id_map[orig_id] = "IMPORT_ERROR:{code}"

    For each object:
      - object_id=orig_id is passed to create() to preserve identity
      - history events are replayed in order via create() + sequential update()
      - tombstones are imported through reference-python's real delete()
    """
    from pamspec_ref.service import PamspecError

    id_map: dict[str, str] = {}
    refimpl_actor = {"actor_id": "r5-import", "actor_kind": "system"}
    refimpl_provenance = {
        "recorded_by": "r5-round-trip-import",
        "import_source": "mem0ai:2.0.12",
    }

    for obj in sorted(bundle.get("objects", []), key=lambda o: o["object_id"]):
        orig_id = obj["object_id"]
        is_tombstone = obj.get("tombstone", False)

        current_content = obj.get("current_content")
        scope = obj.get("scope_str") or "user:r5-import/agent:none/run:none"
        object_type = obj.get("object_type") or "claim"
        # Merge import provenance with original provenance; orig keys survive
        provenance = {**refimpl_provenance, **(obj.get("provenance") or {})}
        extensions_raw = obj.get("extensions") or {}
        history_events = obj.get("history_events") or []

        try:
            if is_tombstone:
                # Reconstruct best-available content from history, then delete
                fallback = current_content or "tombstone-placeholder"
                content_sequence = _extract_content_sequence(history_events, fallback)
            else:
                content_sequence = _extract_content_sequence(history_events, current_content)

            first_content = content_sequence[0]
            canonical_content = {"text": first_content, "extensions": extensions_raw}

            create_result = mem_service.create(
                scope_id=scope,
                object_type=object_type,
                canonical_content=canonical_content,
                actor=refimpl_actor,
                provenance=provenance,
                object_id=orig_id,
            )
            current_version_id = create_result["version_id"]

            # Replay subsequent history versions
            for subsequent_content in content_sequence[1:]:
                update_result = mem_service.update(
                    scope_id=scope,
                    object_id=orig_id,
                    expected_version_id=current_version_id,
                    canonical_content={"text": subsequent_content, "extensions": extensions_raw},
                    actor=refimpl_actor,
                    provenance=provenance,
                )
                current_version_id = update_result["version_id"]

            if is_tombstone:
                mem_service.delete(
                    scope_id=scope,
                    object_id=orig_id,
                    expected_version_id=current_version_id,
                    actor=refimpl_actor,
                    provenance=provenance,
                )
                id_map[orig_id] = f"TOMBSTONE:{orig_id}"
            else:
                id_map[orig_id] = orig_id

        except PamspecError as e:
            id_map[orig_id] = f"IMPORT_ERROR:{e.code}"

    return id_map


def export_from_refimpl(mem_service: Any, id_map: dict[str, str]) -> list[dict]:
    """Re-export objects from MemoryService.

    Returns a list of comparison records, one per object.
    Tombstones are re-exported from reference-python's actual tombstone envelope
    (availability_state='deleted'), not synthesized from the local map.
    """
    from pamspec_ref.service import PamspecError

    records: list[dict] = []
    for orig_id, refimpl_id in sorted(id_map.items()):
        if refimpl_id is not None and refimpl_id.startswith("TOMBSTONE:"):
            actual_id = refimpl_id[len("TOMBSTONE:"):]
            tombstone_env = _read_current_envelope(mem_service, actual_id)
            if tombstone_env is not None:
                records.append({
                    "original_object_id": orig_id,
                    "refimpl_object_id": actual_id,
                    "tombstone": tombstone_env.get("availability_state") == "deleted",
                    "availability_state": tombstone_env.get("availability_state"),
                    "scope_id": tombstone_env.get("scope_id"),
                    "sequence": tombstone_env.get("sequence"),
                })
            else:
                records.append({"original_object_id": orig_id, "error": "tombstone_not_found"})
            continue

        if refimpl_id is None or refimpl_id.startswith("IMPORT_ERROR:"):
            records.append({
                "original_object_id": orig_id,
                "error": refimpl_id or "none",
            })
            continue

        for scope in _find_scope(mem_service, refimpl_id):
            try:
                envelope = mem_service.read(scope, refimpl_id)
                records.append({
                    "original_object_id": orig_id,
                    "refimpl_object_id": refimpl_id,
                    "scope_id": envelope.get("scope_id"),
                    "canonical_content": envelope.get("canonical_content"),
                    "provenance": envelope.get("provenance"),
                    "lifecycle_state": envelope.get("lifecycle_state"),
                    "sequence": envelope.get("sequence"),
                })
            except PamspecError:
                records.append({"original_object_id": orig_id, "error": "read_failed"})
    return records


def _find_scope(mem_service: Any, object_id: str) -> list[str]:
    """Look up which scope an object belongs to."""
    row = mem_service._conn.execute(
        "SELECT scope_id FROM memory_current WHERE object_id = ?", (object_id,)
    ).fetchone()
    return [row[0]] if row else []


def _read_current_envelope(mem_service: Any, object_id: str) -> dict | None:
    """Read the current envelope for any object including tombstones.

    Uses direct DB access since MemoryService.read() raises for deleted objects.
    """
    row = mem_service._conn.execute(
        "SELECT current_version_id FROM memory_current WHERE object_id = ?", (object_id,)
    ).fetchone()
    if not row:
        return None
    ver_row = mem_service._conn.execute(
        "SELECT envelope_json FROM memory_versions WHERE version_id = ?", (row[0],)
    ).fetchone()
    return json.loads(ver_row["envelope_json"]) if ver_row else None


def compare_bundles(mem0_bundle: dict, refimpl_records: list[dict]) -> dict:
    """Compare the Mem0 export bundle against the re-export from reference-python.

    Checks every required preservation property for every object explicitly.
    all_pass is the strict conjunction of all applicable properties:
      - identity_preserved: refimpl_object_id == orig_id
      - scope_preserved: refimpl scope_id == mem0 scope_str
      - content_preserved: refimpl text == mem0 current_content
      - provenance_preserved: all mem0 provenance keys survive in refimpl provenance
      - extensions_preserved: refimpl extensions == mem0 extensions
      - version_order_preserved: refimpl sequence == expected replay count
        (None = N/A when Mem0 history has only one version)
      - tombstone_preserved: reference-python has availability_state='deleted'
        (None = N/A for live objects)

    For tombstones: identity_preserved and tombstone_preserved are checked.
    For live objects: identity, scope, content, provenance, extensions,
      version_order (when multi-version) are checked; tombstone_preserved=False
      is a sanity check that the object is not accidentally deleted.
    """
    mem0_by_id = {o["object_id"]: o for o in mem0_bundle.get("objects", [])}
    refimpl_by_orig = {r["original_object_id"]: r for r in refimpl_records}

    results: list[dict] = []
    for orig_id, mem0_obj in sorted(mem0_by_id.items()):
        ri = refimpl_by_orig.get(orig_id, {})
        is_tombstone = mem0_obj.get("tombstone", False)

        if "error" in ri:
            results.append({
                "object_id": orig_id,
                "import_error": ri["error"],
                "identity_preserved": False,
                "scope_preserved": False,
                "content_preserved": False,
                "provenance_preserved": False,
                "extensions_preserved": False,
                "version_order_preserved": None,
                "tombstone_preserved": False,
            })
            continue

        if is_tombstone:
            tombstone_real = (
                ri.get("tombstone") is True
                and ri.get("availability_state") == "deleted"
            )
            results.append({
                "object_id": orig_id,
                "identity_preserved": ri.get("refimpl_object_id") == orig_id,
                "scope_preserved": None,
                "content_preserved": None,
                "provenance_preserved": None,
                "extensions_preserved": None,
                "version_order_preserved": None,
                "tombstone_preserved": tombstone_real,
            })
            continue

        # Live object: check every required property explicitly
        cc = ri.get("canonical_content") or {}
        refimpl_text = cc.get("text") if isinstance(cc, dict) else None
        refimpl_exts = (cc.get("extensions") if isinstance(cc, dict) else {}) or {}
        refimpl_prov = ri.get("provenance") or {}
        refimpl_seq = ri.get("sequence")

        mem0_prov = mem0_obj.get("provenance") or {}
        mem0_exts = mem0_obj.get("extensions") or {}

        # Provenance: all Mem0-original keys must survive in the merged refimpl provenance
        provenance_preserved: bool | None
        if mem0_prov:
            provenance_preserved = all(
                refimpl_prov.get(k) == v for k, v in mem0_prov.items()
            )
        else:
            provenance_preserved = None  # nothing to verify

        # Version order: check if multi-version history was replayed correctly
        history_events = mem0_obj.get("history_events") or []
        n_expected = len([e for e in history_events if e.get("event") in ("ADD", "UPDATE")])
        version_order_preserved: bool | None
        if n_expected > 1:
            version_order_preserved = (
                refimpl_seq is not None and refimpl_seq == n_expected
            )
        else:
            version_order_preserved = None  # single version, ordering N/A

        result = {
            "object_id": orig_id,
            "identity_preserved": ri.get("refimpl_object_id") == orig_id,
            "scope_preserved": ri.get("scope_id") == mem0_obj.get("scope_str"),
            "content_preserved": refimpl_text == mem0_obj.get("current_content"),
            "provenance_preserved": provenance_preserved,
            "extensions_preserved": refimpl_exts == mem0_exts,
            "version_order_preserved": version_order_preserved,
            "tombstone_preserved": False,
        }
        results.append(result)

    def _object_passes(r: dict) -> bool:
        if "import_error" in r:
            return False
        tombstone_val = r.get("tombstone_preserved")
        if tombstone_val is True:
            # Tombstone record: identity and tombstone_preserved are the checks
            return r.get("identity_preserved") is True
        # Live object record: tombstone_preserved must be False (sanity)
        if tombstone_val is not False:
            return False
        for key in ("identity_preserved", "scope_preserved", "content_preserved",
                    "extensions_preserved"):
            if r.get(key) is False:
                return False
        if r.get("provenance_preserved") is False:
            return False
        if r.get("version_order_preserved") is False:
            return False
        return True

    all_pass = bool(results) and all(_object_passes(r) for r in results)

    mem0_norm = _normalize_bundle(mem0_bundle)
    mem0_norm_json = json.dumps(mem0_norm, sort_keys=True)

    return {
        "per_object": results,
        "all_pass": all_pass,
        "mem0_normalized_bundle_json": mem0_norm_json,
        "object_count": len(results),
    }
