# Decision: Optional cost and latency fields on Event Ledger entries

## Status

**Superseded by ADR-0029 (§3.5) and executed by R4a.** The `resource_usage` block introduced by this ADR was removed from `memory-event.schema.json` because the fields it carried (input/output tokens, cached tokens, wall-clock and compute ms, cost amount/currency/unit, region_ref) are billing and observability telemetry, not persistent-memory semantics — they fail gate 1 of the anti-drift rule ("persistent-memory boundary"). Two fields (`model_ref`, `provider_ref`) were also removed from the observability-oriented block; their possible role as optional provenance-generation context is an R5 decision and MUST NOT be revived in a `resource_usage`-shaped block. This ADR is retained as historical record; it does not describe current repository state.

## Original date

2026-07-17

## Superseded on

2026-07-18

## Context

Enterprise adoption of agent systems is bottlenecked by cost visibility:
"how much did this agent cost, per user, per task, per decision?" Every
framework and provider answers this differently. Because PAMSPEC already
records every state-changing operation as an Event Ledger entry, cost
and latency accounting is one small schema extension away.

## Problem

Cost, latency, token counts, and model attribution are currently either
absent, buried in provider-specific traces, or wedged into ad-hoc
application tables. Cross-provider and per-scope budget analysis is
therefore an integration project.

## Proposed Decision

Add an optional `resource_usage` block to `memory-event.schema.json`
with well-defined fields:

- `input_tokens`, `output_tokens`, `cached_input_tokens`
- `wall_clock_ms`, `compute_ms`
- `cost_amount`, `cost_currency` (ISO 4217), `cost_unit` (for non-currency)
- `model_ref`, `provider_ref`, `region_ref`

All fields optional. Absence carries no meaning. The block is
non-authoritative — its presence does not change any authoritative
state and its absence does not invalidate an event.

Also add three new event types related to enhancements in this cycle:
`working_memory_promoted` (P4), `tool_invoked`, and `tool_completed`
(P3). None require a `version_id` because they are correlated with
existing object events.

## Alternatives Considered

- Put cost/latency on Memory Object versions: rejected because a single
  version can be produced by an operation involving multiple model
  calls (a chain-of-thought that eventually commits one decision); the
  event is the right granularity.
- Standardize a full billing schema: rejected because pricing models
  (per-token, per-second, per-request, credits) vary; the minimal
  fields cover the analytics use case without freezing pricing shape.
- Delegate entirely to observability tools: rejected because
  observability data typically doesn't survive PAMSPEC's audit horizon
  and lacks the scope/actor context PAMSPEC provides for free.

## Consequences

- Per-scope, per-actor, per-task cost roll-up becomes a query over the
  Event Ledger.
- Model-provider comparisons are apples-to-apples once populated.
- Implementations that don't record these fields remain fully conformant.

## Interoperability Impact

Cost/latency data now has a shared vocabulary. Exports carry
observability signals through migration.

## Security Impact

`cost_amount` may itself be sensitive (revealing usage patterns);
recommend the same scope-based access controls that protect other
event fields.

## Privacy Impact

No new personal data is introduced by these fields.

## Unresolved Questions

- Should `resource_usage` also appear on Memory Version envelopes for
  operations that produce large one-shot creates? Deferred; the event
  answer is sufficient for now.
- Should a currency-conversion profile be defined for cross-currency
  roll-ups? Deferred to implementations.

## References

- `schemas/0.1-draft/memory-event.schema.json`
- `test-vectors/valid/event-with-resource-usage.json`
