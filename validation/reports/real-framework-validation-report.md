# PAMSPEC × Mem0 real-framework validation report

**Revision:** V08.1 (corrective pass — supersedes V08 in every material claim).
**Framework under test:** Mem0 OSS 2.0.12 (`mem0ai==2.0.12`).
**Backends:** local SentenceTransformer embedder (`sentence-transformers/all-MiniLM-L6-v2`), local Chroma vector store, dummy LLM (never called; every `add()` uses `infer=False`).
**Mem0 source:** unmodified.
**Test date:** 2026-07-18.
**Machine-readable evidence:** `mem0_scenario_results.jsonl` (this directory).
**Environment manifest:** `../environment-manifest.json` (Python, OS, package versions, model reference, file hashes).
**Pinned dependency lock:** `../requirements-lock.txt` (exact resolved versions of the whole transitive tree at test time).

Each of the eight scenarios required by R8 was probed through Mem0's **public Python API** with no monkey-patching of Mem0 internals. Classification per scenario (or sub-requirement) is one of `native`, `emulated`, `gap`, `questionable`, `not-testable`. **All eight scenarios executed successfully; a high pass count was never the objective** — the objective was discovering which PAMSPEC semantics are real and portable.

## Correction notice — reversal of the V08 headline finding

V08 (the prior revision of this report) stated that Mem0 exhibits stale derived-vector state after `update(text=...)` and framed this as the sprint's strongest single result. **That claim was not properly established.** The V08 scenario had only a single memory in the collection, so a nearest-neighbor `search(top_k=5)` returning that memory for both old and new queries did not distinguish "old vector retained" from "new vector correctly written but still nearest among one candidate."

V08.1 redesigned scenario 7 with (a) five distinctive control memories, (b) maximally unrelated old and new target phrases, (c) rank AND score capture before/after update for both queries, and (d) a direct fetch of the target's stored embedding through the underlying Chroma collection before and after the update.

**Under the corrected experiment, Mem0 refreshes the stored embedding on `update(text=...)`.**
Observed on 2026-07-18: embedding bytes changed; L2 delta ≈ 1.374 (unit-norm embedding space); old-query rank moved from 0 to 6; new-query rank moved from absent-from-top-10 to 1 with score 1.0. Scenario 7 is therefore classified **native**, not `gap`, and the V08 headline claim is retracted.

The architectural argument that PAMSPEC's authoritative-vs-derived distinction has value remains intact conceptually, but it is **no longer supported by this Mem0 evidence** and this report will not cite Mem0 as its proof. See the `## What we now think differently` section for the revised strongest finding.

## Result summary

| # | Requirement | Result | Adapter notes |
|---|---|---|---|
| 1 | Scope immutability across update | **GAP** | `update(memory_id, metadata={"user_id": "bob"})` silently mutates the native `user_id` field from `alice` to `bob` AND causes cross-tenant movement verified via `get_all(filters={"user_id": ...})`: Alice loses visibility of the memory, Bob gains it. Reproduces the failure class documented in Mem0 Python issue **#6277** (TypeScript twin: **#6342**). |
| 2 | Stable identity + history ledger (**partial** version identity) | **NATIVE (partial)** | Stable `memory_id`; each `history` entry has its own id; monotonic timestamps; prior content preserved verbatim as `old_memory`. **PARTIAL** for PAMSPEC's `version_id` model: history-entry ids are not documented as immutable version identifiers and no operation consumes them as `expected_version_id`. Sub-requirement decomposition is recorded in `mem0_scenario_results.jsonl` under scenario 2. |
| 3 | Expected-version conflict rejection | **GAP** | `Memory.update` has no `expected_version_id` parameter. Concurrent or stale updates are silently accepted; last-write-wins. |
| 4 | Idempotency-key semantics | **GAP** | `Memory.add` has no `idempotency_key` parameter. Repeated identical `add` returns a NEW memory id each call. |
| 5 | Delete / tombstone / stale-reference (split into sub-requirements) | **EMULATED (mixed)** | Split into five sub-requirements: (a) delete recorded in history — **native**; (b) `get` after delete returns no active object — **native**; (c) `update` using deleted id is rejected — **native** (`ValueError: Memory with id ... not found`); (d) same-id recreation prohibited — **not-testable** (Mem0 auto-assigns UUIDs; public API exposes no way to request a specific id, so a differing recreated id cannot distinguish "identity reserved" from "random UUID happened to differ"); (e) standards-grade persistent tombstone as a first-class object — **emulated** (an adapter would layer this on top of the `DELETE` history event). |
| 6 | Provenance preservation | **EMULATED** | Scope tuple (`user_id`, `agent_id`, `run_id`) is native and preserved across `update`. `created_at`/`updated_at` timestamps are native. `metadata` is opaque, so PAMSPEC-shaped provenance fields survive as long as an adapter stores them under metadata. Mem0 records only coarse `event: ADD/UPDATE/DELETE` in `history`; activity kind must be layered on. |
| 7 | Derived state (vector index) refreshed on authoritative update | **NATIVE** *(corrected — see reversal notice above)* | Direct Chroma collection fetch before and after `update(text=new_content)` showed stored-embedding bytes changed with L2 delta ≈ 1.374 across five-control experiment. Rank/score signals corroborate: old-query rank 0→6, new-query rank absent→1 (score 1.0). Mem0 does refresh the derived vector on update. |
| 8 | Unknown extension fields survive round-trip | **EMULATED** | Scalar unknown metadata keys pass through cleanly across add → get → update → get. Nested-dict values are rejected at `add` time by Chroma (`ValueError: Expected metadata value to be a str, int, float, bool, SparseVector, list, or None`). An adapter must JSON-encode nested shapes. |

