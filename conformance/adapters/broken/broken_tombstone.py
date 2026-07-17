"""Broken adapter: returns deleted-object content after tombstone.

Violates: tombstone semantics. After a `delete`, a subsequent
`read` returns the previous envelope instead of raising
`object_deleted`.

Suite case that MUST fail:
`case_delete_creates_tombstone_and_blocks_default_read` in
`conformance.suite.test_lite`.
"""

from typing import Any

from conformance.harness.adapter import PamspecErrorLike

from ._base import DelegatingReferenceAdapter


class BrokenReadsDeletedObjectAdapter(DelegatingReferenceAdapter):
    def read(self, *, scope_id: str, object_id: str, version_id: str | None = None) -> dict[str, Any]:
        try:
            return self._ref.read(scope_id=scope_id, object_id=object_id, version_id=version_id)
        except PamspecErrorLike as e:
            if e.code == "object_deleted":
                # Recover the last non-deleted version from history and
                # return it. Simulates a broken impl that "helpfully"
                # returns the last known content instead of the tombstone.
                history = self._ref.history(scope_id=scope_id, object_id=object_id)
                for env in reversed(history):
                    if env.get("availability_state") != "deleted":
                        return env
            raise
