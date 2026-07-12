# Decision: Temporal Semantics and Clock Model

## Status

Accepted for the semantic consistency pass.

## Proposed Decision

PAMSPEC distinguishes `observed_at`, `asserted_at`, `valid_from`, `valid_until`, `committed_at`, `recorded_at`, and logical `sequence`.

Client-supplied observation and assertion times are untrusted claims unless validated. The Memory Service assigns `committed_at`, `recorded_at`, and the ordering sequence. Event ordering does not rely only on wall-clock time.

## Alternatives Considered

- Generic `created_at` and `updated_at` were rejected because they conflate observation, assertion, and commit semantics.

## Consequences

Temporal queries explicitly select valid time, observation time, commit time, or event sequence.

## Interoperability Impact

Replay and temporal evaluation no longer depend on ambiguous timestamps.

## Security Impact

Future timestamps, clock skew, forged observation times, and time-zone ambiguity are treated explicitly.

## Privacy Impact

Fine-grained timestamps can reveal activity patterns and remain scope-controlled.

## Unresolved Questions

- Profiles may define precision minimization for privacy.

