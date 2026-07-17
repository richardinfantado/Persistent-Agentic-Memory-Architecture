"""Adapter that plugs the Python reference implementation into the
conformance harness. Serves as the ground-truth adapter and as the
worked example for anyone writing an adapter for a different
implementation.
"""

from __future__ import annotations

from typing import Any

from pamspec_ref import MemoryService, PamspecError

from conformance.harness.adapter import Adapter, PamspecErrorLike


def _rewrap(fn):
    """Translate pamspec_ref.PamspecError into PamspecErrorLike so
    the suite can assert on stable codes without touching the
    reference impl's exception type.
    """
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except PamspecError as e:
            raise PamspecErrorLike(
                code=e.code,
                message=e.message,
                retryable=e.retryable,
                **e.details,
            ) from None
    return wrapped


class ReferencePythonAdapter(Adapter):
    def __init__(self, db_path: str = ":memory:"):
        self._svc = MemoryService(db_path)

    def supported_profiles(self) -> list[str]:
        return ["PAMSPEC-Lite", "PAMSPEC-Delegation", "PAMSPEC-Subscribe"]

    # ---- Lite ----

    @_rewrap
    def create(self, **kwargs):
        return self._svc.create(**kwargs)

    @_rewrap
    def read(self, **kwargs):
        return self._svc.read(**kwargs)

    @_rewrap
    def update(self, **kwargs):
        return self._svc.update(**kwargs)

    @_rewrap
    def transition(self, **kwargs):
        return self._svc.transition(**kwargs)

    @_rewrap
    def delete(self, **kwargs):
        return self._svc.delete(**kwargs)

    @_rewrap
    def query(self, **kwargs):
        return self._svc.query(**kwargs)

    @_rewrap
    def history(self, **kwargs):
        return self._svc.history(**kwargs)

    # ---- Delegation ----

    @_rewrap
    def grant_delegation(self, **kwargs):
        return self._svc.delegations().grant(**kwargs)

    @_rewrap
    def check_delegation(self, **kwargs):
        return self._svc.delegations().check(**kwargs)

    @_rewrap
    def revoke_delegation(self, delegation_id: str) -> None:
        self._svc.delegations().revoke(delegation_id)

    # ---- Subscribe ----

    @_rewrap
    def subscribe(self, *, scope_id: str, actor: dict[str, Any],
                  filter_spec: dict[str, Any] | None = None,
                  start_sequence: int = 0):
        return self._svc.subscribe(
            scope_id=scope_id, actor=actor,
            filter_spec=filter_spec, start_sequence=start_sequence,
        )

    @_rewrap
    def poll_subscription(self, subscription, max_events: int = 100):
        return subscription.poll(max_events=max_events)

    def close_subscription(self, subscription, reason: str = "client_closed") -> None:
        subscription.close(reason)

    # ---- Teardown ----

    def close(self) -> None:
        try:
            self._svc.close()
        except Exception:
            pass
