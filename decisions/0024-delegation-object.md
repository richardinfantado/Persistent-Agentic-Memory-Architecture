# Decision: Delegation Object for auditable multi-agent handoff

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

Multi-agent systems (supervisor/worker, planner/executor, critic
loops) constantly have Agent A operate on memory on behalf of
Agent B or a human principal. Today this authority transfer is
implicit — either both agents share a service account, or one
agent silently uses another's credentials.

## Problem

Implicit delegation is a confused-deputy factory:

- The Ledger records the delegate as the actor, losing the fact
  that they acted on behalf of another.
- There is no bounded time window, so a compromised sub-agent
  can act indefinitely.
- There is no way to scope authority to a subset of operations
  or objects.
- Revocation requires side-channel signaling.

## Proposed Decision

Introduce a **Delegation Object** as a first-class, independently
versioned authoritative object type with its own schema
(`delegation.schema.json`). Fields include `granting_actor`,
`delegated_actor`, `granted_operations`, optional
`granted_object_types`/`granted_object_ids`, optional
`target_scope_id` for cross-scope grants, required `policy_basis`,
`not_before`/`not_after`, `usage_limit`, and `revocable` flag.

Every exercise of a delegation MUST reference `delegation_id` in
provenance. Event Ledger records `delegation_granted`,
`delegation_revoked`, and `delegation_exercised`.

## Alternatives Considered

- Model delegation as a Relationship Object (`actor -delegates_to->
  actor`): rejected because relationships don't carry time bounds
  or operation restrictions naturally, and lumping delegation with
  content-relationships weakens both.
- Rely on external OAuth/OIDC token exchange: rejected because it
  keeps the delegation record out of PAMSPEC's audit horizon,
  defeating the point.
- Do nothing, let implementations handle it: rejected because
  cross-implementation delegation portability is a real need for
  federated agent systems.

## Consequences

- Auditors can reconstruct "who really asked for this" from the
  Ledger alone.
- Sub-agent compromise has a bounded blast radius (time, operations,
  objects).
- Implementations gain a common vocabulary for capability-scoped
  agent authority.

## Interoperability Impact

Multi-agent handoff becomes portable across frameworks and
providers. A supervisor built on LangGraph can hand off to a worker
in an OpenAI Agents SDK deployment through a Delegation Object
without loss of audit trail.

## Security Impact

Directly addresses the confused-deputy risk called out in the
spec's Security Considerations. Time-bounded, scope-bounded,
operation-bounded, and revocable delegations are the strongest
defensive posture short of a full capability system.

## Privacy Impact

The delegated actor's identity is recorded on every exercised
operation. Where privacy considerations require, the delegation
record can be redacted (via existing Availability State) while
the operational events stand.

## Unresolved Questions

- Should transitive delegation (delegate re-delegates) be allowed
  by default or require explicit policy?
- Should the schema express *deny* rules (forbidden operations)
  as well as grants?

## References

- `schemas/0.1-draft/delegation.schema.json`
- `test-vectors/valid/delegation.json`
- `draft-infantado-agent-memory-architecture`, Security Considerations section
