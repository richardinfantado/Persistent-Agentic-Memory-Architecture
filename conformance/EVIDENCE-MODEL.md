# PAMSPEC Evidence and Conformance Model (R6.1b)

> **Status:** R6.1b — third corrective pass on R6.1. Defines the machine-readable evidence discipline the R7 conformance harness and R8 framework-validation sprints must follow. Does NOT modify the PAMSPEC Internet-Draft (`draft-infantado-agent-memory-architecture-latest`).
>
> **Follow-on work:** R6.2 wires the R7 conformance harness to emit `EvidenceRecord` values alongside the legacy pass/fail report; R6.3 migrates V08.x results to this format as a supplementary supplementary chain (immutable evidence at commit `6ae806b` is not rewritten); R6.4 wires evidence-schema validation into the repository validator AND adds a byte-for-byte prefix check that ensures existing lines of an evidence-chain file are never modified once committed.

## Why this exists

Between V08 and V08.1, one PAMSPEC sprint published a headline framework gap that a properly controlled experiment showed to be an artifact of under-designed methodology. The retraction was handled in prose reports. For PAMSPEC to publish evidence whose discipline is auditable — not just its schemas — the retraction pathway must be first-class in the machine-readable evidence, and records must be genuinely append-only.

R6 designs the model so it satisfies both. The schema is `conformance/schemas/0.1-draft/evidence-record.schema.json`. The canonical retraction example is `validation/reports/evidence-chain-v08-derived-vector.jsonl`.

## Design constraint: append-only, immutable records

Every evidence record is written once and never modified. If a later record shows the earlier claim to be wrong, the correction is expressed as a **revision relationship** on the later record, not by rewriting the earlier one.

Intrinsic `claim_status` values (as-written by the author at authoring time):

- `confirmed` — the record's classification is supported by the evidence as the author judged at the time.
- `inconclusive` — the experiment ran but cannot distinguish among alternative explanations. An `inconclusive` record MUST NOT retract or supersede another (schema-enforced).
- `not_testable` — the claim cannot be evaluated with the subject's current public API without modifying the subject.

Effective disposition of an older claim is derived by walking forward in the chain and looking for a later record whose `revises.record_id` points at the older record. If such a record exists with `revises.effect ∈ {retracts, supersedes}` AND the reviser's `claim_status = confirmed`, that later record determines the older claim's effective disposition. `reproduces` and `extends` do not change effective disposition.

## Record provenance: `origin`, `recorded_at`, `evidence_observed_at`

Every record MUST identify how and when it came into being.

- `origin` — enum: `native_emission | retrospective_reconstruction`.
  - `native_emission` means the record was produced directly by a harness or scenario at the moment the claim was observed.
  - `retrospective_reconstruction` means the record was materialized after the fact from prior evidence (commit history, prior JSONL, prose reports). All records in the V08 reference chain are `retrospective_reconstruction` — the R6 EvidenceRecord format did not exist when V08 or V08.1 were originally observed.
- `recorded_at` — strict RFC 3339 date-time when the R6 record itself was materialized. For `native_emission`, roughly the moment the harness ran. For `retrospective_reconstruction`, later than the observation and may be identical across all reconstructed records materialized in one pass. **Enforced (invariant 13):** for `retrospective_reconstruction` records, `evidence_observed_at ≤ recorded_at`.
- `evidence_observed_at` — strict RFC 3339 date-time when the underlying claim was observed. For `native_emission`, equals `recorded_at`. For `retrospective_reconstruction`, the original observation time (usually the git commit time of the original evidence). Revision-edge monotonicity (invariant 11) is enforced on `evidence_observed_at`, NOT `recorded_at`, because the observation order is what matters — a retrospective reconstruction can materialize records in any order.

**Date-time format.** R6 uses **strict RFC 3339**. The `T` separator is required (a space is rejected); a timezone offset (`Z` or `+HH:MM` / `-HH:MM`) is required (naive timestamps are rejected). Calendar values must be valid (`2026-13-45T00:00:00Z` is rejected). Enforced by the validator's custom `date-time` format checker.

