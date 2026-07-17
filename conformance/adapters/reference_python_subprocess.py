"""Subprocess wrapper exposing the Python reference implementation
over the harness stdio protocol (see harness/PROTOCOL.md).

Run as: python -m conformance.adapters.reference_python_subprocess

Reads one JSON request per line on stdin. Writes one JSON response
per line on stdout. Logs go to stderr only. The wrapper keeps a
single MemoryService instance for the lifetime of the process and
manages subscription handles by id.

The wrapper deliberately re-uses the same reference implementation
that the in-process ReferencePythonAdapter uses, so subprocess and
in-process tests exercise the same behavior.
"""

from __future__ import annotations

import json
import sys
import uuid
from typing import Any

from pamspec_ref import MemoryService, PamspecError


PROTOCOL_VERSION = 1


def _emit(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")
    sys.stdout.flush()


def _log(msg: str) -> None:
    sys.stderr.write(f"[reference_python_subprocess] {msg}\n")
    sys.stderr.flush()


def _error_envelope(request_id: str, code: str, message: str, retryable: bool = False, **details: Any) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": details,
        },
    }


class Wrapper:
    def __init__(self):
        self._svc = MemoryService(":memory:")
        self._subscriptions: dict[str, Any] = {}

    # --- Lite ---

    def create(self, args):
        return self._svc.create(**args)

    def read(self, args):
        return self._svc.read(**args)

    def update(self, args):
        return self._svc.update(**args)

    def transition(self, args):
        return self._svc.transition(**args)

    def delete(self, args):
        return self._svc.delete(**args)

    def query(self, args):
        return self._svc.query(**args)

    def history(self, args):
        return self._svc.history(**args)

    # --- Delegation ---

    def grant_delegation(self, args):
        return self._svc.delegations().grant(**args)

    def check_delegation(self, args):
        return self._svc.delegations().check(**args)

    def revoke_delegation(self, args):
        self._svc.delegations().revoke(args["delegation_id"])
        return {"revoked": True}

    # --- Subscribe ---

    def subscribe(self, args):
        sub = self._svc.subscribe(
            scope_id=args["scope_id"],
            actor=args["actor"],
            filter_spec=args.get("filter_spec"),
            start_sequence=args.get("start_sequence", 0),
        )
        sub_id = str(uuid.uuid4())
        self._subscriptions[sub_id] = sub
        return {"subscription_id": sub_id}

    def poll_subscription(self, args):
        sub = self._subscriptions.get(args["subscription_id"])
        if sub is None:
            raise PamspecError("object_not_found", "subscription not found")
        return {"events": sub.poll(max_events=args.get("max_events", 100))}

    def close_subscription(self, args):
        sub = self._subscriptions.get(args["subscription_id"])
        if sub is None:
            raise PamspecError("object_not_found", "subscription not found")
        sub.close(args.get("reason", "client_closed"))
        return {"closed": True}


OPERATIONS = {
    "create", "read", "update", "transition", "delete", "query", "history",
    "grant_delegation", "check_delegation", "revoke_delegation",
    "subscribe", "poll_subscription", "close_subscription",
}


def main() -> int:
    _emit({
        "type": "hello",
        "protocol_version": PROTOCOL_VERSION,
        "adapter": {"name": "reference-python-subprocess", "version": "0.1.0"},
        "implementation": {"name": "pamspec_ref", "version": "0.1.0-draft"},
        "spec_commit": "",
        "profiles_supported": ["PAMSPEC-Lite", "PAMSPEC-Delegation", "PAMSPEC-Subscribe"],
    })
    wrapper = Wrapper()
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
            if op not in OPERATIONS:
                _emit(_error_envelope(request_id, "invalid_request", f"unknown operation {op!r}"))
                continue
            handler = getattr(wrapper, op)
            try:
                result = handler(args)
            except PamspecError as e:
                _emit(_error_envelope(request_id, e.code, e.message, e.retryable, **e.details))
                continue
            _emit({"request_id": request_id, "result": result})
        except json.JSONDecodeError as e:
            _emit(_error_envelope(request_id, "invalid_request", f"invalid JSON: {e}"))
        except Exception as e:
            _log(f"internal error handling request {request_id!r}: {type(e).__name__}: {e}")
            _emit(_error_envelope(request_id, "internal_error", str(e)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
