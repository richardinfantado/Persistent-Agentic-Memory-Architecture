"""PAMSPEC-over-MCP protocol-adapter stub.

Maps MCP tool calls (`pamspec.<operation>`) onto the reference
implementation's MemoryService. Preserves PAMSPEC error envelopes
in the tool result rather than collapsing them into MCP protocol
errors.

This module intentionally does NOT depend on any specific MCP
transport package. Wire `dispatch()` into whichever MCP transport
you use.
"""

from __future__ import annotations

from typing import Any, Callable

from pamspec_ref import MemoryService, PamspecError

BINDING_VERSION = "0.1.0-draft"
SPEC_VERSION = "0.1.0-draft"


class PamspecMcpAdapter:
    def __init__(self, service: MemoryService, profiles: list[str] | None = None):
        self._svc = service
        self._profiles = profiles or ["PAMSPEC-Lite"]
        self._tools: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "pamspec.create": self._create,
            "pamspec.read": self._read,
            "pamspec.update": self._update,
            "pamspec.transition": self._transition,
            "pamspec.query": self._query,
            "pamspec.inspect_history": self._inspect_history,
            "pamspec.delete": self._delete,
        }

    def manifest(self) -> dict[str, Any]:
        return {
            "spec_version": SPEC_VERSION,
            "binding_version": BINDING_VERSION,
            "profiles": self._profiles,
            "operations": [name.split(".", 1)[1] for name in sorted(self._tools)],
        }

    def dispatch(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = self._tools.get(tool_name)
        if handler is None:
            return self._error_envelope(
                "invalid_request",
                f"unknown tool '{tool_name}'; call pamspec.manifest for supported operations",
                False,
                arguments.get("operation_id", "op:unknown"),
            )
        try:
            return handler(arguments)
        except PamspecError as e:
            return {"error": e.to_envelope(arguments.get("operation_id", "op:unknown"))}

    def _error_envelope(
        self, code: str, message: str, retryable: bool, operation_id: str
    ) -> dict[str, Any]:
        return {
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "operation_id": operation_id,
                "details": {},
            }
        }

    def _create(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self._svc.create(
            scope_id=args["scope_id"],
            object_type=args["object_type"],
            canonical_content=args["canonical_content"],
            actor=args["actor"],
            provenance=args["provenance"],
            object_id=args.get("object_id"),
            lifecycle_state=args.get("lifecycle_state", "active"),
            availability_state=args.get("availability_state", "available"),
            retention_state=args.get("retention_state", "retained"),
            validation_state=args.get("validation_state", "unverified"),
            idempotency_key=args.get("idempotency_key"),
            operation_id=args.get("operation_id"),
        )
        return {"result": result}

    def _read(self, args: dict[str, Any]) -> dict[str, Any]:
        envelope = self._svc.read(
            scope_id=args["scope_id"],
            object_id=args["object_id"],
            version_id=args.get("version_id"),
        )
        return {"result": {"envelope": envelope}}

    def _update(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self._svc.update(
            scope_id=args["scope_id"],
            object_id=args["object_id"],
            expected_version_id=args["expected_version_id"],
            canonical_content=args["canonical_content"],
            actor=args["actor"],
            provenance=args["provenance"],
            operation_id=args.get("operation_id"),
        )
        return {"result": result}

    def _transition(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self._svc.transition(
            scope_id=args["scope_id"],
            object_id=args["object_id"],
            expected_version_id=args["expected_version_id"],
            dimension=args["dimension"],
            target_state=args["target_state"],
            actor=args["actor"],
            provenance=args["provenance"],
            operation_id=args.get("operation_id"),
        )
        return {"result": result}

    def _query(self, args: dict[str, Any]) -> dict[str, Any]:
        filters = args.get("filters", {}) or {}
        limit = args.get("limit", 50)
        rows = self._svc.query(
            scope_id=args["scope_id"],
            object_type=filters.get("object_type"),
            lifecycle_state=filters.get("lifecycle_state", "active"),
            availability_state=filters.get("availability_state", "available"),
            validation_state=filters.get("validation_state", "corroborated"),
            limit=limit,
        )
        return {"result": {"objects": rows, "count": len(rows)}}

    def _inspect_history(self, args: dict[str, Any]) -> dict[str, Any]:
        if "object_id" in args:
            versions = self._svc.history(
                scope_id=args["scope_id"], object_id=args["object_id"]
            )
            return {"result": {"versions": versions}}
        after = args.get("after_sequence", 0)
        events = list(self._svc.events(scope_id=args["scope_id"], after_sequence=after))
        return {"result": {"events": events}}

    def _delete(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self._svc.delete(
            scope_id=args["scope_id"],
            object_id=args["object_id"],
            expected_version_id=args["expected_version_id"],
            actor=args["actor"],
            provenance=args["provenance"],
            operation_id=args.get("operation_id"),
        )
        return {"result": result}
