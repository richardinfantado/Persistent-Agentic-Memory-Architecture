"""Reference Delegation Object storage and enforcement.

Enforcement is:
- Time window (not_before/not_after) checked against the service clock.
- granted_operations must be a superset of the exercised operation.
- Optional granted_object_ids restriction.
- Optional usage_limit decremented per exercise.

This is a reference; a production implementation would additionally
validate the granting_actor actually held the granted authority.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from .service import PamspecError, _now, _new_id, SPEC_VERSION


class DelegationStore:
    def __init__(self, conn: sqlite3.Connection, lock: threading.RLock):
        self._conn = conn
        self._lock = lock
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS delegations (
                    delegation_id TEXT PRIMARY KEY,
                    scope_id TEXT NOT NULL,
                    envelope_json TEXT NOT NULL,
                    revoked_at TEXT,
                    usage_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_del_scope ON delegations (scope_id);
                """
            )

    def grant(
        self,
        scope_id: str,
        granting_actor: dict[str, Any],
        delegated_actor: dict[str, Any],
        granted_operations: list[str],
        policy_basis: str,
        not_before: str,
        not_after: str,
        granted_object_types: list[str] | None = None,
        granted_object_ids: list[str] | None = None,
        target_scope_id: str | None = None,
        revocable: bool = True,
        usage_limit: int | None = None,
    ) -> dict[str, Any]:
        if not_before > not_after:
            raise PamspecError(
                "policy_denied", "delegation_window_inverted: not_before > not_after"
            )
        if not granted_operations:
            raise PamspecError("invalid_request", "granted_operations MUST be non-empty")
        now = _now()
        envelope = {
            "spec_version": SPEC_VERSION,
            "delegation_id": _new_id("del"),
            "version_id": _new_id("delver"),
            "scope_id": scope_id,
            "granting_actor": granting_actor,
            "delegated_actor": delegated_actor,
            "granted_operations": granted_operations,
            "policy_basis": policy_basis,
            "not_before": not_before,
            "not_after": not_after,
            "revocable": revocable,
            "lifecycle_state": "active",
            "availability_state": "available",
            "retention_state": "retained",
            "validation_state": "corroborated",
            "committed_at": now,
            "recorded_at": now,
            "sequence": 1,
            "actor": granting_actor,
            "provenance": {
                "provenance_id": _new_id("prov"),
                "actor": granting_actor,
                "activity": "granted_delegation",
                "recorded_at": now,
            },
        }
        if granted_object_types is not None:
            envelope["granted_object_types"] = granted_object_types
        if granted_object_ids is not None:
            envelope["granted_object_ids"] = granted_object_ids
        if target_scope_id is not None:
            envelope["target_scope_id"] = target_scope_id
        if usage_limit is not None:
            envelope["usage_limit"] = usage_limit
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO delegations (delegation_id, scope_id, envelope_json) VALUES (?, ?, ?)",
                (envelope["delegation_id"], scope_id, json.dumps(envelope, sort_keys=True)),
            )
        return envelope

    def revoke(self, delegation_id: str) -> None:
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT envelope_json FROM delegations WHERE delegation_id = ?",
                (delegation_id,),
            ).fetchone()
            if row is None:
                raise PamspecError("object_not_found", "delegation not found")
            env = json.loads(row["envelope_json"])
            if not env.get("revocable", True):
                raise PamspecError("policy_denied", "delegation is not revocable")
            self._conn.execute(
                "UPDATE delegations SET revoked_at = ? WHERE delegation_id = ?",
                (_now(), delegation_id),
            )

    def check(
        self,
        delegation_id: str,
        scope_id: str,
        delegated_actor_id: str,
        operation: str,
        object_id: str | None = None,
        object_type: str | None = None,
    ) -> dict[str, Any]:
        """Return the delegation envelope if the operation is permitted, else raise."""
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT envelope_json, revoked_at, usage_count FROM delegations WHERE delegation_id = ?",
                (delegation_id,),
            ).fetchone()
            if row is None:
                raise PamspecError("access_denied", "delegation not found")
            env = json.loads(row["envelope_json"])
            if row["revoked_at"] is not None:
                raise PamspecError("access_denied", "delegation revoked")
            if env["scope_id"] != scope_id:
                raise PamspecError("access_denied", "delegation scope mismatch")
            if env["delegated_actor"]["actor_id"] != delegated_actor_id:
                raise PamspecError("access_denied", "actor is not the delegate")
            now = _now()
            if now < env["not_before"] or now > env["not_after"]:
                raise PamspecError("access_denied", "delegation outside time window")
            if operation not in env["granted_operations"]:
                raise PamspecError(
                    "access_denied",
                    f"operation '{operation}' not among granted_operations",
                )
            if "granted_object_types" in env and object_type is not None:
                if object_type not in env["granted_object_types"]:
                    raise PamspecError(
                        "access_denied",
                        f"object_type '{object_type}' not permitted by delegation",
                    )
            if "granted_object_ids" in env and object_id is not None:
                if object_id not in env["granted_object_ids"]:
                    raise PamspecError(
                        "access_denied",
                        f"object '{object_id}' not permitted by delegation",
                    )
            if "usage_limit" in env:
                if row["usage_count"] >= env["usage_limit"]:
                    raise PamspecError("access_denied", "delegation usage limit exhausted")
                self._conn.execute(
                    "UPDATE delegations SET usage_count = usage_count + 1 WHERE delegation_id = ?",
                    (delegation_id,),
                )
            return env
