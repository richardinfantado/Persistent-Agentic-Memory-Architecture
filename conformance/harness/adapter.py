"""Adapter interface for PAMSPEC conformance testing.

An adapter is the thin translation layer between the conformance
suite (which speaks the canonical PAMSPEC operation vocabulary) and
a specific implementation (which may be in-process Python, an HTTP
server, an MCP server, a subprocess CLI, etc.).

An adapter MUST:
- Implement every method the profile it targets requires.
- Translate the implementation's native exceptions into
  PamspecErrorLike so the suite can assert on stable error codes.
- Return envelope-shaped dicts using the field names in
  schemas/0.1-draft/*.schema.json.

An adapter SHOULD NOT:
- Cache or transform data in ways that would let a broken
  implementation appear conformant.
- Silently retry — retry policy is the suite's job.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Callable, Iterator


class PamspecErrorLike(Exception):
    """Portable error shape adapters raise on operation failure.

    Matches the wire form of schemas/0.1-draft/error.schema.json.
    """

    def __init__(self, code: str, message: str = "", retryable: bool = False, **details: Any):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details

    def __repr__(self) -> str:
        return f"PamspecErrorLike(code={self.code!r}, retryable={self.retryable})"


@contextmanager
def expect_error(code: str) -> Iterator[dict[str, Any]]:
    """Context manager for suite tests: fail unless the block raises
    PamspecErrorLike with the given code. Yields a dict the block
    can populate for post-error assertions.
    """
    box: dict[str, Any] = {}
    try:
        yield box
    except PamspecErrorLike as e:
        if e.code != code:
            raise AssertionError(
                f"expected error code {code!r}, got {e.code!r} (message: {e.message!r})"
            ) from None
        box["error"] = e
        return
    raise AssertionError(f"expected PamspecErrorLike code={code!r}, no error raised")


class Adapter(ABC):
    """Abstract PAMSPEC adapter.

    Every method takes normalized inputs (matching the operation
    schemas) and returns either a normalized result dict or raises
    PamspecErrorLike.
    """

    # ------------- Profile advertisement -------------

    @abstractmethod
    def supported_profiles(self) -> list[str]:
        """Return the list of PAMSPEC profile names this adapter supports."""

    # ------------- Core CRUD (PAMSPEC-Lite) -------------

    @abstractmethod
    def create(
        self,
        *,
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
    ) -> dict[str, Any]:
        """Create returns a dict with at least: object_id, version_id, sequence, envelope."""

    @abstractmethod
    def read(
        self, *, scope_id: str, object_id: str, version_id: str | None = None
    ) -> dict[str, Any]:
        """Read returns the envelope."""

    @abstractmethod
    def update(
        self,
        *,
        scope_id: str,
        object_id: str,
        expected_version_id: str,
        canonical_content: Any,
        actor: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        """Update returns {object_id, version_id, sequence, envelope}."""

    @abstractmethod
    def transition(
        self,
        *,
        scope_id: str,
        object_id: str,
        expected_version_id: str,
        dimension: str,
        target_state: str,
        actor: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        """Transition returns {object_id, version_id, sequence, envelope}."""

    @abstractmethod
    def delete(
        self,
        *,
        scope_id: str,
        object_id: str,
        expected_version_id: str,
        actor: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        """Delete returns {object_id, version_id (of tombstone), envelope}."""

    @abstractmethod
    def query(
        self,
        *,
        scope_id: str,
        object_type: str | None = None,
        lifecycle_state: str | None = "active",
        availability_state: str | None = "available",
        validation_state: str | None = "corroborated",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Query returns a list of envelopes."""

    @abstractmethod
    def history(self, *, scope_id: str, object_id: str) -> list[dict[str, Any]]:
        """Inspect object version history, oldest first."""

    # ------------- Delegation (P7) -------------

    def grant_delegation(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("adapter does not implement Delegation")

    def check_delegation(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("adapter does not implement Delegation")

    def revoke_delegation(self, delegation_id: str) -> None:
        raise NotImplementedError("adapter does not implement Delegation")

    # ------------- Subscribe (P6) -------------

    def subscribe(self, **kwargs: Any) -> Any:
        raise NotImplementedError("adapter does not implement Subscribe")

    def poll_subscription(self, subscription: Any, max_events: int = 100) -> list[dict[str, Any]]:
        raise NotImplementedError("adapter does not implement Subscribe")

    def close_subscription(self, subscription: Any, reason: str = "client_closed") -> None:
        raise NotImplementedError("adapter does not implement Subscribe")

    # ------------- Teardown -------------

    def close(self) -> None:
        """Optional cleanup between test cases."""
