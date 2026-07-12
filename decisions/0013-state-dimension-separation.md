# Decision: State Dimension Separation

## Status

Accepted for the semantic consistency pass.

## Date

2026-07-12

## Context

Lifecycle maturity, content availability, retention policy, and validation confidence were represented by overlapping values.

## Problem

Using `redacted`, `deleted`, `expired`, or `legal_hold` as lifecycle values makes transitions ambiguous and prevents consistent filtering and enforcement.

## Proposed Decision

PAMSPEC defines four independent authoritative dimensions:

- Lifecycle State: `scratch`, `candidate`, `active`, `superseded`, `deprecated`, `archived`.
- Availability State: `available`, `partially_redacted`, `redacted`, `deleted`.
- Retention State: `retained`, `expired`, `pending_deletion`, `legal_hold`.
- Validation State: `unverified`, `corroborated`, `disputed`, `rejected`.

Every authoritative change to any dimension creates a new Memory Version and Event Ledger entry.

## Alternatives Considered

- A single status field was rejected because it combines unrelated policy dimensions.
- Treating redaction and deletion as lifecycle maturity was rejected because availability is independent from maturity.

## Consequences

Queries, schemas, transition tables, and tombstone behavior require separate fields and transition validation.

## Interoperability Impact

Implementations can exchange state without guessing whether a value governs maturity, access, retention, or validation.

## Security Impact

Authorization and legal-hold enforcement can be evaluated without overloading lifecycle semantics.

## Privacy Impact

Redaction, deletion, expiration, and legal hold become independently testable.

## Unresolved Questions

- Future profiles may restrict supported transitions by object type.

