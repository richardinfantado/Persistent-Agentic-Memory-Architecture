# Working Memory — cross-framework evidence note

R8 required a short comparison across Mem0, Letta, LangGraph, and current PAMSPEC Working Memory, answering only whether there is enough shared behavior to justify a portable Working Memory concept.

## Observations

| Framework | Working / short-term memory | Long-term memory | Same API surface? |
|---|---|---|---|
| **Mem0 OSS 2.0.12** | No distinct working-memory tier. `Memory.add` writes to the single memory store; there is no "session-scoped" vs "long-term" separation at the API. | Same store as the above. | N/A (one tier only) |
| **LangGraph** | Short-term memory is `Checkpointer`-based — per-thread state persisted at checkpoint boundaries, distinct from long-term memory. | Long-term memory is `Store`-based — cross-thread, namespaced. Different API from checkpointers. | **No.** Different APIs, different lifecycle, different consumers. |
| **Letta** | Uses persistent `MemoryBlock` structures that are **always present in the agent's context**. The "working" property is contextual availability, not a distinct storage tier. | Long-term recall via archival memory (separate storage). | Partial — both are memory objects, but they play very different roles at runtime. |
| **PAMSPEC Working Memory (current, experimental)** | `working_memory` object type with `task_ref`, `purpose`, `ttl_hint_seconds`, `promotion_hint`; distinguished by `lifecycle_state: scratch`. | Standard object types (`claim`, `decision`, etc.) with `lifecycle_state: active` and up. | Yes — same envelope, same operations, distinguished by `lifecycle_state` and `object_type`. |

## Verdict

**Partially, keep experimental.**

Reasoning:

- Mem0 has no working-memory concept at all. Portability would require Mem0 to add one, or PAMSPEC to declare that a Mem0-conformant adapter has no working-memory support (i.e. the property is optional across the ecosystem).
- LangGraph's split is at the *API* level (`Checkpointer` vs `Store`), not just a field on a common envelope. A PAMSPEC Working Memory type on a common envelope cannot round-trip cleanly to two different LangGraph APIs.
- Letta's blocks are always-in-context, which is a *retrieval-eligibility* property more than a storage-tier property.

The frameworks disagree on *what working memory is*. Mem0 has none; LangGraph splits by API; Letta splits by contextual availability. A single portable Working Memory schema would either paper over the disagreement or force framework changes.

**Recommended action:** keep Working Memory in `experimental/` per ADR-0029 §3.4. **Do not move working-memory files in R4b or later**. Graduation to a profile requires:

1. At least two framework adapters (not one) demonstrating shared behavior that a common schema captures.
2. An explicit adopter statement that they'd use the portable form.

## No schema changes

Per R8's constraint on this branch, no schema changes are made. This is an evidence note only.
