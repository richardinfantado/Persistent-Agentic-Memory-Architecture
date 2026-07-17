# What PAMSPEC is for

*Written after the R8 Mem0 evidence. Revised under the V08.1 corrective pass. Word count: below 500.*

## 1. What PAMSPEC standardizes

PAMSPEC standardizes **how persistent agent memory remains trustworthy while it evolves across runtimes.** Its subject is the correctness of the authoritative memory record across create, update, retrieve, delete, and history operations — not storage layout, not transport, not embedding quality, not extraction quality.

The normative Lite core requires: stable object identity, immutable version identity with monotonic ordering, immutable scope, minimal provenance, expected-version conflict rejection, idempotent create, deterministic deletion with tombstone semantics, and a defined boundary between authoritative state and derived artifacts.

## 2. Why a versioned document store is insufficient

A versioned document store preserves records. It does not, on its own, define:

- whether scope stays fixed when metadata is edited,
- whether concurrent updates must yield to expected-version checks,
- whether identical creates are idempotent,
- whether deletion prevents stale-reference resurrection,
- whether the authoritative/derived boundary is contractual.

Against Mem0 OSS 2.0.12 (V08.1), R8 measured: `update(memory_id, metadata={"user_id":"bob"})` silently mutates native scope and moves the memory across tenants (verified via `get_all` visibility before and after); no expected-version parameter exists; no idempotency-key parameter exists.

## 3. Which behavior is uniquely memory-specific

One cluster is demonstrated by this sprint:

- **Stable identity + strict update contract.** Immutable scope, distinct version identity, expected-version conflict rejection, idempotency-key semantics. These are correctness properties on the *authoritative* update path that generic CRUD does not require.

**Authoritative-vs-derived integrity** remains architecturally interesting, but Mem0 refreshes the derived vector on `update` (V08.1 experiment, direct embedding fetch, L2 delta ≈ 1.374). This sprint therefore does not cite derived-artifact staleness as a PAMSPEC-demonstrated distinct contribution. That case would need a framework where an authoritative update demonstrably leaves derived artefacts stale.

## 4. What PAMSPEC explicitly does not standardize

- Storage engines, vector-store choice, embedding model choice.
- Transport, wire framing, or connection protocol.
- Identity, authorization, delegation, sharing, cryptographic erasure.
- Billing, cost accounting, latency, telemetry.
- Cognitive memory taxonomy as normative wire types.
- Runtime coordination between agents.
- Working-memory portability (currently `experimental/`).

## 5. Evidence from the Mem0 adapter

Running the eight R8 scenarios against unmodified Mem0 OSS 2.0.12 produced (V08.1): three **gaps** (scope immutability, expected-version conflict, idempotency-key), two **native** (identity + history — *partial* for version identity; derived-vector refresh), three **emulated** (delete/tombstone — with one *not-testable* sub-requirement — provenance, unknown-field). Full evidence: `reports/mem0_scenario_results.jsonl`, `reports/real-framework-validation-report.md`, `environment-manifest.json`.

The three gaps are exactly the class of failure a memory-only spec can address without pulling in orchestration, identity, or transport. The native pass on derived-vector refresh and the emulated cases confirm the boundary is honest: PAMSPEC does not restate what production frameworks already provide.

If a PAMSPEC-conformant memory service exposed those three properties to Mem0 users via a Mem0-side adapter, three documented failure classes — one currently open as Mem0 Python issue #6277 — would become impossible without changing Mem0's core. That is a distinct contribution.
