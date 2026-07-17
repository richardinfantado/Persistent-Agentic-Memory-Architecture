"""Reference Subscribe implementation.

Pull-model with a cursor. Real bindings (MCP notifications, WebSocket,
SSE, message bus) push events; this reference exposes a poll() method
so a transport wrapper can drive the loop.

Delivery guarantee: at-least-once, keyed by event_id.
Per-event authorization re-evaluation is performed by the caller
(the MemoryService) because it holds the policy engine.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any, Callable, Iterator

from .service import _new_id, _now


class Subscription:
    def __init__(
        self,
        subscription_id: str,
        scope_id: str,
        actor: dict[str, Any],
        event_source: Callable[[str, int], list[dict[str, Any]]],
        filter_spec: dict[str, Any] | None = None,
        start_sequence: int = 0,
        authorize: Callable[[dict[str, Any], dict[str, Any]], bool] | None = None,
    ):
        self.subscription_id = subscription_id
        self.scope_id = scope_id
        self.actor = actor
        self._event_source = event_source
        self._filter = filter_spec or {}
        self._cursor = start_sequence
        self._authorize = authorize or (lambda actor, event: True)
        self._closed = False
        self._lock = threading.RLock()
        self.opened_at = _now()
        self.closed_at: str | None = None
        self.close_reason: str | None = None

    def _matches_filter(self, event: dict[str, Any]) -> bool:
        f = self._filter
        if "event_classes" in f and event["event_type"] not in f["event_classes"]:
            return False
        if "object_id" in f and event.get("object_id") != f["object_id"]:
            return False
        if "object_type" in f:
            payload = event.get("payload") or {}
            if payload.get("object_type") != f["object_type"]:
                return False
        return True

    def poll(self, max_events: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            if self._closed:
                return []
            events = self._event_source(self.scope_id, self._cursor)
            delivered: list[dict[str, Any]] = []
            for event in events:
                if not self._matches_filter(event):
                    self._cursor = max(self._cursor, event["ledger_sequence"])
                    continue
                if not self._authorize(self.actor, event):
                    self._cursor = max(self._cursor, event["ledger_sequence"])
                    continue
                delivered.append(event)
                self._cursor = event["ledger_sequence"]
                if len(delivered) >= max_events:
                    break
            return delivered

    def acknowledge(self, ledger_sequence: int) -> None:
        with self._lock:
            self._cursor = max(self._cursor, ledger_sequence)

    def close(self, reason: str = "client_closed") -> None:
        with self._lock:
            if not self._closed:
                self._closed = True
                self.closed_at = _now()
                self.close_reason = reason

    @property
    def closed(self) -> bool:
        return self._closed

    def descriptor(self) -> dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "scope_id": self.scope_id,
            "actor": self.actor,
            "filter": self._filter,
            "start_sequence": self._cursor,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "close_reason": self.close_reason,
        }


class SubscriptionManager:
    def __init__(self):
        self._subs: dict[str, Subscription] = {}
        self._lock = threading.RLock()

    def open(
        self,
        scope_id: str,
        actor: dict[str, Any],
        event_source: Callable[[str, int], list[dict[str, Any]]],
        filter_spec: dict[str, Any] | None = None,
        start_sequence: int = 0,
        authorize: Callable[[dict[str, Any], dict[str, Any]], bool] | None = None,
    ) -> Subscription:
        sub_id = _new_id("sub")
        sub = Subscription(
            subscription_id=sub_id,
            scope_id=scope_id,
            actor=actor,
            event_source=event_source,
            filter_spec=filter_spec,
            start_sequence=start_sequence,
            authorize=authorize,
        )
        with self._lock:
            self._subs[sub_id] = sub
        return sub

    def close(self, subscription_id: str, reason: str = "client_closed") -> None:
        with self._lock:
            sub = self._subs.get(subscription_id)
            if sub is not None:
                sub.close(reason)

    def get(self, subscription_id: str) -> Subscription | None:
        with self._lock:
            return self._subs.get(subscription_id)
