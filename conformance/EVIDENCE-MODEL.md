# PAMSPEC Evidence and Conformance Model (R6.1a)

> **Status:** R6.1a — corrective pass on R6.1. This document defines the machine-readable evidence discipline the R7 conformance harness and R8 framework-validation sprints must follow. It does NOT modify the PAMSPEC Internet-Draft (`draft-infantado-agent-memory-architecture-latest`).
>
> **Follow-on work:** R6.2 wires the R7 conformance harness to emit `EvidenceRecord` values alongside the legacy pass/fail report; R6.3 migrates V08.x results to this format as a supplementary file (the immutable evidence at commit `6ae806b` is not rewritten); R6.4 wires evidence-schema validation into the repository validator.

## Why this exists

Between V08 and V08.1, one PAMSPEC sprint published a headline framework gap that a properly controlled experiment showed to be an artifact of under-designed methodology. The retraction was handled in prose reports. For PAMSPEC to publish evidence whose discipline is auditable — not just its schemas — the retraction pathway must be first-class in the machine-readable evidence, and records must be genuinely append-only.

R6.1a designs the model so it satisfies both. The schema is `conformance/schemas/0.1-draft/evidence-record.schema.json`. The canonical retraction example is `validation/reports/evidence-chain-v08-derived-vector.jsonl`.

## Design constraint: append-only, immutable records

Every evidence record is written once and never modified. If a later record shows the earlier claim to be wrong, the correction is expressed as a **revision relationship** on the later record, not by rewriting the earlier one.

- **Intrinsic** `claim_status` on a record reflects the author's assessment at the moment the record was written. The intrinsic states are exactly three:
  - `confirmed` — the record's classification is supported by the evidence, as the author judged it at the time
  - `inconclusive` — the experiment ran but cannot distinguish among alternative explanations
  - `not_testable` — the claim cannot be evaluated with the subject's current public API without modifying the subject
- **Effective** disposition of an older claim is derived by walking forward in the chain and looking for a later record whose `revises.record_id` points at the older record. If such a record exists with `revises.effect` in `{retracts, supersedes}`, that later record determines the older claim's effective disposition. `reproduces` and `extends` do not change effective disposition.

The V08 record's intrinsic `claim_status` in the reference chain is `confirmed` — because V08 confirmed its (wrong) claim when it was written. The V08.1 record carries `revises.effect = retracts` pointing at V08. The V08 record itself is preserved unchanged.

## The four test_kinds

| test_kind | Question it answers | Typical use |
|---|---|---|
| `probe` | What does this subject currently do? | First look at Mem0, Letta, LangGraph, or any framework whose behavior is not yet characterized. |
| `conformance` | Does this subject satisfy a normative PAMSPEC requirement? | Reference-python, TypeScript reference, adapters bound to a Profile. |
| `regression` | Did previously observed behavior change? | Re-run of a prior probe or conformance record against a new subject version. |
| `controlled_experiment` | Is the observed signal distinguishable from an experimental artifact? | Follow-up to any probe or conformance record whose conclusion is doubted. MUST have a non-null `control_design` with at least one `confounders_ruled_out` or `negative_controls` entry. |

## The three intrinsic claim_status values

| claim_status | Meaning |
|---|---|
| `confirmed` | The classification is supported by the evidence, as the author assessed at authoring time. |
| `inconclusive` | The experiment ran but cannot distinguish among alternative explanations. Publish honestly — do not upgrade to `confirmed` on convenience. |
| `not_testable` | Cannot be evaluated with the current framework surface without source modification. |

`retracted` and `superseded` are **not** intrinsic statuses. They are relationships carried by later records.

## The four revision effects

| revises.effect | Alters effective disposition? | Meaning |
|---|---|---|
| `retracts` | Yes | Later evidence shows the earlier record's claim is wrong. Requires a non-empty `reason`. |
| `supersedes` | Yes | Replaces the earlier record without contradiction (e.g. re-run with better methodology reaching the same conclusion, or a newer version producing the same result). |
| `reproduces` | No | An independent run reproduced the earlier result. Increases confidence; effective disposition unchanged. |
| `extends` | No | Adds evidence to the earlier record. Effective disposition unchanged. |

