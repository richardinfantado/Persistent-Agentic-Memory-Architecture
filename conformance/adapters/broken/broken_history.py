"""Broken adapter: drops unknown extension fields on read.

Violates: preservation of unknown fields across read/history.
Simulates a schema-strict implementation that silently strips any
canonical_content key it doesn't recognize (any key prefixed with
`x-` for the purposes of this control), and strips any unknown
top-level envelope key.

Suite case that MUST fail:
`case_unknown_extension_fields_preserved_on_read` in
`conformance.suite.test_lite`.
"""

from typing import Any

from ._base import DelegatingReferenceAdapter


class BrokenLosesUnknownExtensionFieldsAdapter(DelegatingReferenceAdapter):
    _KNOWN_ENVELOPE_KEYS = {
        "spec_version", "object_id", "version_id", "scope_id",
        "object_type", "canonical_content", "lifecycle_state",
        "availability_state", "retention_state", "validation_state",
        "committed_at", "recorded_at", "sequence", "actor",
        "provenance", "schema_id", "observed_at", "asserted_at",
        "valid_from", "valid_until", "relationship_refs", "integrity",
        "quality_signals",
    }

    def _strip_x_keys(self, obj: Any) -> Any:
        """Deeply strip keys with the `x-` prefix from dicts, and drop
        unknown top-level envelope keys. Simulates an over-strict
        schema-enforcing consumer."""
        if isinstance(obj, dict):
            return {
                k: self._strip_x_keys(v)
                for k, v in obj.items()
                if not (isinstance(k, str) and k.startswith("x-"))
            }
        if isinstance(obj, list):
            return [self._strip_x_keys(v) for v in obj]
        return obj

    def _strip(self, envelope: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(envelope, dict):
            return envelope
        clean = {k: v for k, v in envelope.items() if k in self._KNOWN_ENVELOPE_KEYS}
        if "canonical_content" in clean:
            clean["canonical_content"] = self._strip_x_keys(clean["canonical_content"])
        return clean

    def read(self, **kwargs) -> dict[str, Any]:
        return self._strip(self._ref.read(**kwargs))

    def history(self, **kwargs) -> list[dict[str, Any]]:
        return [self._strip(e) for e in self._ref.history(**kwargs)]
