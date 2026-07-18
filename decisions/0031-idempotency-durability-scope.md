# Decision: Idempotency Durability Scope (OD-C4)

## Status

Accepted

## Date

2026-07-19

## Context

R8 formalized CR-6 (Idempotency) and left OD-C4 open: does Core idempotency require cross-process atomicity (preventing duplicate creates when two concurrent processes race on the same idempotency key), or is durability across a single process restart sufficient?

R5 evidence proved restart durability via the SQLite sidecar (`r5.idempotency_restart_durable`). Cross-process concurrent idempotency was not tested and was recorded as a known gap.

## Problem

Two deployment models exist for a PAMSPEC Memory Service:

1. **Server model** — a single Memory Service process handles all concurrent callers. Multiple agents each connect to one server; the server serializes all operations internally.
2. **Embedded library model** — each agent process embeds its own Memory Service instance, possibly sharing a backing store (e.g., SQLite file) across processes.

Cross-process idempotency atomicity (preventing races when two embedded instances process the same idempotency key at the same instant) requires SERIALIZABLE database isolation or external distributed locking. This is a significant implementation constraint.

## Proposed Decision

**CR-6 requires durability across process restart, not cross-process concurrent atomicity.**

Rationale:
- PAMSPEC's architectural model is a single authoritative Memory Service (analogous to a database server). Concurrent callers connect to one service; internal concurrency is the service's concern, not the specification's.
- The at-least-once delivery scenario that motivates idempotency is agent retry on transport failure — a second sequential attempt by the same caller, not a simultaneous race by two independent processes.
- Making cross-process atomicity a Core requirement would impose distributed transaction semantics on all implementations, eliminating embedded/library deployments.
- The reference-python implementation and Mem0EnforcementAdapter both operate as single-server deployments; restart durability is proven.

**Normative statement added to draft §Consistency and Concurrency:**
> The idempotency record MUST be durable: it MUST survive the Memory Service process restarting with the same persistent store.

Cross-process concurrent idempotency atomicity is a deployment quality concern. Implementations that expose a shared backing store to multiple concurrent processes SHOULD document their atomicity guarantees; this document does not require any specific guarantee beyond restart durability.

## Alternatives Considered

**Cross-process required** — Would require SERIALIZABLE isolation or external locking. Eliminates embedded deployments. Evidence from R5 does not cover this scenario; it would require a new test milestone before evidence could be considered confirmed. Rejected as overly constraining for Core.

## Consequences

- The draft's idempotency section gains one normative MUST for durability.
- OD-C4 is closed. The known gap (cross-process atomicity not tested) is documented in the draft's Security Considerations as a deployment concern.
- No implementation changes required. Reference-python and Mem0EnforcementAdapter both already satisfy restart durability via SQLite.

## Interoperability Impact

Implementations that use only in-memory idempotency state (e.g., a dict that disappears on restart) do not conform to Core. Persistent storage (SQLite, file, database) is required for the idempotency store. This is a real constraint that eliminates stateless or purely in-memory implementations.

## Security Impact

Durable idempotency prevents replay attacks across restarts. An attacker who causes a service restart cannot re-create a previously idempotency-guarded object with different content — the key is still on record after restart.

## Privacy Impact

Idempotency records associate `(idempotency_key, content_hash, object_id)`. The key is caller-supplied; implementations MUST treat keys as potentially sensitive and apply the same access controls as the associated object.

## Open Questions

None. OD-C4 is resolved.

## References

- R8 `R8-OPEN-DECISIONS.md` OD-C4
- R5 evidence `r5.idempotency_restart_durable` (`validation/evidence/mem0-r5-portability.jsonl`)
- R8 `R8-EVIDENCE-MAPPING.md` CR-6 Known Limitation