**Retrospective records may NOT carry a harness_commit** — see the schema conditional `origin=retrospective_reconstruction ⇒ harness_commit=null`. Native emissions may still legitimately carry a null `harness_commit` (produced by a non-R7 validation scenario or a hand-authored probe), so the reverse implication is not enforced.

## The four `test_kind`s

| test_kind | Question it answers |
|---|---|
| `probe` | What does this subject currently do? |
| `conformance` | Does this subject satisfy a normative PAMSPEC requirement? |
| `regression` | Did previously observed behavior change? |
| `controlled_experiment` | Is the observed signal distinguishable from an experimental artifact? Requires `control_design`, `environment_manifest`, and `results_artifact` non-null (schema-enforced). |

## The four revision `effect`s

| revises.effect | Alters effective disposition? |
|---|---|
| `retracts` | Yes — later evidence shows the earlier record's claim is wrong. |
| `supersedes` | Yes — replaces the earlier record without contradiction. |
| `reproduces` | No — an independent run reproduced the earlier result. |
| `extends` | No — adds evidence to the earlier record. |

Multiple later records may reference the same earlier record. Multiple altering revisions with the **same effect** on the same target are allowed (independent reproductions of a retraction, or independent supersessions with the same outcome). Conflicting altering effects (one `retracts` and one `supersedes` on the same target) are rejected by the validator.

An `inconclusive` reviser MUST NOT carry an altering revision (`retracts`/`supersedes`). That is enforced by the schema conditional `revises.effect ∈ {retracts, supersedes} ⇒ claim_status = confirmed`.

## Subject and adapter identity

Every record identifies its `subject` with `{kind, name, version}`. `kind` ∈ `{framework, implementation, adapter, binding, specification}`. All three fields are required and non-null.

The optional `adapter` block names the PAMSPEC adapter through which the subject was observed. Null when the subject was examined through its own public API without a PAMSPEC adapter in the loop.

## PAMSPEC context

`pamspec_context.spec_commit` (full 40-char SHA, non-null) pins the record to the PAMSPEC specification state it was evaluated against. `harness_commit` (full SHA, nullable) records the R7 harness that produced the record — **null when the record was not produced by an R7 harness run** (validation scenarios, hand-authored probes, retrospective reconstructions). `profile` and `profile_version` are paired: either both non-null (formal profile conformance) or both null (architectural probe).

## Classification semantics

- `native` — subject provides the requirement directly.
- `emulated` — the tested adapter demonstrably supplied the behavior although the underlying framework did not provide it natively. Schema-enforced preconditions: `adapter` non-null AND `evidence_source` contains `"adapter"`. Hypothetical compensation is NOT emulated — use `adapter_feasibility` on a `gap` record instead.
- `gap` — requirement not met, no adapter in scope. May carry `adapter_feasibility`.
- `questionable` — evidence suggests the requirement itself may be artificial.
- `not_testable` — cannot be probed with the current public API without modifying the subject. **Bidirectional with `claim_status`**: `classification=not_testable ⇔ claim_status=not_testable` (both directions schema-enforced).

## Results artifact

`results_artifact` is a `{reference, sha256}` pair identifying the raw machine-readable evidence file this record summarizes. A hash alone does not identify what was hashed; the reference-and-hash pair does. Nullable when the record IS the raw evidence or when no separate artifact exists. `controlled_experiment` records MUST have both `environment_manifest` and `results_artifact` non-null (schema-enforced). When `environment_manifest` is non-null, its `sha256` MUST also be non-null (schema-enforced).

## Enforced invariants

Schema-level (JSON Schema `if/then` conditionals):

1. `classification=not_testable ⇔ claim_status=not_testable` (both directions).
2. `test_kind=controlled_experiment ⇒ control_design non-null`.
3. `test_kind=controlled_experiment ⇒ environment_manifest non-null AND results_artifact non-null`.
4. `environment_manifest non-null ⇒ sha256 non-null`.
5. `classification=not_testable ⇒ limitations non-empty`.
6. `evidence_source contains "source_review" ⇒ limitations non-empty`.
7. `classification=emulated ⇒ adapter non-null AND evidence_source contains "adapter"`.
8. `evidence_source contains "adapter" ⇒ adapter non-null`.
9. `revises.effect ∈ {retracts, supersedes} ⇒ claim_status = confirmed`.
10. `profile null ⇔ profile_version null` (both directions).
11. `origin = retrospective_reconstruction ⇒ pamspec_context.harness_commit = null` (retrospective records may not falsely attribute evidence to the R7 harness).

