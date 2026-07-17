"""PAMSPEC-Lite reference implementation.

SQLite-backed, in-process. Optimized for spec-clarity, not throughput.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

SPEC_VERSION = "0.1.0-draft"

LITE_LIFECYCLE = {"active", "superseded", "archived"}
LITE_AVAILABILITY = {"available", "deleted"}
LITE_RETENTION = {"retained", "pending_deletion"}
LITE_VALIDATION = {"unverified", "corroborated"}

LIFECYCLE_TRANSITIONS = {
    "active": {"superseded", "archived"},
    "superseded": {"archived"},
    "archived": {"active"},
}


class PamspecError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, **details: Any):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details

    def to_envelope(self, operation_id: str) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "operation_id": operation_id,
            "details": self.details,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4()}"


class MemoryService:
    """PAMSPEC-Lite Memory Service."""

    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._init_schema()

    def delegations(self):
        from .delegation import DelegationStore
        if not hasattr(self, "_delegations"):
            self._delegations = DelegationStore(self._conn, self._lock)
        return self._delegations

    def subscriptions(self):
        from .subscription import SubscriptionManager
        if not hasattr(self, "_subs"):
            self._subs = SubscriptionManager()
        return self._subs

    def subscribe(
        self,
        scope_id: str,
        actor: dict,
        filter_spec: dict | None = None,
        start_sequence: int = 0,
        authorize=None,
    ):
        return self.subscriptions().open(
            scope_id=scope_id,
            actor=actor,
            event_source=lambda s, after: list(self.events(scope_id=s, after_sequence=after)),
            filter_spec=filter_spec,
            start_sequence=start_sequence,
            authorize=authorize,
        )

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memory_versions (
                    version_id TEXT PRIMARY KEY,
                    object_id TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    envelope_json TEXT NOT NULL,
                    committed_at TEXT NOT NULL,
                    UNIQUE (object_id, sequence)
                );
                CREATE INDEX IF NOT EXISTS idx_mv_object ON memory_versions (object_id);
                CREATE INDEX IF NOT EXISTS idx_mv_scope ON memory_versions (scope_id);

                CREATE TABLE IF NOT EXISTS memory_current (
                    object_id TEXT PRIMARY KEY,
                    scope_id TEXT NOT NULL,
                    current_version_id TEXT NOT NULL,
                    current_sequence INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS event_ledger (
                    event_id TEXT PRIMARY KEY,
                    scope_id TEXT NOT NULL,
                    object_id TEXT,
                    version_id TEXT,
                    event_type TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    ledger_sequence INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_ev_scope ON event_ledger (scope_id, ledger_sequence);
                CREATE INDEX IF NOT EXISTS idx_ev_object ON event_ledger (object_id, ledger_sequence);

                CREATE TABLE IF NOT EXISTS idempotency (
                    idempotency_key TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    result_json TEXT NOT NULL
                );
                """
            )

    def _next_ledger_seq(self) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(ledger_sequence), 0) + 1 AS s FROM event_ledger"
        ).fetchone()
        return int(row["s"])

    def _next_object_seq(self, object_id: str) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 AS s FROM memory_versions WHERE object_id = ?",
            (object_id,),
        ).fetchone()
        return int(row["s"])

    def _record_event(
        self,
        scope_id: str,
        event_type: str,
        object_id: str | None,
        version_id: str | None,
        payload: dict[str, Any],
    ) -> str:
        event_id = _new_id("evt")
        recorded_at = _now()
        ledger_seq = self._next_ledger_seq()
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "scope_id": scope_id,
            "object_id": object_id,
            "version_id": version_id,
            "recorded_at": recorded_at,
            "ledger_sequence": ledger_seq,
            **payload,
        }
        self._conn.execute(
            "INSERT INTO event_ledger "
            "(event_id, scope_id, object_id, version_id, event_type, event_json, recorded_at, ledger_sequence) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event_id,
                scope_id,
                object_id,
                version_id,
                event_type,
                json.dumps(event, sort_keys=True),
                recorded_at,
                ledger_seq,
            ),
        )
        return event_id

    @staticmethod
    def _validate_states(envelope: dict[str, Any]) -> None:
        if envelope["lifecycle_state"] not in LITE_LIFECYCLE:
            raise PamspecError(
                "invalid_request",
                f"PAMSPEC-Lite does not support lifecycle_state '{envelope['lifecycle_state']}'",
            )
        if envelope["availability_state"] not in LITE_AVAILABILITY:
            raise PamspecError(
                "invalid_request",
                f"PAMSPEC-Lite does not support availability_state '{envelope['availability_state']}'",
            )
        if envelope["retention_state"] not in LITE_RETENTION:
            raise PamspecError(
                "invalid_request",
                f"PAMSPEC-Lite does not support retention_state '{envelope['retention_state']}'",
            )
        if envelope["validation_state"] not in LITE_VALIDATION:
            raise PamspecError(
                "invalid_request",
                f"PAMSPEC-Lite does not support validation_state '{envelope['validation_state']}'",
            )

    def _check_idempotency(
        self, key: str | None, request: dict[str, Any]
    ) -> dict[str, Any] | None:
        if not key:
            return None
        digest = json.dumps(request, sort_keys=True)
        row = self._conn.execute(
            "SELECT request_digest, result_json FROM idempotency WHERE idempotency_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if row["request_digest"] != digest:
            raise PamspecError(
                "duplicate_operation",
                "idempotency key reused with different request content",
            )
        return json.loads(row["result_json"])

    def _store_idempotency(
        self, key: str | None, request: dict[str, Any], result: dict[str, Any]
    ) -> None:
        if not key:
            return
        digest = json.dumps(request, sort_keys=True)
        self._conn.execute(
            "INSERT INTO idempotency (idempotency_key, request_digest, result_json) VALUES (?, ?, ?)",
            (key, digest, json.dumps(result, sort_keys=True)),
        )

    def create(
        self,
        scope_id: str,
        object_type: str,
        canonical_content: Any,
        actor: dict[str, Any],
        provenance: dict[str, Any],
        object_id: str | None = None,
        lifecycle_state: str = "active",
        availability_state: str = "available",
        retention_state: str = "retained",
        validation_state: str = "unverified",
        idempotency_key: str | None = None,
        operation_id: str | None = None,
    ) -> dict[str, Any]:
        operation_id = operation_id or _new_id("op")
        request = {
            "op": "create",
            "scope_id": scope_id,
            "object_type": object_type,
            "canonical_content": canonical_content,
            "actor": actor,
            "provenance": provenance,
            "object_id": object_id,
            "lifecycle_state": lifecycle_state,
            "availability_state": availability_state,
            "retention_state": retention_state,
            "validation_state": validation_state,
        }
        cached = self._check_idempotency(idempotency_key, request)
        if cached is not None:
            return cached

        with self._lock, self._conn:
            object_id = object_id or _new_id("mem")
            existing = self._conn.execute(
                "SELECT 1 FROM memory_current WHERE object_id = ?", (object_id,)
            ).fetchone()
            if existing:
                raise PamspecError(
                    "invalid_request",
                    "object_id already exists; use update() for new versions",
                )

            version_id = _new_id("ver")
            sequence = 1
            now = _now()
            envelope = {
                "spec_version": SPEC_VERSION,
                "object_id": object_id,
                "version_id": version_id,
                "scope_id": scope_id,
                "object_type": object_type,
                "canonical_content": canonical_content,
                "lifecycle_state": lifecycle_state,
                "availability_state": availability_state,
                "retention_state": retention_state,
                "validation_state": validation_state,
                "committed_at": now,
                "recorded_at": now,
                "sequence": sequence,
                "actor": actor,
                "provenance": provenance,
            }
            self._validate_states(envelope)

            self._conn.execute(
                "INSERT INTO memory_versions (version_id, object_id, scope_id, sequence, envelope_json, committed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (version_id, object_id, scope_id, sequence, json.dumps(envelope, sort_keys=True), now),
            )
            self._conn.execute(
                "INSERT INTO memory_current (object_id, scope_id, current_version_id, current_sequence) "
                "VALUES (?, ?, ?, ?)",
                (object_id, scope_id, version_id, sequence),
            )
            event_id = self._record_event(
                scope_id, "object_created", object_id, version_id, {"actor": actor}
            )
            result = {
                "operation_id": operation_id,
                "object_id": object_id,
                "version_id": version_id,
                "sequence": sequence,
                "envelope": envelope,
                "event_id": event_id,
            }
            self._store_idempotency(idempotency_key, request, result)
            return result

    def read(
        self,
        scope_id: str,
        object_id: str,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT envelope_json FROM memory_versions WHERE object_id = ? AND scope_id = ? "
            + ("AND version_id = ?" if version_id else "ORDER BY sequence DESC LIMIT 1"),
            ((object_id, scope_id, version_id) if version_id else (object_id, scope_id)),
        ).fetchone()
        if row is None:
            raise PamspecError("object_not_found", f"object {object_id} not found in scope {scope_id}")
        envelope = json.loads(row["envelope_json"])
        if envelope["availability_state"] == "deleted" and version_id is None:
            raise PamspecError("object_deleted", "object has been deleted")
        return envelope

    def _load_current(self, scope_id: str, object_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT current_version_id FROM memory_current WHERE object_id = ? AND scope_id = ?",
            (object_id, scope_id),
        ).fetchone()
        if row is None:
            raise PamspecError("object_not_found", f"object {object_id} not found in scope {scope_id}")
        env_row = self._conn.execute(
            "SELECT envelope_json FROM memory_versions WHERE version_id = ?",
            (row["current_version_id"],),
        ).fetchone()
        return json.loads(env_row["envelope_json"])

    def update(
        self,
        scope_id: str,
        object_id: str,
        expected_version_id: str,
        canonical_content: Any,
        actor: dict[str, Any],
        provenance: dict[str, Any],
        operation_id: str | None = None,
    ) -> dict[str, Any]:
        operation_id = operation_id or _new_id("op")
        with self._lock, self._conn:
            current = self._load_current(scope_id, object_id)
            if current["availability_state"] == "deleted":
                raise PamspecError("object_deleted", "cannot update a deleted object")
            if current["version_id"] != expected_version_id:
                raise PamspecError(
                    "version_conflict",
                    "expected version is stale",
                    retryable=True,
                    expected_version_id=expected_version_id,
                    current_version_id=current["version_id"],
                )

            new_seq = self._next_object_seq(object_id)
            new_ver = _new_id("ver")
            now = _now()
            envelope = {**current}
            envelope.update(
                version_id=new_ver,
                canonical_content=canonical_content,
                actor=actor,
                provenance=provenance,
                sequence=new_seq,
                committed_at=now,
                recorded_at=now,
            )
            self._validate_states(envelope)

            self._conn.execute(
                "INSERT INTO memory_versions (version_id, object_id, scope_id, sequence, envelope_json, committed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_ver, object_id, scope_id, new_seq, json.dumps(envelope, sort_keys=True), now),
            )
            self._conn.execute(
                "UPDATE memory_current SET current_version_id = ?, current_sequence = ? WHERE object_id = ?",
                (new_ver, new_seq, object_id),
            )
            event_id = self._record_event(
                scope_id, "object_updated", object_id, new_ver, {"actor": actor}
            )
            return {
                "operation_id": operation_id,
                "object_id": object_id,
                "version_id": new_ver,
                "sequence": new_seq,
                "envelope": envelope,
                "event_id": event_id,
            }

    def transition(
        self,
        scope_id: str,
        object_id: str,
        expected_version_id: str,
        dimension: str,
        target_state: str,
        actor: dict[str, Any],
        provenance: dict[str, Any],
        operation_id: str | None = None,
    ) -> dict[str, Any]:
        operation_id = operation_id or _new_id("op")
        with self._lock, self._conn:
            current = self._load_current(scope_id, object_id)
            if current["version_id"] != expected_version_id:
                raise PamspecError(
                    "version_conflict", "expected version is stale", retryable=True,
                    expected_version_id=expected_version_id,
                    current_version_id=current["version_id"],
                )
            if dimension == "lifecycle":
                allowed = LIFECYCLE_TRANSITIONS.get(current["lifecycle_state"], set())
                if target_state not in allowed:
                    raise PamspecError(
                        "invalid_state_transition",
                        f"cannot transition lifecycle {current['lifecycle_state']} -> {target_state}",
                    )
                key = "lifecycle_state"
                event_type = "lifecycle_transitioned"
            elif dimension == "validation":
                key = "validation_state"
                event_type = "validation_transitioned"
            else:
                raise PamspecError(
                    "invalid_request",
                    f"PAMSPEC-Lite supports transitions on 'lifecycle' or 'validation' only, got {dimension}",
                )

            new_seq = self._next_object_seq(object_id)
            new_ver = _new_id("ver")
            now = _now()
            envelope = {**current}
            envelope.update(
                version_id=new_ver,
                sequence=new_seq,
                committed_at=now,
                recorded_at=now,
                actor=actor,
                provenance=provenance,
            )
            envelope[key] = target_state
            self._validate_states(envelope)

            self._conn.execute(
                "INSERT INTO memory_versions (version_id, object_id, scope_id, sequence, envelope_json, committed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_ver, object_id, scope_id, new_seq, json.dumps(envelope, sort_keys=True), now),
            )
            self._conn.execute(
                "UPDATE memory_current SET current_version_id = ?, current_sequence = ? WHERE object_id = ?",
                (new_ver, new_seq, object_id),
            )
            event_id = self._record_event(
                scope_id, event_type, object_id, new_ver,
                {"dimension": dimension, "target_state": target_state, "actor": actor},
            )
            return {
                "operation_id": operation_id,
                "object_id": object_id,
                "version_id": new_ver,
                "sequence": new_seq,
                "envelope": envelope,
                "event_id": event_id,
            }

    def delete(
        self,
        scope_id: str,
        object_id: str,
        expected_version_id: str,
        actor: dict[str, Any],
        provenance: dict[str, Any],
        operation_id: str | None = None,
    ) -> dict[str, Any]:
        operation_id = operation_id or _new_id("op")
        with self._lock, self._conn:
            current = self._load_current(scope_id, object_id)
            if current["version_id"] != expected_version_id:
                raise PamspecError(
                    "version_conflict", "expected version is stale", retryable=True,
                    expected_version_id=expected_version_id,
                    current_version_id=current["version_id"],
                )
            if current["availability_state"] == "deleted":
                raise PamspecError("object_deleted", "object already deleted")

            new_seq = self._next_object_seq(object_id)
            new_ver = _new_id("ver")
            now = _now()
            tombstone = {
                "spec_version": SPEC_VERSION,
                "object_id": object_id,
                "version_id": new_ver,
                "scope_id": scope_id,
                "object_type": current["object_type"],
                "canonical_content": None,
                "lifecycle_state": current["lifecycle_state"],
                "availability_state": "deleted",
                "retention_state": current["retention_state"],
                "validation_state": current["validation_state"],
                "committed_at": now,
                "recorded_at": now,
                "sequence": new_seq,
                "actor": actor,
                "provenance": provenance,
            }
            self._conn.execute(
                "INSERT INTO memory_versions (version_id, object_id, scope_id, sequence, envelope_json, committed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_ver, object_id, scope_id, new_seq, json.dumps(tombstone, sort_keys=True), now),
            )
            self._conn.execute(
                "UPDATE memory_current SET current_version_id = ?, current_sequence = ? WHERE object_id = ?",
                (new_ver, new_seq, object_id),
            )
            event_id = self._record_event(
                scope_id, "object_deleted", object_id, new_ver, {"actor": actor}
            )
            return {
                "operation_id": operation_id,
                "object_id": object_id,
                "version_id": new_ver,
                "sequence": new_seq,
                "envelope": tombstone,
                "event_id": event_id,
            }

    def query(
        self,
        scope_id: str,
        object_type: str | None = None,
        lifecycle_state: str | None = "active",
        availability_state: str | None = "available",
        validation_state: str | None = "corroborated",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT mv.envelope_json FROM memory_current mc "
            "JOIN memory_versions mv ON mv.version_id = mc.current_version_id "
            "WHERE mc.scope_id = ?",
            (scope_id,),
        ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            env = json.loads(row["envelope_json"])
            if object_type and env["object_type"] != object_type:
                continue
            if lifecycle_state and env["lifecycle_state"] != lifecycle_state:
                continue
            if availability_state and env["availability_state"] != availability_state:
                continue
            if validation_state and env["validation_state"] != validation_state:
                continue
            results.append(env)
            if len(results) >= limit:
                break
        return results

    def history(self, scope_id: str, object_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT envelope_json FROM memory_versions WHERE object_id = ? AND scope_id = ? ORDER BY sequence ASC",
            (object_id, scope_id),
        ).fetchall()
        return [json.loads(r["envelope_json"]) for r in rows]

    def events(self, scope_id: str, after_sequence: int = 0) -> Iterable[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT event_json FROM event_ledger WHERE scope_id = ? AND ledger_sequence > ? "
            "ORDER BY ledger_sequence ASC",
            (scope_id, after_sequence),
        ).fetchall()
        return [json.loads(r["event_json"]) for r in rows]

    def close(self) -> None:
        self._conn.close()
