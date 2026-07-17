# Decision: PAMSPEC-Lite conformance profile and reference implementation

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

PAMSPEC-Core requires all four state dimensions, full Event Ledger event
classes, and multi-profile capability. That is the right target for
enterprise or platform implementations. It is a discouraging target for a
single developer who wants to try the architecture on a prototype.

Specifications gain adoption when the first hour of trying them is easy.

## Problem

The lowest-effort path today for an agent developer is "write a JSON blob
to Postgres and hope future me can figure it out." PAMSPEC needs a profile
that is smaller than that in mental cost while still being genuinely
conformant.

## Proposed Decision

Define **PAMSPEC-Lite** as a minimal profile requiring only: scope
enforcement, canonical envelope, subset lifecycle/availability/retention/
validation values, expected-version concurrency, idempotency, and an
append-only Event Ledger. Provide a Python reference implementation
(`implementations/reference-python/`) that satisfies PAMSPEC-Lite in
under 500 lines of SQLite-backed code, with a passing test suite.

## Alternatives Considered

- Only ship PAMSPEC-Core: rejected because on-ramp friction blocks
  adoption in exactly the population (indie agent devs) that needs the
  interop story most.
- Ship many small profiles (Lite, Micro, Nano): rejected as premature —
  one on-ramp profile is enough evidence that layered conformance works.
- Publish a reference impl without a distinct profile: rejected because
  a reference impl needs a normative target to be reference *of*.

## Consequences

- Adopters can be conformant in an afternoon and grow into fuller profiles.
- The reference implementation becomes the executable definition of the
  minimal semantics — spec ambiguity gets caught by test failures.
- Documentation must clearly mark which profile each artifact targets.

## Interoperability Impact

Any implementation that satisfies a larger profile can import from
PAMSPEC-Lite exports without translation. PAMSPEC-Lite exports omit
fields that only larger profiles produce, so importers must accept
missing optional fields.

## Security Impact

Because PAMSPEC-Lite omits redaction and legal hold, it is not
appropriate for regulated deployments; the profile documentation must
say so explicitly.

## Privacy Impact

Deletion is available (tombstone), but the absence of redaction means
partial erasure requires promotion to a fuller profile.

## Unresolved Questions

- Should there be a formal "conformance report" template implementations
  submit against a profile?
- Should the reference implementation be dual-licensed or bundled with
  a friendlier license (currently follows repo licensing)?

## References

- `implementations/reference-python/`
- `draft-infantado-agent-memory-architecture`, Interoperability and Conformance section
- ADR-0006 (Version creation rules)