Multiple later records may reference the same earlier record. Only records with `effect` in `{retracts, supersedes}` alter effective disposition. Conflicting later effects are rejected by the validator (a record cannot both retract-and-supersede the same target).

## Subject and adapter identity

Every record identifies its `subject` with three required fields — `kind`, `name`, `version` — using one of the five subject kinds: `framework`, `implementation`, `adapter`, `binding`, `specification`. This aligns with R7's `ConformanceReport` which already tracks adapter name/version and implementation name/version.

Records may additionally carry an optional `adapter` object naming the PAMSPEC adapter through which the subject was observed. This is null when the subject was examined through its own public API without a PAMSPEC adapter in the loop.

## PAMSPEC context

Every record MUST pin its evaluation to a specific `pamspec_context.spec_commit` (full 40-character git SHA). A requirement's identifier can be stable while the underlying text is edited; the `spec_commit` prevents that drift from silently invalidating a claim. `harness_commit` (full SHA, nullable) records which R7 conformance harness produced the record.

## Classification semantics

- `native` — subject provides the requirement directly.
- `emulated` — the **tested adapter** demonstrably supplied the behavior although the underlying framework did not provide it natively. Never used to describe hypothetical compensation — use `adapter_feasibility` instead when the adapter is not yet built.
- `gap` — the requirement is not met and no adapter is in scope. If PAMSPEC-adapter compensation is theoretically feasible, record that separately in `adapter_feasibility` (`feasible | infeasible | unknown | not_applicable`).
- `questionable` — evidence suggests the requirement itself may be artificial.
- `not_testable` — cannot be probed with the current public API without modifying the subject. Combined with `claim_status = not_testable` (schema-enforced).

## Enforced invariants

Both the JSON schema and `scripts/validate_evidence.py` enforce the following. The schema conditionals cover the local property-relationship checks; the Python validator handles chain-level invariants that JSON Schema cannot express.

Schema-level (JSON Schema `if/then`):

1. `classification=not_testable` → `claim_status=not_testable`.
2. `test_kind=controlled_experiment` → non-null `control_design`.
3. `classification=not_testable` → `limitations` non-empty.
4. `evidence_source` contains `source_review` → `limitations` non-empty.

Chain-level (validator):

5. `record_id` unique within a chain file.
6. `controlled_experiment` control_design MUST have at least one entry in `confounders_ruled_out` or `negative_controls`.
7. `revises.record_id` MUST resolve to a record earlier in the same chain file (append-only ordering).
8. A record MUST NOT revise itself.
9. Revision cycles are prohibited (defensive; the earlier-only rule already prevents them, but tested explicitly).
10. `revises.record_id` target's `requirement_id` MUST equal the reviser's `requirement_id`.
11. `recorded_at` MUST NOT move backward along a revision edge (revisers are later than the revised).
12. A record may not carry a revision relationship that combines conflicting effects — a single record has one `revises` block with one `effect`. Two later records that both retract-and-supersede the same target with different effective outcomes ARE rejected.

## Relationship to the R7 conformance harness

R7's `ConformanceReport` already emits per-case pass/fail with adapter and implementation identity, protocol version, spec commit, and supported profiles. R6.2 will extend the harness so a suite case can additionally emit an `EvidenceRecord` conforming to this schema, using the same identity information R7 already carries. R7's existing pass/fail semantics are unchanged; R6 adds evidence-lifecycle metadata alongside them.

## Relationship to the PAMSPEC Internet-Draft

**None.** The evidence model is companion metadata for how PAMSPEC's own claims are audited over time. It is intentionally out of scope for the draft. When R5+R6 evidence exists to justify an R8 core/profiles split, a focused normative change proposal will be prepared then — not now.

## Do not

- Do not delete or modify a record after it is written. If it is wrong, revise it in a new appended record.
- Do not edit an evidence file that a permalink references from outside the repo (`evidence_commit=6ae806b`). Add a new supplementary chain file in a new commit.
- Do not label a probe `confirmed` when the design cannot rule out alternative explanations. Use `inconclusive` and disclose the gap in `limitations`.
- Do not classify hypothetical adapter compensation as observed `emulated` behavior. Use `gap` + `adapter_feasibility`.
- Do not carry a claim across framework-version bumps without a `regression` record.
