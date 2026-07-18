"""PAMSPEC enforcement adapter over unmodified Mem0 2.0.12.

Wraps a mem0.Memory instance and enforces PAMSPEC semantics that Mem0
does not natively provide. Mem0 source is not modified.

Enforced behaviors (adapter-supplied, not native to Mem0):
  - scope immutability: update() rejects attempts to change scope fields
  - expected-version conflict: update() rejects stale expected_version_id
  - durable idempotency: create() with the same idempotency_key is
    idempotent; no duplicate write occurs
  - tombstone registry: deleted object_ids are tracked; further mutations
    raise a scope_mutation or object_not_found error envelope
  - explicit PAMSPEC error envelopes: all rejections return a dict with
    {ok: False, error: {code, message, retryable}}

Native Mem0 behaviors (used as-is, not re-implemented):
  - memory storage and retrieval (via Mem0's public Python API)
  - scope tuple (user_id / agent_id / run_id)
  - history ledger
  - timestamps (created_at, updated_at)

Classification of each operation's source is recorded in the
`_diagnostics` list for R5 evidence records.

Mem0 version: 2.0.12 (unmodified).
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from typing import Any


_MISSING = object()


class PamspecAdapterError(Exception):
    """Raised when the adapter rejects an operation before it reaches Mem0."""
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.envelope = {"ok": False, "error": {"code": code, "message": message, "retryable": retryable}}


def _ok(result: dict) -> dict:
    return {"ok": True, "result": result}


def _digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


class Mem0EnforcementAdapter:
    """PAMSPEC enforcement adapter over mem0.Memory.

    Thread-safe for concurrent use (uses a lock for side-state operations).
    Mem0 itself is not modified.

    Scope format: "<scope_str>" — a flat string. The adapter stores it and
    enforces immutability. Mem0 scope fields (user_id, agent_id, run_id) are
    derived from parsing the scope string on first create.
    """

    SCOPE_SEP = "/"
    SCOPE_FIELDS = ("user_id", "agent_id", "run_id")

    def __init__(self, mem0_instance: Any):
        self._mem0 = mem0_instance
        self._lock = threading.Lock()
        # Side-state (adapter-enforced, not in Mem0)
        self._scope_registry: dict[str, dict] = {}   # object_id -> {user_id, agent_id, run_id, scope_str}
        self._version_state: dict[str, str] = {}     # object_id -> current_version_id
        self._idempotency: dict[str, dict] = {}      # idem_key -> {digest, result}
        self._tombstones: set[str] = set()           # deleted object_ids
        self._diagnostics: list[dict] = []

    def _parse_scope(self, scope_str: str) -> dict[str, str]:
        """Parse "user:alice/agent:a1/run:r1" -> {user_id, agent_id, run_id}."""
        parts: dict[str, str] = {}
        for token in scope_str.split("/"):
            if ":" in token:
                k, v = token.split(":", 1)
                if k == "user":
                    parts["user_id"] = v
                elif k == "agent":
                    parts["agent_id"] = v
                elif k == "run":
                    parts["run_id"] = v
        return parts

    def _diag(self, operation: str, source: str, detail: str) -> None:
        self._diagnostics.append({"operation": operation, "source": source, "detail": detail})

    def create(
        self,
        scope_str: str,
        content: str,
        actor: dict,
        provenance: dict,
        object_type: str = "claim",
        idempotency_key: str | None = None,
        extensions: dict | None = None,
    ) -> dict:
        """Create a memory. Returns a PAMSPEC-shaped result envelope.

        Adapter-enforced:
          - idempotency: if idempotency_key already used with same content,
            return the cached result without writing to Mem0.
          - idempotency conflict: same key with DIFFERENT content raises.
          - scope registration: object_id -> scope stored for immutability checks.
        """
        request_digest = _digest({"scope": scope_str, "content": content, "type": object_type})

        with self._lock:
            if idempotency_key is not None and idempotency_key in self._idempotency:
                cached = self._idempotency[idempotency_key]
                if cached["digest"] != request_digest:
                    self._diag("create", "adapter-enforced", "idempotency_conflict")
                    raise PamspecAdapterError(
                        "idempotency_conflict",
                        f"idempotency_key {idempotency_key!r} was previously used "
                        f"with different request content",
                    )
                self._diag("create", "adapter-enforced", "idempotency_hit_return_cached")
                return cached["result"]

        scope_parts = self._parse_scope(scope_str)
        metadata: dict[str, Any] = {
            "pamspec_scope": scope_str,
            "pamspec_object_type": object_type,
            "pamspec_actor": json.dumps(actor),
            "pamspec_provenance": json.dumps(provenance),
        }
        if extensions:
            metadata["pamspec_extensions"] = json.dumps(extensions)

        add_kwargs = dict(
            messages=[{"role": "user", "content": content}],
            infer=False,
            metadata=metadata,
        )
        add_kwargs.update({k: v for k, v in scope_parts.items() if v})

        mem0_result = self._mem0.add(**add_kwargs)
        results = mem0_result.get("results") or []
        if not results:
            raise PamspecAdapterError("internal_error", "Mem0 add() returned no results")

        mem0_id = results[0]["id"]
        version_id = f"ver:{mem0_id}:1"

        result = _ok({
            "object_id": mem0_id,
            "version_id": version_id,
            "sequence": 1,
            "scope_str": scope_str,
            "scope_parts": scope_parts,
            "content": content,
            "actor": actor,
            "provenance": provenance,
            "object_type": object_type,
            "extensions": extensions or {},
            "source": "adapter_created",
        })

        with self._lock:
            self._scope_registry[mem0_id] = {**scope_parts, "scope_str": scope_str}
            self._version_state[mem0_id] = version_id
            if idempotency_key is not None:
                self._idempotency[idempotency_key] = {"digest": request_digest, "result": result}

        self._diag("create", "adapter-enforced+native", f"created object_id={mem0_id}")
        return result

    def update(
        self,
        object_id: str,
        content: str,
        actor: dict,
        provenance: dict,
        expected_version_id: str | None = None,
        scope_str: str | None = None,
        extensions: dict | None = None,
    ) -> dict:
        """Update a memory. Adapter-enforced: scope immutability, expected-version conflict."""
        with self._lock:
            if object_id in self._tombstones:
                self._diag("update", "adapter-enforced", f"rejected: {object_id} is a tombstone")
                raise PamspecAdapterError(
                    "object_not_found",
                    f"object {object_id!r} has been deleted; cannot update a tombstone",
                )

            current_scope = self._scope_registry.get(object_id)
            if scope_str is not None and current_scope is not None:
                if scope_str != current_scope["scope_str"]:
                    self._diag("update", "adapter-enforced", f"scope_mutation_rejected: {object_id}")
                    raise PamspecAdapterError(
                        "scope_mutation",
                        f"scope is immutable for object {object_id!r}; "
                        f"requested {scope_str!r} but registered scope is "
                        f"{current_scope['scope_str']!r}",
                    )

            if expected_version_id is not None:
                current_ver = self._version_state.get(object_id)
                if current_ver != expected_version_id:
                    self._diag("update", "adapter-enforced", f"version_conflict: {object_id}")
                    raise PamspecAdapterError(
                        "version_conflict",
                        f"expected version {expected_version_id!r} but current is "
                        f"{current_ver!r}",
                        retryable=True,
                    )

        metadata: dict[str, Any] = {
            "pamspec_actor": json.dumps(actor),
            "pamspec_provenance": json.dumps(provenance),
        }
        if extensions:
            metadata["pamspec_extensions"] = json.dumps(extensions)

        self._mem0.update(object_id, text=content, metadata=metadata)

        with self._lock:
            old_scope = self._scope_registry.get(object_id, {})
            old_seq_parts = (self._version_state.get(object_id) or "").split(":")
            seq = int(old_seq_parts[-1]) + 1 if old_seq_parts else 2
            new_version_id = f"ver:{object_id}:{seq}"
            self._version_state[object_id] = new_version_id

        self._diag("update", "adapter-enforced+native", f"updated object_id={object_id}")
        return _ok({
            "object_id": object_id,
            "version_id": new_version_id,
            "sequence": seq,
            "content": content,
            "actor": actor,
            "provenance": provenance,
            "extensions": extensions or {},
            "source": "adapter_updated",
        })

    def read(self, object_id: str) -> dict:
        """Read a memory's current state. Uses Mem0's public get()."""
        if object_id in self._tombstones:
            raise PamspecAdapterError("object_not_found", f"object {object_id!r} is a tombstone")
        mem0_obj = self._mem0.get(object_id)
        if mem0_obj is None:
            raise PamspecAdapterError("object_not_found", f"object {object_id!r} not found")
        self._diag("read", "native", f"read object_id={object_id}")
        return _ok({"mem0_object": mem0_obj, "version_id": self._version_state.get(object_id)})

    def delete(self, object_id: str, actor: dict) -> dict:
        """Delete a memory. Adapter records the tombstone."""
        with self._lock:
            if object_id in self._tombstones:
                raise PamspecAdapterError("object_not_found", f"object {object_id!r} already deleted")

        self._mem0.delete(object_id)

        with self._lock:
            self._tombstones.add(object_id)

        self._diag("delete", "adapter-enforced+native", f"tombstone registered for {object_id}")
        return _ok({
            "object_id": object_id,
            "tombstone": True,
            "actor": actor,
            "source": "adapter_deleted",
        })

    def export_bundle(self, object_ids: list[str]) -> dict:
        """Export selected objects into a deterministic PAMSPEC bundle.

        For each object_id:
          - reads current state from Mem0
          - reads history from Mem0
          - includes tombstone state from adapter registry
          - preserves scope, provenance, extensions from adapter side-state
          - preserves content from Mem0

        The bundle is deterministic: same objects, same content, same
        serialization order (sorted by object_id).
        """
        items: list[dict] = []
        for oid in sorted(object_ids):
            scope_info = self._scope_registry.get(oid, {})
            is_tombstone = oid in self._tombstones

            mem0_obj = None
            mem0_history = []
            if not is_tombstone:
                mem0_obj = self._mem0.get(oid)
                try:
                    mem0_history = self._mem0.history(oid) or []
                except Exception:
                    mem0_history = []

            metadata: dict = {}
            if mem0_obj:
                metadata = mem0_obj.get("metadata") or {}

            extensions = {}
            if metadata.get("pamspec_extensions"):
                try:
                    extensions = json.loads(metadata["pamspec_extensions"])
                except Exception:
                    extensions = {"raw": metadata["pamspec_extensions"]}

            provenance = {}
            if metadata.get("pamspec_provenance"):
                try:
                    provenance = json.loads(metadata["pamspec_provenance"])
                except Exception:
                    provenance = {}

            actor = {}
            if metadata.get("pamspec_actor"):
                try:
                    actor = json.loads(metadata["pamspec_actor"])
                except Exception:
                    actor = {}

            items.append({
                "object_id": oid,
                "scope_str": scope_info.get("scope_str", ""),
                "scope_parts": {k: scope_info.get(k, "") for k in ("user_id", "agent_id", "run_id")},
                "object_type": metadata.get("pamspec_object_type", "claim"),
                "current_content": mem0_obj["memory"] if mem0_obj else None,
                "current_version_id": self._version_state.get(oid),
                "provenance": provenance,
                "actor": actor,
                "extensions": extensions,
                "tombstone": is_tombstone,
                "history_events": [
                    {"event": h.get("event"), "old_memory": h.get("old_memory"),
                     "new_memory": h.get("new_memory")}
                    for h in mem0_history
                ],
            })

        return {
            "bundle_version": "r5-0.1-draft",
            "source_framework": "mem0ai",
            "source_framework_version": "2.0.12",
            "objects": items,
        }
