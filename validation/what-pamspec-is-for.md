# What PAMSPEC is for

*Written after the R8 Mem0 evidence. Word count: below 500.*

## 1. What PAMSPEC standardizes

PAMSPEC standardizes **how persistent agent memory remains trustworthy while it evolves across runtimes.** Its subject is the correctness of the authoritative memory record across create, update, retrieve, delete, and history operations — not storage layout, not transport, not embedding quality, not extraction quality.

Concretely, PAMSPEC's normative Lite core requires: stable object identity, immutable version identity with monotonic ordering, immutable scope, minimal provenance, expected-version conflict rejection, idempotent create, deterministic deletion with tombstone semantics, and a distinction between authoritative state and derived artifacts (vectors, summaries, indexes, caches).

## 2. Why a versioned document store is insufficient

A versioned document store preserves records. It does not define:

- whether scope stays fixed when metadata is edited,
- whether concurrent updates must yield to expected-version checks,
- whether identical creates are idempotent,
- whether deletion prevents stale-reference resurrection,
- whether derived artifacts (vectors, summaries, retrieval projections) refresh when authoritative content changes.

Against Mem0 OSS 2.0.12, R8 measured: scope mutation via `update()` silently succeeds; no expected-version parameter exists; no idempotency-key parameter exists; and `update(memory_id, text=...)` does not refresh the vector index, so `search()` returns the memory for both the old and new content simultaneously. Any agent relying on retrieval acts on stale beliefs.

## 3. Which behavior is uniquely memory-specific

Two clusters emerged as PAMSPEC's defensible distinct contribution:

- **Stable identity + strict update contract.** Immutable scope, distinct version identity, expected-version conflict rejection, idempotency-key semantics. These are correctness properties on the *authoritative* update path that generic CRUD does not require.
- **Authoritative-vs-derived integrity.** When authoritative memory changes, derived artifacts must be refreshed, invalidated, or explicitly declared stale. Silent divergence is the failure mode PAMSPEC is well-positioned to prevent.

## 4. Which behavior PAMSPEC explicitly does not standardize

- Storage engines, vector-store choice, embedding model choice.
- Transport, wire framing, or connection protocol.
- Identity, authorization, delegation, sharing, cryptographic erasure.
- Billing, cost accounting, latency, observability telemetry.
- Cognitive memory taxonomy as normative wire types.
- Runtime coordination between agents.
- Working-memory portability (currently `experimental/`, awaiting cross-framework evidence).

## 5. What evidence from the Mem0 adapter supports the claim

Running the eight R8 scenarios against unmodified Mem0 OSS 2.0.12 produced four **gaps** (scope immutability, expected-version conflict, idempotency-key, derived-vector refresh), one **native** pass (identity + history), and three **emulated** requirements (delete/tombstone, provenance, unknown-field preservation). The full evidence is in `reports/mem0_scenario_results.jsonl` and `reports/real-framework-validation-report.md`.

The four gaps are exactly the class of failure a memory-only spec can address without pulling in orchestration, identity, or transport. They align with the PAMSPEC normative Lite core in ADR-0029 §2.2 and §3.1. The native pass and the emulated cases confirm the boundary is drawn honestly: PAMSPEC does not restate what production frameworks already provide.

If a PAMSPEC-conformant memory service exposed those four properties to Mem0 users via a Mem0-side adapter, four documented failure classes would become impossible without changing Mem0's core. That is a distinct contribution.
