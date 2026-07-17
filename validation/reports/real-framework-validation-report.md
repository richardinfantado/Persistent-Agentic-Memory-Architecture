# PAMSPEC × Mem0 real-framework validation report

**Framework under test:** Mem0 OSS 2.0.12 (`mem0ai==2.0.12`).
**Backends:** local SentenceTransformer embedder (`all-MiniLM-L6-v2`), local Chroma vector store, dummy LLM (never called; every `add()` uses `infer=False`).
**Mem0 source:** unmodified.
**Test date:** 2026-07-18.
**Machine-readable evidence:** `mem0_scenario_results.jsonl` (this directory).

The scenarios below are exactly the eight the R8 spec required. Each was probed through Mem0's **public Python API** with no monkey-patching of Mem0 internals. Classification per scenario is one of `native`, `emulated`, `gap`, `questionable`, `not-testable`. **A high pass count was not the objective**; the objective was discovering which PAMSPEC semantics are real and portable.

## Result summary

| # | Requirement | Result | Adapter notes |
|---|---|---|---|
| 1 | Scope immutability across update | **GAP** | Mem0 `update(memory_id, metadata={"user_id": "bob"})` silently mutates the native `user_id` field from `alice` to `bob`. Reproduces the failure mode documented in Mem0 issue #6342 category (scope mutation). |
| 2 | Stable identity + distinct version identity + history | **NATIVE** | Stable `memory_id`; each `history` entry has its own id; monotonic timestamps; prior content preserved verbatim as `old_memory`. Update actor is not exposed (`actor_id: None` in this test path). |
| 3 | Expected-version conflict rejection | **GAP** | `Memory.update` has no `expected_version_id` parameter. Concurrent or stale updates are silently accepted; last-write-wins. |
| 4 | Idempotency-key semantics | **GAP** | `Memory.add` has no `idempotency_key` parameter (signature: `messages, user_id, agent_id, run_id, metadata, timestamp, expiration_date, infer, memory_type, prompt`). Repeated identical `add` returns a NEW memory id each call. |
| 5 | Persistent tombstone + identity reserved + stale-reference rejection | **EMULATED** | Delete records a `DELETE` event in `history` (tombstone-like). `get` after delete returns `None`. Stale `update` on a deleted id fails with `ValueError: Memory with id ... not found. Please provide a valid 'memory_id'`. Identity is not reserved against recreation because there is no public way to specify a recreation id (Mem0 assigns UUIDs). |
| 6 | Provenance preservation | **EMULATED** | Scope tuple (`user_id`, `agent_id`, `run_id`) is native and preserved across `update`. `created_at`/`updated_at` timestamps are native. `metadata` is opaque, so PAMSPEC-shaped provenance fields (`source_actor`, `activity`, `original_source`, `model_ref`) survive as long as they are stored under metadata by the caller. Mem0 does not itself record activity kind beyond the coarse `event: ADD/UPDATE/DELETE` in `history`. |
| 7 | Derived state (vector index) refreshed on authoritative update | **GAP** | **Most important finding of this sprint.** When `update(memory_id, text="dogs")` is called on a memory that originally contained `"cats"`, `search("cats")` **still returns the updated memory** — and `search("dogs")` also returns it. The vector index is not refreshed by `update`; both the old vector and the new content are simultaneously findable. This is exactly the stale-derived-artifact class of failure PAMSPEC's authoritative-vs-derived model is well-positioned to address. |
| 8 | Unknown extension fields survive round-trip | **EMULATED** | Scalar unknown metadata keys (`"x-experimental-ext": "some-value"`) pass through cleanly across add → get → update → get. Nested-dict values (`"x-experimental-ext": {"nested": [1, 2, 3]}`) are rejected at `add` time by Chroma with `ValueError: Expected metadata value to be a str, int, float, bool, SparseVector, list, or None`. An adapter would have to JSON-encode nested shapes to preserve them. |

## Bucket rollup

- **Native (1):** identity + history.
- **Emulated (3):** delete/tombstone (mostly there), provenance (via metadata convention), unknown-field preservation (scalar OK, nested needs adapter serialization).
- **Gap (4):** scope immutability, expected-version conflict, idempotency-key, derived-vector refresh.
- **Questionable (0).**
- **Not testable (0).**

## What survived, what didn't, what changed our view

### What is real PAMSPEC value-add

**Scope immutability**, **expected-version conflict**, **idempotency-key**, and **derived-state refresh on authoritative update** are all **real gaps** in a production-oriented framework. A PAMSPEC contract that makes these normative and testable would prevent concrete, documented failures — not hypothetical ones.

The derived-state finding (scenario 7) is the strongest single result. Mem0 lets the vector index diverge from authoritative content silently. Any agent relying on retrieval to reflect current memory will act on stale beliefs. This is precisely the STALE / MemoRepair class of failure the R8 spec cited, and it is reproducible on the very first `update` after any `add`.

### What is not distinct value-add

**Identity + history** is already native. PAMSPEC restating it would only add profile ceremony.

**Delete/tombstone**, **provenance**, and **unknown-field preservation** are close enough to native that a well-designed adapter closes the gap. PAMSPEC's contribution here is not the presence of these concepts but the specific *shape* — and Mem0's `event: DELETE`, `event: ADD`, `event: UPDATE` in history is very close to PAMSPEC's Event Ledger event vocabulary.

### What we now think differently

- **Working Memory in Mem0 is not distinguishable from long-term memory** at the API level. Mem0 has one storage tier; the working/long-term split is a runtime construct in frameworks like LangGraph and Letta. Confirms the ADR-0029 decision to treat Working Memory as `experimental/` rather than a normative type.

- **Mem0's scope model IS user/agent/run tuples**, not opaque scope ids. A PAMSPEC binding for Mem0 that treats scope as an opaque string loses information; the reverse translation (unpacking `"user:alice/agent:a1/run:r1"` into the tuple) is trivial. This is a design point for R5, not a blocker for R8.

- **The `resource_usage` block removed in R4a was a good removal.** Mem0 does not carry any per-event resource-accounting concept in its ledger, confirming that telemetry belongs outside the memory contract.

### Cross-check against public issues

See `issue-mapping.md` in this directory for the mapping from real public issues (Mem0 scope mutation, Letta migration data loss, LangGraph checkpointer state loss) to the requirements we validated.

### Comparison to AMP

See `amp-comparison-note.md` in this directory. Summary: PAMSPEC's distinct contribution — under this evidence — is on **authoritative-vs-derived integrity semantics** and **stable identity + strict update contract** — not on the wire-format, operations, or adapter-plumbing dimensions AMP already covers.

## Reproducing this report

```bash
python -m pip install -r validation/requirements.txt
PYTHONPATH=. python -m pytest validation/tests -q
cat validation/reports/mem0_scenario_results.jsonl
```

Total runtime: ~70 seconds on a laptop. First run downloads a ~90 MB SentenceTransformer model into the HuggingFace cache.

## What was NOT done

- Mem0 source was not modified.
- No PAMSPEC feature was added to make results look stronger.
- No new schemas.
- No new ADRs.
- The Internet-Draft source was not rewritten.
- No message was sent to any framework maintainer (those drafts are in `../outreach-drafts/`).
