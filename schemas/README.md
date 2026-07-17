# PAMSPEC Schema Profile

The active candidate schema profile is `0.1-draft` under [`0.1-draft/`](0.1-draft/).

Schema status warnings are expressed through schema `$comment`, `description`, and profile metadata. PAMSPEC instance data does not carry repository-development warning fields.

Schema IDs use the provisional public namespace:

`https://raw.githubusercontent.com/richardinfantado/Persistent-Agentic-Memory-Architecture/main/schemas/0.1-draft/`

## Files in `0.1-draft/`

| Schema | Purpose |
| --- | --- |
| `common.schema.json` | Shared definitions: `id`, `timestamp`, state enums, `standard_object_type`, `extension_object_type`, `pamspec_operation`, `integrity`, `quality_signals` |
| `memory-object.schema.json` | Canonical Memory Object envelope |
| `relationship.schema.json` | Independently identified, versioned Relationship Objects |
| `provenance.schema.json` | Provenance record (informatively aligned with W3C PROV) |
| `actor.schema.json` | Actor with optional `on_behalf_of_actor_id`, `delegation_id`, `attestation` |
| `memory-event.schema.json` | Event Ledger entry with optional `resource_usage` accounting |
| `memory-scope.schema.json` | Memory Scope descriptor |
| `embedding-space.schema.json` | Embedding Space identity descriptor |
| `query.schema.json` | Structured / semantic / hybrid query descriptor |
| `error.schema.json` | Transport-neutral error envelope |
| `delegation.schema.json` | Delegation Object (P7) |
| `subscription.schema.json` | Subscription descriptor (P6) |
| `evaluation-snapshot.schema.json` | Sealed evaluation snapshot (P10) |
| `tool-invocation-content.schema.json` | Canonical content for `tool_invocation` type (P3) |
| `tool-result-content.schema.json` | Canonical content for `tool_result` type (P3) |
| `working-memory-content.schema.json` | Canonical content for `working_memory` type (P4) |

## Validation

```sh
python scripts/validate_test_vectors.py
python scripts/validate_repository.py
```

All schemas are Draft 2020-12 JSON Schema. Cross-schema references use `$ref` with relative URIs against the shared `$id` namespace.
