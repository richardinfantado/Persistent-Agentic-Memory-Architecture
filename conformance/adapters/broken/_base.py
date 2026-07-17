"""Shared base for defective adapters: delegates every non-overridden
method to the reference adapter, so each broken adapter only needs to
override the one method whose contract it violates."""

from __future__ import annotations

from typing import Any

from conformance.adapters.reference_python import ReferencePythonAdapter
from conformance.harness.adapter import Adapter


class DelegatingReferenceAdapter(Adapter):
    """Adapter that delegates every method to a private ReferencePythonAdapter.

    Broken adapters subclass this and override just the one method whose
    contract they intentionally violate.
    """

    def __init__(self):
        self._ref = ReferencePythonAdapter(":memory:")

    def supported_profiles(self) -> list[str]:
        return self._ref.supported_profiles()

    def create(self, **kwargs) -> dict[str, Any]:
        return self._ref.create(**kwargs)

    def read(self, **kwargs) -> dict[str, Any]:
        return self._ref.read(**kwargs)

    def update(self, **kwargs) -> dict[str, Any]:
        return self._ref.update(**kwargs)

    def transition(self, **kwargs) -> dict[str, Any]:
        return self._ref.transition(**kwargs)

    def delete(self, **kwargs) -> dict[str, Any]:
        return self._ref.delete(**kwargs)

    def query(self, **kwargs) -> list[dict[str, Any]]:
        return self._ref.query(**kwargs)

    def history(self, **kwargs) -> list[dict[str, Any]]:
        return self._ref.history(**kwargs)

    def grant_delegation(self, **kwargs) -> dict[str, Any]:
        return self._ref.grant_delegation(**kwargs)

    def check_delegation(self, **kwargs) -> dict[str, Any]:
        return self._ref.check_delegation(**kwargs)

    def revoke_delegation(self, delegation_id: str) -> None:
        self._ref.revoke_delegation(delegation_id)

    def subscribe(self, **kwargs) -> Any:
        return self._ref.subscribe(**kwargs)

    def poll_subscription(self, subscription, max_events: int = 100) -> list[dict[str, Any]]:
        return self._ref.poll_subscription(subscription, max_events)

    def close_subscription(self, subscription, reason: str = "client_closed") -> None:
        self._ref.close_subscription(subscription, reason)

    def close(self) -> None:
        self._ref.close()
