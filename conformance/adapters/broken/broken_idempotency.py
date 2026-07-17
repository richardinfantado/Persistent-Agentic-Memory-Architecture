"""Broken adapter: reuses idempotency keys silently.

Violates: idempotency-key contract. `create` with a previously-used
idempotency_key and a DIFFERENT body silently accepts the new body
instead of raising `duplicate_operation`.

Suite case that MUST fail:
`case_idempotent_key_reuse_with_different_body_fails` in
`conformance.suite.test_lite`.
"""

from typing import Any

from conformance.harness.adapter import PamspecErrorLike

from ._base import DelegatingReferenceAdapter


class BrokenReusesIdempotencyKeyAdapter(DelegatingReferenceAdapter):
    def create(self, **kwargs) -> dict[str, Any]:
        try:
            return self._ref.create(**kwargs)
        except PamspecErrorLike as e:
            if e.code == "duplicate_operation":
                # Swallow the duplicate-operation error and create
                # anyway (without the idempotency key), simulating a
                # broken implementation that "helpfully" retries.
                retry_kwargs = dict(kwargs)
                retry_kwargs.pop("idempotency_key", None)
                return self._ref.create(**retry_kwargs)
            raise
