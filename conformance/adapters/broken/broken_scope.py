"""Broken adapter: ignores scope isolation on read.

Violates: scope isolation. `read(scope_id=B, object_id=X)` where X
was created in scope A returns the envelope instead of raising
`object_not_found`.

Suite case that MUST fail: `case_scope_isolation` in
`conformance.suite.test_lite`.
"""

from typing import Any

from conformance.harness.adapter import PamspecErrorLike

from ._base import DelegatingReferenceAdapter


class BrokenIgnoresScopeAdapter(DelegatingReferenceAdapter):
    def read(self, *, scope_id: str, object_id: str, version_id: str | None = None) -> dict[str, Any]:
        try:
            return self._ref.read(scope_id=scope_id, object_id=object_id, version_id=version_id)
        except PamspecErrorLike as e:
            if e.code == "object_not_found":
                # Deliberate leak: try any scope by falling back to the
                # underlying service search across all scopes.
                for cand_scope in self._all_known_scopes():
                    try:
                        return self._ref.read(scope_id=cand_scope, object_id=object_id, version_id=version_id)
                    except PamspecErrorLike:
                        continue
            raise

    def _all_known_scopes(self) -> list[str]:
        svc = self._ref._svc
        rows = svc._conn.execute("SELECT DISTINCT scope_id FROM memory_versions").fetchall()
        return [r["scope_id"] for r in rows]
