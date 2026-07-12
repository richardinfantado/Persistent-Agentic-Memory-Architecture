# Decision: Canonical Content Shape

## Status

Accepted for the semantic consistency pass.

## Proposed Decision

Canonical Content MAY be any JSON value. `schema_id` defines type-specific validation and interpretation.

## Alternatives Considered

- Requiring an object wrapper was rejected because scalar, array, and reference-oriented content would need artificial wrappers.

## Consequences

Canonical serialization is not defined by this revision. Integrity hashes therefore identify the declared canonicalization profile when hashes cover Canonical Content.

## Interoperability Impact

Implementations can preserve scalar, array, object, boolean, number, string, and null content.

## Security Impact

Consumers validate content against the declared schema and do not assume object-shaped data.

## Privacy Impact

All JSON shapes remain subject to scope and disclosure controls.

## Unresolved Questions

- Canonical JSON serialization remains future work.

