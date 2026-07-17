"""Three defective adapters that violate versioning contracts."""

from __future__ import annotations

from typing import Any

from conformance.harness.adapter import PamspecErrorLike

from ._base import DelegatingReferenceAdapter


class BrokenSilentOverwriteAdapter(DelegatingReferenceAdapter):
    """Violates: distinct version identity on update.

    `update` returns the *same* version_id as before instead of a new
    one. Version history is silently overwritten.

    Suite case that MUST fail: `case_update_creates_new_version` in
    `conformance.suite.test_lite`.
    """

    def update(self, **kwargs) -> dict[str, Any]:
        result = self._ref.update(**kwargs)
        # Force the returned version_id back to the caller's expected
        # (stale) version, discarding version distinctness.
        stale = kwargs["expected_version_id"]
        env = dict(result.get("envelope", {}))
        env["version_id"] = stale
        return {**result, "version_id": stale, "envelope": env}


class BrokenNonMonotonicSequenceAdapter(DelegatingReferenceAdapter):
    """Violates: strictly increasing sequence within an object's version history.

    `history` returns versions with non-monotonic sequence numbers.

    Suite case that MUST fail: `case_history_is_monotonic` in
    `conformance.suite.test_lite`.
    """

    def history(self, **kwargs) -> list[dict[str, Any]]:
        rows = self._ref.history(**kwargs)
        # Assign each row the same sequence number (=1), violating
        # strict monotonicity.
        broken = []
        for row in rows:
            r = dict(row)
            r["sequence"] = 1
            broken.append(r)
        return broken


class BrokenAcceptsStaleExpectedVersionAdapter(DelegatingReferenceAdapter):
    """Violates: expected-version conflict semantics.

    `update` with a stale expected_version_id silently succeeds instead
    of raising `version_conflict` — swallows the conflict and applies
    the caller's write over whatever is current.

    Suite case that MUST fail:
    `case_stale_expected_version_raises_version_conflict` in
    `conformance.suite.test_lite`.
    """

    def update(self, **kwargs) -> dict[str, Any]:
        try:
            return self._ref.update(**kwargs)
        except PamspecErrorLike as e:
            if e.code == "version_conflict":
                # Silently retry with the current version id from the error.
                current = e.details.get("current_version_id")
                if current is not None:
                    kwargs = dict(kwargs)
                    kwargs["expected_version_id"] = current
                    return self._ref.update(**kwargs)
            raise
