# Decision: Memory Object Type Extension Model

## Status

Accepted for the semantic consistency pass.

## Proposed Decision

Standard types are `claim`, `decision`, `task`, `artifact`, `observation`, `entity`, `relationship`, and `summary`.

Extension types use a collision-resistant reverse-domain name or absolute URI, such as `com.example.incident-assessment`.

An extension type MUST include `schema_id`. Implementations MUST preserve unknown extension types during export and import. Creation MAY reject unsupported types. A reader SHOULD return the canonical envelope even when extension content is uninterpreted, subject to policy.

## Alternatives Considered

- A closed enumeration was rejected because it makes extensibility non-functional.
- Unnamespaced short extension names were rejected because they invite collisions.

## Consequences

The object schema permits standard values or extension identifiers.

## Interoperability Impact

Unknown types remain portable without requiring every implementation to interpret them.

## Security Impact

Readers must not execute or trust unknown content solely because it was preserved.

## Privacy Impact

Unknown extension data remains subject to normal scope and disclosure policy.

## Unresolved Questions

- A future registry could replace purely decentralized namespacing.

