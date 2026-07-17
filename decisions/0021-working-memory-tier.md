# Decision: Working Memory tier and Promote operation

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

MemGPT, Letta, LangGraph, and multi-agent frameworks all distinguish
short-lived per-task scratchpad state ("working memory") from
consolidated long-term memory. Each names it differently and stores
it differently. Agents that restart mid-task lose context because
this state either wasn't persisted or was persisted in a place that
polluted retrieval.

## Problem

Two failure modes:

1. Working memory lives only in the process; a crash or restart
   loses task progress even though the surrounding memory system is
   durable.
2. Working memory shares storage with consolidated memory and
   contaminates retrieval — the agent later "remembers" its own
   speculative scratchpad as if it were validated fact.

## Proposed Decision

- Add `working_memory` as a standard object type with a canonical
  content schema and a required `task_ref` linking to the task or
  session that owns it.
- Default it to `lifecycle_state = scratch`, which the existing
  spec already excludes from default trusted retrieval.
- Add a **Promote** operation that converts a working_memory object
  into a canonical Memory Object type (claim/decision/task/summary),
  transitions the source to `superseded`, and creates a
  `derived_from` Relationship Object between the two.

## Alternatives Considered

- Reuse `scratch` lifecycle on existing types: rejected because it
  conflates "half-baked claim" with "planning scratchpad" — different
  semantics, different lifetimes.
- Model working memory as an ephemeral session-only concept: rejected
  because durability across restarts is exactly the pain point.
- Model it inside Compute Plane, not Persistent State Plane: rejected
  because durability requires persistent storage, which is by
  definition PSP.

## Consequences

- Frameworks can standardize how their scratchpad state persists
  and interoperates.
- Consolidation from scratchpad to canonical memory becomes an
  explicit, auditable step rather than an implicit copy.
- Storage cost of working memory needs monitoring (see P5:
  cost/latency fields on the ledger).

## Interoperability Impact

Agent state can be handed off between frameworks and providers
without losing in-flight task progress.

## Security Impact

Because working memory is `scratch` and `unverified` by default,
prompt-injection content persisted here does not enter the trusted
retrieval path unless a promotion review approves it.

## Privacy Impact

Working memory frequently contains draft or intermediate content
with unresolved PII considerations. `ttl_hint_seconds` gives
implementations a signal for aggressive expiry.

## Unresolved Questions

- Should Promote be a distinct operation, or a shorthand for
  Create + Transition + Relate? Current answer: distinct, because
  the three-step form is not atomic across implementations.
- Should working_memory support a size limit at the schema level?

## References

- `schemas/0.1-draft/working-memory-content.schema.json`
- `test-vectors/valid/working-memory.json`
- `draft-infantado-agent-memory-architecture`, Type System and
  Operation Semantics sections
