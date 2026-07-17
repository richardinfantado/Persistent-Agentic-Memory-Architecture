# Decision: Optional attestation block on actor identity

## Status

Accepted for `-01` enhancement cycle.

## Date

2026-07-17

## Context

The industry is moving toward verifiable agent identity: agent
manifests, signed capabilities, sigstore-style provenance, W3C DIDs
for autonomous agents. Without a common home in PAMSPEC's `actor`
schema, this metadata would live outside the memory audit horizon.

## Problem

`actor` today is just `actor_id` + `actor_kind` + optional
`display_name`. In adversarial or federated contexts, "the agent
did X" is unattributable — the actor_id is a string, not a
verifiable claim.

## Proposed Decision

Extend `actor.schema.json` with:

- `on_behalf_of_actor_id`: the ultimate principal when the executor
  is not the source of authority.
- `delegation_id`: reference to a Delegation Object (P7) when the
  operation was authorized by explicit delegation.
- `attestation` block: optional verifiable identity data
  (agent_manifest_ref, manifest_digest, attestation_authority,
  attestation_method, signature, validity window,
  capabilities_declared, did_ref).

Attestation remains non-authoritative in the base profile. A future
profile may require attestation for `actor_kind = agent` in
regulated scopes.

## Alternatives Considered

- Model attestation as a separate object type: rejected because
  attestation is per-operation metadata; carrying it inside the
  actor block colocates it with the identity it attests.
- Wait for a settled standard (DIDs? OpenID for AI?): rejected
  because the shape here is minimal and additive; convergence on
  attestation methods can happen inside the `attestation_method`
  field over time.
- Require attestation now: rejected because the ecosystem is not
  ready and mandatory attestation would block adoption.

## Consequences

- PAMSPEC records now carry the primitives needed for supply-chain
  and identity verification of agent-authored memory.
- Auditors can trace "which build of which agent under whose
  authority" from memory data alone.
- Delegation Objects (P7) and attestation compose: an operation
  can carry both the granted-by trail and the who-am-I proof.

## Interoperability Impact

Actor semantics remain backward compatible; existing objects with
minimal `actor` blocks continue to validate. Federated deployments
gain a common shape for identity data.

## Security Impact

Reduces spoofing risk: recorded operations are cryptographically
attributable when attestation is present. Attestation validation
itself is out of scope for the schema; implementations perform
signature verification against the declared `attestation_authority`.

## Privacy Impact

Attestation may reference actor identity in ways that increase
identifiability. Redaction of the `attestation` block is permitted
under normal Availability State transitions.

## Unresolved Questions

- Should PAMSPEC define its own manifest schema, or reference an
  external one?
- Should attestation refresh be modeled as a new Memory Version, or
  as a distinct event class?

## References

- `schemas/0.1-draft/actor.schema.json`
- `test-vectors/valid/attested-agent-actor.json`
- ADR-0024 (Delegation Object)
- `draft-infantado-agent-memory-architecture`, Memory Object Model