## Bucket rollup (V08.1)

Scenario-level aggregate (top-line classification per scenario):

- **Native (2):** identity + history ledger (partial version identity), derived-vector refresh.
- **Emulated (3):** delete/tombstone (mixed sub-classification), provenance, unknown-field preservation.
- **Gap (3):** scope immutability, expected-version conflict, idempotency-key.
- **Questionable (0).**
- **Not testable (0 at the scenario level; 1 sub-requirement inside scenario 5).**

Comparison to V08 rollup (native 1 / emulated 3 / gap 4 / not-testable 0): scenario 7 moved gap→native under corrected experimental design; scenario 5 gained a not-testable sub-requirement; scenario 2 gained explicit "partial" framing.

## What we now think differently

### Revised strongest finding

The strongest single finding of the sprint is now **scope immutability (scenario 1)**, not derived-vector refresh. The scope-mutation result is doubly established: (a) `update(metadata={"user_id": "bob"})` mutates the native `user_id` from `alice` to `bob`, and (b) an independent `get_all(filters={"user_id": ...})` visibility probe before and after confirms cross-tenant movement — the memory disappears from Alice's tenant view and appears in Bob's. This directly reproduces the failure class currently open as Mem0 Python issue **#6277** and its TypeScript twin **#6342**.

A PAMSPEC contract that makes scope immutability normative and testable would prevent a concrete, currently-open bug in a production-oriented framework — not a hypothetical one.

### Remaining real PAMSPEC value-add

**Expected-version conflict rejection** and **idempotency-key semantics** remain gaps. Neither is present in Mem0's public API; both correspond to well-known operational failure classes (last-write-wins clobbering, retry storms creating duplicates).

**Delete/tombstone** and **provenance** and **unknown-field preservation** are close enough to native that a well-designed adapter closes the gap, but the adapter work is non-trivial (per-object tombstone lifecycle, provenance-key convention, JSON-encoding for nested extensions).

### Not distinct value-add

**Derived-vector refresh** is native in Mem0 as tested. PAMSPEC's authoritative-vs-derived distinction remains **an architectural idea**, but it is not evidenced by this framework probe. If PAMSPEC wants to make an empirical case for that distinction, it will need to find a framework or storage path where a mainline `update` operation demonstrably leaves derived artefacts stale — that framework was not Mem0 2.0.12 with the Chroma vector store.

**Identity + history** is native; PAMSPEC restating the *object identity + ledger* dimensions of it would only add profile ceremony. PAMSPEC's `version_id` model still has independent value where operations consume it as `expected_version_id` (scenario 3), but that value pertains to concurrency control, not to plain history.

### Working Memory

Working Memory in Mem0 is not distinguishable from long-term memory at the API level. See `working-memory-evidence.md` for the cross-framework observation and the recommendation to keep PAMSPEC Working Memory `experimental/`.

## Cross-check against public issues

See `issue-mapping.md`. V08.1 correction: the primary Python-side Mem0 issue for scope mutation is **#6277** (open); **#6342** is the TypeScript twin. V08 referenced #6342 as the primary — corrected here.

## Comparison to AMP

See `amp-comparison-note.md`. V08.1 correction: PAMSPEC's distinct contribution, on the evidence in this sprint, is **stable identity + strict update contract** (scope immutability, expected-version, idempotency) — not authoritative-vs-derived integrity, which Mem0 already handles natively for the vector case tested. Whether other derived-artifact classes (summaries, graph state) exhibit the staleness pattern remains an open empirical question.

## Reproducing this report

```bash
python -m pip install -r validation/requirements.txt
# Optional exact reproduction:
python -m pip install -r validation/requirements-lock.txt
PYTHONPATH=. python -m pytest validation/tests -q
cat validation/reports/mem0_scenario_results.jsonl
cat validation/environment-manifest.json
```

Runtime: ~130 seconds on a laptop (dominated by SentenceTransformer inference across scenario 7's control set + Chroma persistence). First run downloads the ~90 MB embedding model into the HuggingFace cache.

## What was NOT done

- Mem0 source was not modified.
- No PAMSPEC feature was added to make results look stronger.
- No claim was retained after evidence contradicted it (see the reversal notice).
- No new schemas.
- No new ADRs.
- The Internet-Draft source was not rewritten.
- No message was sent to any framework maintainer (those drafts are in `../outreach-drafts/`).
