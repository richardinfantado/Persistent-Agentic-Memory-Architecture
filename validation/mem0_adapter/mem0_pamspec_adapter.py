"""Mem0 subprocess adapter — R7 protocol.

Maps PAMSPEC operations onto Mem0's public API. Records every
operation's classification (native / adapter-emulated / gap /
questionable / not-testable) via stderr diagnostic lines so the
validation report can be assembled without re-running.

Public API used (Mem0 2.0.12):
    Memory.add(messages, user_id, agent_id, run_id, metadata, infer)
    Memory.get(memory_id)
    Memory.get_all(filters, top_k, show_expired)
    Memory.update(memory_id, text, metadata)
    Memory.history(memory_id)
    Memory.delete(memory_id)

Scope model: PAMSPEC's opaque `scope_id` string is parsed with a
permissive convention. Accepted forms:
    "user:<u>"                   -> user_id=<u>
    "user:<u>/agent:<a>"         -> user_id=<u>, agent_id=<a>
    "user:<u>/agent:<a>/run:<r>" -> plus run_id=<r>
    anything else                -> user_id=scope_id (fallback)

The adapter never modifies Mem0 source. When a PAMSPEC requirement
cannot be represented natively, the adapter either emulates
(recording the emulation as a diagnostic) or returns a structured
error with code = "framework_gap".

Diagnostics on stderr have the shape:
    [DIAG] <request_id> <operation> <bucket> <one-line summary>
where bucket is one of native | emulated | gap | questionable | not-testable.
"""

from __future__ import annotations

import json
import sys
import uuid
from typing import Any

from mem0 import Memory

# Local import (same directory when run as -m module)
from validation.mem0_adapter.mem0_config import build_config  # type: ignore


PROTOCOL_VERSION = 1


def _emit(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")
    sys.stdout.flush()


def _diag(request_id: str, operation: str, bucket: str, summary: str) -> None:
    sys.stderr.write(f"[DIAG] {request_id} {operation} {bucket} {summary}\n")
    sys.stderr.flush()


def _err(request_id: str, code: str, message: str, retryable: bool = False, **details: Any) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": details,
        },
    }


def _parse_scope(scope_id: str) -> dict[str, str]:
    """Adapter convention. Never fails; unknown forms fall back to user_id=scope_id."""
    parts = {}
    for segment in scope_id.split("/"):
        if ":" not in segment:
            continue
        key, _, value = segment.partition(":")
        if key in ("user", "agent", "run") and value:
            parts[f"{key}_id"] = value
    if not parts:
        parts["user_id"] = scope_id
    return parts


