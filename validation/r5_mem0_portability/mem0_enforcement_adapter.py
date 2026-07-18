"""PAMSPEC enforcement adapter over unmodified Mem0 2.0.12.

Wraps a mem0.Memory instance and enforces PAMSPEC semantics that Mem0
does not natively provide. Mem0 source is not modified.

Enforced behaviors (adapter-supplied, not native to Mem0):
  - scope immutability: update() rejects attempts to change scope fields
  - expected-version conflict: update() rejects stale expected_version_id
  - durable idempotency: create() with the same idempotency_key is
    idempotent; state persists across adapter restarts when sidecar_path
    is a real file (not ":memory:")
  - tombstone registry: deleted object_ids are tracked durably; further
    mutations raise a scope_mutation or object_not_found error envelope
  - explicit PAMSPEC error envelopes: all rejections return a dict with
    {ok: False, error: {code, message, retryable}}

Native Mem0 behaviors (used as-is, not re-implemented):
  - memory storage and retrieval (via Mem0's public Python API)
  - scope tuple (user_id / agent_id / run_id)
  - history ledger
  - timestamps (created_at, updated_at)

Durable side state (SQLite sidecar):
  - object scope (scope_registry table)
  - current adapter version sequence (version_state table)
  - idempotency key + request digest + result (idempotency_store table)
  - tombstone object_ids (tombstones table)

Classification of each operation's source is recorded in the
`_diagnostics` list for R5 evidence records.

Mem0 version: 2.0.12 (unmodified).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
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

    sidecar_path: SQLite database path for durable side state. Use ":memory:"
    for in-process-only durability (state lost on adapter close). Use a real
    file path for cross-restart durability — two adapter instances sharing the
    same file path share all side state.
    """

    SCOPE_SEP = "/"
    SCOPE_FIELDS = ("user_id", "agent_id", "run_id")

    def __init__(self, mem0_instance: Any, sidecar_path: str = ":memory:"):
        self._mem0 = mem0_instance
        self._lock = threading.Lock()
        self._db = sqlite3.connect(sidecar_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._init_sidecar()
        self._diagnostics: list[dict] = []

    def _init_sidecar(self) -> None:
        with self._db:
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS scope_registry (
                    object_id TEXT PRIMARY KEY,
                    scope_str TEXT NOT NULL,
                    user_id TEXT,
                    agent_id TEXT,
                    run_id TEXT
                );
                CREATE TABLE IF NOT EXISTS version_state (
                    object_id TEXT PRIMARY KEY,
                    current_version_id TEXT NOT NULL,
                    current_sequence INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_store (
                    idempotency_key TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    result_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tombstones (
                    object_id TEXT PRIMARY KEY
                );
            """)

    def close(self) -> None:
        """Close the SQLite sidecar connection."""
        self._db.close()

    # ── Sidecar helpers ──────────────────────────────────────────────────────

    def _is_tombstone(self, object_id: str) -> bool:
        row = self._db.execute(
            "SELECT 1 FROM tombstones WHERE object_id = ?", (object_id,)
        ).fetchone()
        return row is not None

    def _add_tombstone(self, object_id: str) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO tombstones (object_id) VALUES (?)", (object_id,)
            )

    @property
    def _tombstones(self) -> set:
        """Return current tombstone set (for test introspection)."""
        rows = self._db.execute("SELECT object_id FROM tombstones").fetchall()
        return {r["object_id"] for r in rows}

    def _get_scope_info(self, object_id: str) -> dict | None:
        row = self._db.execute(
            "SELECT scope_str, user_id, agent_id, run_id FROM scope_registry WHERE object_id = ?",
            (object_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "scope_str": row["scope_str"],
            "user_id": row["user_id"] or "",
            "agent_id": row["agent_id"] or "",
            "run_id": row["run_id"] or "",
        }

    def _set_scope_info(self, object_id: str, scope_info: dict) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO scope_registry "
                "(object_id, scope_str, user_id, agent_id, run_id) VALUES (?, ?, ?, ?, ?)",
                (
                    object_id,
                    scope_info["scope_str"],
                    scope_info.get("user_id"),
                    scope_info.get("agent_id"),
                    scope_info.get("run_id"),
                ),
            )

    def _get_version_id(self, object_id: str) -> str | None:
        row = self._db.execute(
            "SELECT current_version_id FROM version_state WHERE object_id = ?", (object_id,)
        ).fetchone()
        return row["current_version_id"] if row else None

    def _get_version_seq(self, object_id: str) -> tuple[str | None, int]:
        row = self._db.execute(
            "SELECT current_version_id, current_sequence FROM version_state WHERE object_id = ?",
            (object_id,),
        ).fetchone()
        if row is None:
            return None, 0
        return row["current_version_id"], row["current_sequence"]

    def _set_version(self, object_id: str, version_id: str, sequence: int) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO version_state "
                "(object_id, current_version_id, current_sequence) VALUES (?, ?, ?)",
                (object_id, version_id, sequence),
            )

    def _get_idempotency(self, key: str) -> dict | None:
        row = self._db.execute(
            "SELECT request_digest, result_json FROM idempotency_store WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return {"digest": row["request_digest"], "result": json.loads(row["result_json"])}

    def _set_idempotency(self, key: str, digest: str, result: dict) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO idempotency_store "
                "(idempotency_key, request_digest, result_json) VALUES (?, ?, ?)",
                (key, digest, json.dumps(result, sort_keys=True)),
            )

    # ── Core operations ──────────────────────────────────────────────────────

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
            return the cached result without writing to Mem0. State is durable
            across adapter restarts when sidecar_path is a real file.
          - idempotency conflict: same key with DIFFERENT content raises.
          - scope registration: object_id -> scope stored for immutability checks.
        """
        request_digest = _digest({"scope": scope_str, "content": content, "type": object_type})

        with self._lock:
            if idempotency_key is not None:
                cached = self._get_idempotency(idempotency_key)
                if cached is not None:
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
            self._set_scope_info(mem0_id, {**scope_parts, "scope_str": scope_str})
            self._set_version(mem0_id, version_id, 1)
            if idempotency_key is not None:
                self._set_idempotency(idempotency_key, request_digest, result)

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
            if self._is_tombstone(object_id):
                self._diag("update", "adapter-enforced", f"rejected: {object_id} is a tombstone")
                raise PamspecAdapterError(
                    "object_not_found",
                    f"object {object_id!r} has been deleted; cannot update a tombstone",
                )

            current_scope = self._get_scope_info(object_id)
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
                current_ver = self._get_version_id(object_id)
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
            _, current_seq = self._get_version_seq(object_id)
            seq = (current_seq or 1) + 1
            new_version_id = f"ver:{object_id}:{seq}"
            self._set_version(object_id, new_version_id, seq)

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
        if self._is_tombstone(object_id):
            raise PamspecAdapterError("object_not_found", f"object {object_id!r} is a tombstone")
        mem0_obj = self._mem0.get(object_id)
        if mem0_obj is None:
            raise PamspecAdapterError("object_not_found", f"object {object_id!r} not found")
        self._diag("read", "native", f"read object_id={object_id}")
        return _ok({"mem0_object": mem0_obj, "version_id": self._get_version_id(object_id)})

    def delete(self, object_id: str, actor: dict) -> dict:
        """Delete a memory. Adapter records the tombstone durably in the SQLite sidecar."""
        with self._lock:
            if self._is_tombstone(object_id):
                raise PamspecAdapterError("object_not_found", f"object {object_id!r} already deleted")

        self._mem0.delete(object_id)

        with self._lock:
            self._add_tombstone(object_id)

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
          - reads current state from Mem0 (live objects only)
          - reads history from Mem0 (attempted for all objects)
          - includes tombstone state from adapter sidecar
          - preserves scope, provenance, extensions from adapter sidecar
          - preserves content from Mem0

        The bundle is deterministic: same objects, same content, same
        serialization order (sorted by object_id).
        """
        items: list[dict] = []
        for oid in sorted(object_ids):
            scope_info = self._get_scope_info(oid) or {}
            is_tombstone = self._is_tombstone(oid)

            mem0_obj = None
            if not is_tombstone:
                mem0_obj = self._mem0.get(oid)

            # Always try to get history (Mem0 uses soft-delete; history persists)
            mem0_history: list = []
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
                "current_version_id": self._get_version_id(oid),
                "provenance": provenance,
                "actor": actor,
                "extensions": extensions,
                "tombstone": is_tombstone,
                "history_events": [
                    {
                        "event": h.get("event"),
                        "old_memory": h.get("old_memory"),
                        "new_memory": h.get("new_memory"),
                    }
                    for h in mem0_history
                ],
            })

        return {
            "bundle_version": "r5-0.1-draft",
            "source_framework": "mem0ai",
            "source_framework_version": "2.0.12",
            "objects": items,
        }
