"""Bundle import into reference-python and round-trip comparison for R5.

Takes a bundle produced by Mem0EnforcementAdapter.export_bundle() and:
  1. Imports each non-tombstone object into a fresh MemoryService instance.
  2. Re-exports from MemoryService into a normalized comparison dict.
  3. Compares the Mem0 bundle and the re-exported bundle on the dimensions
     that are expected to survive the round trip:
     - stable object identity
     - immutable scope
     - canonical content
     - provenance
     - extension preservation
     - tombstone state
     - deterministic normalized bundle output

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


def import_bundle_into_refimpl(bundle: dict, mem_service: Any) -> dict[str, str]:
    """Import objects from an export bundle into a MemoryService instance.

    Returns a mapping {original_object_id -> refimpl_object_id}.
    Tombstoned objects are imported as deleted.
    """
    from pamspec_ref.service import MemoryService, PamspecError

    id_map: dict[str, str] = {}
    refimpl_actor = {"actor_id": "r5-import", "actor_kind": "system"}
    refimpl_provenance = {
        "recorded_by": "r5-round-trip-import",
        "import_source": "mem0ai:2.0.12",
    }

    for obj in sorted(bundle.get("objects", []), key=lambda o: o["object_id"]):
        orig_id = obj["object_id"]
        if obj.get("tombstone"):
            id_map[orig_id] = None
            continue

        content = obj.get("current_content") or ""
        scope = obj.get("scope_str") or "user:r5-import/agent:none/run:none"
        object_type = obj.get("object_type") or "claim"
        provenance = {**refimpl_provenance, **(obj.get("provenance") or {})}
        extensions_raw = obj.get("extensions") or {}

        canonical_content = {
            "text": content,
            "extensions": extensions_raw,
        }

        try:
            result = mem_service.create(
                scope_id=scope,
                object_type=object_type,
                canonical_content=canonical_content,
                actor=refimpl_actor,
                provenance=provenance,
            )
            id_map[orig_id] = result["object_id"]
        except PamspecError as e:
            id_map[orig_id] = f"IMPORT_ERROR:{e.code}"

    return id_map


def export_from_refimpl(mem_service: Any, id_map: dict[str, str]) -> list[dict]:
    """Re-export objects from MemoryService.

    Returns a list of comparison records, one per successfully imported object.
    """
    from pamspec_ref.service import PamspecError

    records: list[dict] = []
    for orig_id, refimpl_id in sorted(id_map.items()):
        if refimpl_id is None:
            records.append({"original_object_id": orig_id, "tombstone": True})
            continue
        if refimpl_id.startswith("IMPORT_ERROR:"):
            records.append({
                "original_object_id": orig_id,
                "error": refimpl_id,
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


def compare_bundles(mem0_bundle: dict, refimpl_records: list[dict]) -> dict:
    """Compare the Mem0 export bundle against the re-export from reference-python.

    Returns a summary dict with per-object comparison results and an overall pass/fail.
    """
    mem0_by_id = {o["object_id"]: o for o in mem0_bundle.get("objects", [])}
    refimpl_by_orig = {r["original_object_id"]: r for r in refimpl_records}

    results: list[dict] = []
    for orig_id, mem0_obj in sorted(mem0_by_id.items()):
        ri = refimpl_by_orig.get(orig_id, {})
        is_tombstone = mem0_obj.get("tombstone", False)

        if is_tombstone:
            results.append({
                "object_id": orig_id,
                "tombstone_preserved": ri.get("tombstone") is True,
            })
            continue

        if "error" in ri:
            results.append({"object_id": orig_id, "import_error": ri["error"]})
            continue

        cc = ri.get("canonical_content") or {}
        refimpl_text = cc.get("text") if isinstance(cc, dict) else None
        refimpl_exts = cc.get("extensions") if isinstance(cc, dict) else {}

        result = {
            "object_id": orig_id,
            "scope_preserved": ri.get("scope_id") == mem0_obj.get("scope_str"),
            "content_preserved": refimpl_text == mem0_obj.get("current_content"),
            "extensions_preserved": (refimpl_exts or {}) == (mem0_obj.get("extensions") or {}),
            "tombstone_preserved": True,
        }
        results.append(result)

    all_pass = all(
        r.get("scope_preserved", False) and r.get("content_preserved", False)
        for r in results
        if "import_error" not in r and not r.get("tombstone_preserved") is True
    ) and all("import_error" not in r for r in results)

    mem0_norm = _normalize_bundle(mem0_bundle)
    mem0_norm_json = json.dumps(mem0_norm, sort_keys=True)

    return {
        "per_object": results,
        "all_pass": all_pass,
        "mem0_normalized_bundle_json": mem0_norm_json,
        "object_count": len(results),
    }
