# Decision: Subscribe operation for reactive memory consumption

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

Long-running agents need to *react* to relevant memory changes, not
poll for them. Framework-specific hacks (background threads, cron
loops, database triggers) reinvent the same primitive badly.

## Problem

Without a first-class Subscribe operation:

- Polling defaults to either wasteful cadences or unacceptable
  latencies.
- Cross-implementation subscription semantics diverge (guarantees,
  filters, back-pressure), preventing interop.
- Authorization becomes stale — a subscriber that lost access to
  a scope may keep receiving events until the next poll.

## Proposed Decision

Add a **Subscribe** operation that:

- Streams Event Ledger entries matching a filter within a scope.
- Returns a `subscription_id`, resolved filter, `start_sequence`,
  and binding-specific `channel_ref`.
- Guarantees at-least-once delivery keyed by `event_id`.
- Preserves ordering within a scope.
- Re-evaluates authorization per event, not only at subscription
  time.
- Emits `subscription_opened` at start and `subscription_closed`
  at end (client-initiated or service-initiated).
- Supports an `after_sequence` catch-up mode for resumption after
  crash or network partition.

## Alternatives Considered

- Poll-only: rejected because latency and cost make it a
  non-starter for reactive agents.
- Notification hook per binding, no core operation: rejected
  because the guarantees and filter model would fragment.
- Exactly-once delivery: rejected because it is expensive to
  implement across storage backends; at-least-once + `event_id`
  deduplication is standard practice and sufficient.

## Consequences

- Turns PAMSPEC from a memory store into a memory nervous system.
- Bindings (MCP, HTTP/SSE, WebSocket, gRPC, message bus) map the
  channel differently but preserve the same semantics.
- Implementations must track subscriber ledger positions.

## Interoperability Impact

Reactive agent patterns become portable across PAMSPEC
implementations. The MCP binding (P2) already reserves
`pamspec.subscribe` with matching semantics.

## Security Impact

Per-event authorization re-evaluation prevents privilege drift
during long-lived subscriptions. Filters MUST NOT be used to
reveal existence of protected events.

## Privacy Impact

Subscription filters cannot be used to enumerate deleted or
redacted objects; the Availability State rules apply to
subscription delivery identically to query.

## Unresolved Questions

- Should there be a standard shape for the `predicate` field, or
  should it remain profile-defined?
- Should subscriptions survive service restart automatically, or
  require explicit re-subscription with `after_sequence`?

## References

- `schemas/0.1-draft/subscription.schema.json`
- `bindings/mcp/README.md`
- `draft-infantado-agent-memory-architecture`, Operation Semantics section