class Mem0Adapter:
    def __init__(self):
        self._mem: dict[str, Memory] = {}  # keyed by collection name (~ scope tenant)
        # Track adapter-side sequences per memory_id (Mem0 has no monotonic sequence).
        self._seq: dict[str, int] = {}
        # Track scope claimed at create time (Mem0 stores it but the adapter
        # enforces stability separately, since Mem0's update() can mutate metadata).
        self._claimed_scope: dict[str, str] = {}

    def _client(self, scope_id: str) -> Memory:
        collection = "pamspec_" + str(abs(hash(scope_id)) % (10 ** 8))
        if collection not in self._mem:
            self._mem[collection] = Memory.from_config(build_config(collection))
        return self._mem[collection]

    # ---- operations ----

    def create(self, request_id: str, args: dict[str, Any]) -> dict[str, Any]:
        scope_id = args.get("scope_id", "")
        canonical_content = args.get("canonical_content", {})
        actor = args.get("actor", {})
        # Serialize canonical_content into Mem0's "messages" surface.
        # Mem0 expects string OR list-of-messages; use the JSON string form
        # so arbitrary content shapes survive.
        text = json.dumps(canonical_content, sort_keys=True)
        scope_kwargs = _parse_scope(scope_id)
        # Mem0's default vector store (Chroma) rejects nested-dict metadata
        # values (see validation scenario 8). Adapter serializes nested
        # PAMSPEC pieces to JSON strings so they can round-trip.
        provenance = args.get("provenance")
        metadata = {
            "pamspec_scope_id": scope_id,
            "pamspec_actor_id": actor.get("actor_id"),
            "pamspec_actor_json": json.dumps(actor, sort_keys=True) if actor else None,
            "pamspec_provenance_json": json.dumps(provenance, sort_keys=True) if provenance else None,
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        try:
            client = self._client(scope_id)
            result = client.add([{"role": "user", "content": text}], infer=False, metadata=metadata, **scope_kwargs)
        except Exception as e:
            _diag(request_id, "create", "gap", f"Mem0 add raised: {type(e).__name__}: {e}")
            return _err(request_id, "internal_error", f"mem0.add raised: {type(e).__name__}: {e}")
        # Mem0.add returns {"results": [{"id": ..., "memory": ..., "event": "ADD"}]}
        results = result.get("results", []) if isinstance(result, dict) else []
        if not results:
            _diag(request_id, "create", "not-testable", "Mem0 add returned no results (infer=False may drop content)")
            return _err(request_id, "invalid_request", "mem0.add produced no memory")
        first = results[0]
        memory_id = first.get("id")
        self._seq[memory_id] = 1
        self._claimed_scope[memory_id] = scope_id
        _diag(request_id, "create", "native", f"created memory {memory_id!r} in scope {scope_id!r}")
        envelope = {
            "spec_version": "0.1.0-draft",
            "object_id": memory_id,
            "version_id": memory_id,   # Mem0 has no distinct version identity — same as object id
            "sequence": 1,
            "scope_id": scope_id,
            "object_type": args.get("object_type", "observation"),
            "canonical_content": canonical_content,
            "actor": actor,
            "provenance": args.get("provenance"),
        }
        return {
            "request_id": request_id,
            "result": {
                "object_id": memory_id,
                "version_id": memory_id,
                "sequence": 1,
                "envelope": envelope,
                # Adapter honesty flag — no distinct version identity in Mem0.
                "_adapter_notes": {
                    "version_id_is_object_id": True,
                    "reason": "Mem0 has no distinct version identity; adapter reports object_id as version_id and records sequence via adapter-side counter.",
                },
            },
        }

    def read(self, request_id: str, args: dict[str, Any]) -> dict[str, Any]:
        scope_id = args.get("scope_id", "")
        object_id = args["object_id"]
        try:
            client = self._client(scope_id)
            mem = client.get(object_id)
        except Exception as e:
            return _err(request_id, "object_not_found", f"mem0.get raised: {type(e).__name__}: {e}")
        if mem is None:
            return _err(request_id, "object_not_found", "not found")
        # Reconstruct canonical_content from the stored JSON string, if possible.
        raw = mem.get("memory") if isinstance(mem, dict) else None
        try:
            canonical_content = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            canonical_content = raw
        # Enforce scope isolation at the ADAPTER level — Mem0 does not.
        claimed = self._claimed_scope.get(object_id) or (mem.get("metadata", {}) or {}).get("pamspec_scope_id")
        if claimed and claimed != scope_id:
            _diag(request_id, "read", "emulated", f"scope isolation enforced by adapter; Mem0 would have returned across scopes")
            return _err(request_id, "object_not_found", "scope isolation enforced by adapter")
        envelope = {
            "spec_version": "0.1.0-draft",
            "object_id": object_id,
            "version_id": object_id,
            "sequence": self._seq.get(object_id, 1),
            "scope_id": scope_id,
            "canonical_content": canonical_content,
            "_mem0_metadata": mem.get("metadata"),
        }
        _diag(request_id, "read", "native", f"read {object_id!r}")
        return {"request_id": request_id, "result": envelope}

    def update(self, request_id: str, args: dict[str, Any]) -> dict[str, Any]:
        scope_id = args.get("scope_id", "")
        object_id = args["object_id"]
        expected_version_id = args.get("expected_version_id")
        canonical_content = args.get("canonical_content")
        # Adapter-side expected-version check. Mem0 has no native concurrency.
        current_version = object_id  # since version_id == object_id in this adapter
        if expected_version_id is not None and expected_version_id != current_version:
            _diag(request_id, "update", "emulated", "expected-version check enforced by adapter; Mem0 has no native equivalent")
            return _err(request_id, "version_conflict",
                        f"expected {expected_version_id!r} != current {current_version!r}",
                        retryable=True,
                        expected_version_id=expected_version_id,
                        current_version_id=current_version)
        # Serialize new content.
        text = json.dumps(canonical_content, sort_keys=True)
        client = self._client(scope_id)
        try:
            client.update(object_id, text=text)
        except Exception as e:
            return _err(request_id, "internal_error", f"mem0.update raised: {type(e).__name__}: {e}")
        self._seq[object_id] = self._seq.get(object_id, 1) + 1
        _diag(request_id, "update", "emulated",
              f"Mem0 mutates in place; adapter increments sequence to {self._seq[object_id]}")
        envelope = {
            "spec_version": "0.1.0-draft",
            "object_id": object_id,
            "version_id": object_id,
            "sequence": self._seq[object_id],
            "scope_id": scope_id,
            "canonical_content": canonical_content,
        }
        return {
            "request_id": request_id,
            "result": {
                "object_id": object_id,
                "version_id": object_id,
                "sequence": self._seq[object_id],
                "envelope": envelope,
                "_adapter_notes": {
                    "expected_version_check": "adapter-emulated",
                    "distinct_version_identity": False,
                },
            },
        }

    def history(self, request_id: str, args: dict[str, Any]) -> dict[str, Any]:
        scope_id = args.get("scope_id", "")
        object_id = args["object_id"]
        client = self._client(scope_id)
        try:
            hist = client.history(object_id)
        except Exception as e:
            return _err(request_id, "internal_error", f"mem0.history raised: {type(e).__name__}: {e}")
        _diag(request_id, "history", "native", f"{len(hist) if hist else 0} history entries")
        return {"request_id": request_id, "result": {"history": hist}}

    def delete(self, request_id: str, args: dict[str, Any]) -> dict[str, Any]:
        scope_id = args.get("scope_id", "")
        object_id = args["object_id"]
        client = self._client(scope_id)
        try:
            client.delete(object_id)
        except Exception as e:
            return _err(request_id, "internal_error", f"mem0.delete raised: {type(e).__name__}: {e}")
        _diag(request_id, "delete", "native", f"deleted {object_id!r} (physical removal, no tombstone)")
        return {
            "request_id": request_id,
            "result": {
                "object_id": object_id,
                "_adapter_notes": {
                    "deletion_kind": "physical_remove",
                    "tombstone_preserved": False,
                    "identity_reserved_against_recreation": False,
                },
            },
        }

    def query(self, request_id: str, args: dict[str, Any]) -> dict[str, Any]:
        scope_id = args.get("scope_id", "")
        client = self._client(scope_id)
        scope_kwargs = _parse_scope(scope_id)
        try:
            result = client.get_all(filters=scope_kwargs)
        except Exception as e:
            return _err(request_id, "internal_error", f"mem0.get_all raised: {type(e).__name__}: {e}")
        results = result.get("results", []) if isinstance(result, dict) else result
        _diag(request_id, "query", "native", f"{len(results)} memories")
        return {"request_id": request_id, "result": {"objects": results, "count": len(results)}}


OPERATIONS = {
    "create": lambda a, rid, args: a.create(rid, args),
    "read": lambda a, rid, args: a.read(rid, args),
    "update": lambda a, rid, args: a.update(rid, args),
    "history": lambda a, rid, args: a.history(rid, args),
    "delete": lambda a, rid, args: a.delete(rid, args),
    "query": lambda a, rid, args: a.query(rid, args),
}


def main() -> int:
    _emit({
        "type": "hello",
        "protocol_version": PROTOCOL_VERSION,
        "adapter": {"name": "mem0-pamspec-adapter", "version": "0.1.0"},
        "implementation": {"name": "mem0ai", "version": "2.0.12"},
        "spec_commit": "",
        "profiles_supported": ["PAMSPEC-Lite"],  # honest — only the CRUD subset is covered
    })
    adapter = Mem0Adapter()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request_id = "unknown"
        try:
            req = json.loads(line)
            request_id = req.get("request_id", "unknown")
            op = req.get("operation")
            args = req.get("arguments") or {}
            handler = OPERATIONS.get(op)
            if handler is None:
                _diag(request_id, op or "?", "not-testable", f"unknown operation {op!r}")
                _emit(_err(request_id, "invalid_request", f"unknown operation {op!r}"))
                continue
            _emit(handler(adapter, request_id, args))
        except json.JSONDecodeError as e:
            _emit(_err(request_id, "invalid_request", f"invalid JSON: {e}"))
        except Exception as e:
            import traceback
            sys.stderr.write(f"[ERROR] {request_id} {type(e).__name__}: {e}\n{traceback.format_exc()}\n")
            _emit(_err(request_id, "internal_error", str(e)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
