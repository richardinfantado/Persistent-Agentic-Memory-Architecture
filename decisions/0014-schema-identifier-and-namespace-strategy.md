# Decision: Schema Identifier and Namespace Strategy

## Status

Accepted for the semantic consistency pass.

## Proposed Decision

Schema identifiers use:

`https://raw.githubusercontent.com/richardinfantado/Persistent-Agentic-Memory-Architecture/main/schemas/0.1-draft/`

The long-term candidate namespace is `https://pamspec.org/schema/`, but it is not used until the domain is acquired and configured.

Schema IDs include the schema profile version and remain unique.

## Alternatives Considered

- `example.invalid` was rejected because it is not a public resolvable namespace.
- An unversioned `main/schemas/` namespace was rejected because it cannot identify incompatible schema revisions.

## Consequences

The repository maintains versioned schema files under `schemas/0.1-draft/`.

## Interoperability Impact

Schema discovery and version declaration become deterministic.

## Security Impact

Consumers should still pin reviewed schema content rather than trusting mutable network retrieval.

## Privacy Impact

No direct privacy impact.

## Unresolved Questions

- Migration to a future `pamspec.org` namespace requires a separate ADR.