Chain-level (`scripts/validate_evidence.py`, invariants numbered from the earlier revisions):

5. `record_id` unique per file.
6. `controlled_experiment` control_design must have at least one entry in `confounders_ruled_out` or `negative_controls`.
7. `revises.record_id` must resolve to a record earlier in the same file (append-only ordering).
8. No self-revision.
9. No revision cycles.
10. `revises` target's `requirement_id` must equal the reviser's `requirement_id`.
11. `evidence_observed_at` must not move backward along a revision edge.
12. Multiple altering revisions with the **same** effect on a target are allowed; conflicting altering effects on the same target are prohibited.
13. For `origin = retrospective_reconstruction` records, `evidence_observed_at ≤ recorded_at` (the underlying experiment cannot occur after the record was materialized).

Additionally: the JSON Schema Draft 2020-12 validator is instantiated with a custom **strict RFC 3339** date-time format checker. Malformed timestamps, space-separated forms (`2026-07-18 15:00:00+08:00`), naive timestamps without a timezone offset, and invalid calendar values are all rejected at schema-check time.

## Storage rule

One append-only chain file per evidence subject or requirement family:

```
validation/evidence/
  mem0-vector-refresh.jsonl
  mem0-scope-immutability.jsonl
  reference-python-lite.jsonl
```

Or, during the 0.1-draft cycle, under `validation/reports/`:

```
validation/reports/
  evidence-chain-v08-derived-vector.jsonl
  evidence-chain-<subject>-<requirement>.jsonl
```

Rules:

1. Earlier lines in a chain file MUST NEVER be modified, removed, reordered, or replaced.
2. New records may only be **appended**.
3. External permalinks reference an immutable commit + path pair; the historical commit does not change when new records are later appended at the tip of the branch.
4. R6.4 will add a repository-validator check enforcing that a modified evidence-chain file has the version from `main` as an exact byte-for-byte prefix.

Do NOT create a separate "supplementary" file to work around invariant 7's earlier-only ordering — invariant 7 is a within-file rule, and the append-only storage rule already reconciles with external permalinks.

## Relationship to the R7 conformance harness

R7's `ConformanceReport` already emits per-case pass/fail with adapter and implementation identity, protocol version, spec commit, and supported profiles. R6.2 will extend the harness so a suite case can additionally emit an `EvidenceRecord` conforming to this schema, using the identity information R7 already carries and setting `origin=native_emission`. R7's pass/fail semantics are unchanged; R6 adds evidence-lifecycle metadata alongside them.

## Relationship to the PAMSPEC Internet-Draft

**None.** The evidence model is companion metadata for how PAMSPEC's own claims are audited over time. It is intentionally out of scope for the draft.

## Note on the schema `$id`

The schema `$id` currently contains the mutable `main` branch in its URL: `https://raw.githubusercontent.com/richardinfantado/Persistent-Agentic-Memory-Architecture/main/conformance/schemas/0.1-draft/evidence-record.schema.json`. This is acceptable during the 0.1-draft cycle because the versioned directory (`0.1-draft/`) will be frozen before external publication, and a release-tag URL or commit-pinned canonical URI will replace this identifier at that point. Do not treat the current URL as a stable long-term identifier.

## Do not

- Do not delete or modify a record after it is written. If it is wrong, append a revising record.
- Do not modify earlier lines of an already-committed evidence-chain file. Append only.
- Do not label a probe `confirmed` when the design cannot rule out alternative explanations. Use `inconclusive` and disclose the gap in `limitations`.
- Do not use `inconclusive` on a reviser with `effect ∈ {retracts, supersedes}` — an inconclusive experiment cannot authoritatively retract or supersede.
- Do not classify hypothetical adapter compensation as observed `emulated` behavior. Use `gap` + `adapter_feasibility`.
- Do not carry a claim across framework-version bumps without a `regression` record.
- Do not set `harness_commit` for a record that a harness did not produce (validation scenarios, hand-authored probes, retrospective reconstructions all leave it null).
