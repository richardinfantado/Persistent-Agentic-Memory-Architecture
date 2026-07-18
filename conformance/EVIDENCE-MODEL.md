# PAMSPEC Evidence and Conformance Model (R6.1)

> **Status:** R6.1 specification of the evidence model. This document does NOT modify the PAMSPEC Internet-Draft (`draft-infantado-agent-memory-architecture-latest`). It defines the machine-readable evidence discipline the conformance harness (R7) and framework validation sprints (R8/V08.x) must follow.
>
> **Follow-on work:** R6.2 wires the R7 `ConformanceReport` to emit `EvidenceRecord` values in addition to legacy pass/fail; R6.3 migrates V08.x results to the new format as a supplementary file; R6.4 wires schema validation into the repository validator.

## Why this exists

Between V08 and V08.1, one PAMSPEC sprint claimed a headline framework gap ("Mem0 does not refresh the derived vector on update") that a properly controlled experiment showed to be an artifact of under-designed methodology. The sprint retracted the claim in V08.1 and replaced it with a corrected result. That retraction was handled by human vigilance in prose reports. For PAMSPEC to be a public specification whose evidence discipline is auditable — not just its schemas — the retraction pathway must be a first-class feature of the machine-readable evidence, not an editorial afterthought in a report.

R6 makes four claim-lifecycle states and four test-purpose kinds mandatory metadata on every evidence record. It defines the schema at `conformance/schemas/evidence-record.schema.json`. It designates the V08→V08.1 chain as the reference retraction example at `validation/reports/evidence-chain-v08-derived-vector.jsonl`.

## The four test_kinds

Every evidence record MUST declare exactly one of:

| test_kind | Question it answers | Typical use |
|---|---|---|
| `probe` | What does this external framework currently do? | First look at Mem0, Letta, LangGraph, or any framework whose behavior is not yet characterized. |
| `conformance` | Does this implementation satisfy a normative PAMSPEC requirement? | Reference-python, TypeScript reference, adapters bound to a Profile. |
| `regression` | Did previously observed behavior change? | Re-running an old probe/conformance record against a new version of the framework or implementation. |
| `controlled_experiment` | Is the observed signal distinguishable from an experimental artifact? | Follow-up to any probe or conformance record whose conclusion is doubted. Design MUST populate `control_design.alternative_explanations_ruled_out`. |

These are not aliases for each other. A probe should never be published claiming a framework gap without a controlled_experiment record backing it, UNLESS the probe's `limitations` and `control_design` explicitly disclose the uncontrolled scope AND the claim_status is `inconclusive` or the classification is annotated accordingly.

## The five claim_status states

| claim_status | Meaning |
|---|---|
| `confirmed` | The classification is supported by the observed evidence and no known alternative explanation better fits it. |
| `inconclusive` | The experiment ran but cannot distinguish among alternative explanations. Publish honestly — do not upgrade to `confirmed` on convenience. |
| `retracted` | A later record has shown this record's claim to be wrong. Retracted records MUST remain in the evidence chain. A retracted record MUST have a superseding record with matching `requirement_id` and `supersedes_claim = <retracted record_id>`. |
| `superseded` | A later record replaced this one without contradicting it (usually re-run against a newer framework version, or with additional controls, that reproduced the earlier conclusion). |
| `not_testable` | The claim cannot be evaluated with the framework's current public API surface without source modification, which the sprint disallows. |

## Retraction protocol

1. A retracted record is NEVER deleted, edited, or amended silently.
2. When a claim is retracted, the record's `claim_status` is set to `retracted` and a **new** record is appended to the evidence chain with a distinct `record_id`, `supersedes_claim` pointing at the retracted record's id, and its own `claim_status` (usually `confirmed`, sometimes `inconclusive`).
3. Every retracted record MUST list, in `limitations`, the specific methodological weakness that caused the retraction. The next auditor should be able to see exactly what to avoid.
4. Every retraction MUST be surfaced in the human-readable report that references the evidence chain, not only in the machine-readable file.

The V08→V08.1 chain at `validation/reports/evidence-chain-v08-derived-vector.jsonl` is the canonical worked example. Two records: `v08.scenario7.probe` (retracted) and `v08.1.scenario7.controlled_experiment` (confirmed, supersedes the first). Both records point at their respective evidence commits (`8871689` and `6ae806b`). Both list their own limitations honestly.

## Required fields (see schema for full detail)

- `record_id`, `recorded_at`
- `test_kind`, `requirement_id`
- `framework`, `framework_version`
- `classification` (native / emulated / gap / questionable / not_testable)
- `sub_requirements` (optional, but present when the top-level requirement decomposes)
- `evidence_source` (public_api / backend_inspection / adapter / source_review; multiple allowed)
- `claim_status` (confirmed / inconclusive / retracted / superseded / not_testable)
- `supersedes_claim` (nullable)
- `control_design` (required for `controlled_experiment`, recommended for `probe` with controls)
- `environment_manifest` (reference + sha256)
- `results_hash` (sha256 of the raw JSONL of the underlying test emissions)
- `evidence_commit` (immutable git SHA)
- `limitations` (honest list of what the evidence does NOT establish)

Two optional fields carry human context alongside the machine record: `observed_evidence` (raw values captured) and `conclusion_narrative` (one plain-English paragraph).

## Relationship to the R7 conformance harness

R7's `ConformanceReport` already emits per-case pass/fail with adapter/implementation metadata (adapter name, adapter version, implementation name and version, protocol version, spec commit, supported profiles). R6.2 will extend the harness so a suite case can additionally emit an `EvidenceRecord` conforming to `conformance/schemas/evidence-record.schema.json`, and can carry the retraction chain forward across runs. R7's existing pass/fail semantics are unchanged; R6 adds evidence-lifecycle metadata alongside them.

## Relationship to the PAMSPEC Internet-Draft

**None.** The evidence model is companion metadata for how PAMSPEC's own claims are audited over time. It is intentionally out of scope for the draft. When R5+R6 evidence exists to justify an R8 core/profiles split, a focused normative change proposal will be prepared then — not now.

## Do not

- Do not delete a record after it is written. If it is wrong, retract-and-supersede.
- Do not edit an evidence file that a permalink references from outside the repo (e.g. `evidence_commit=6ae806b`). Retract-and-supersede in a new commit.
- Do not label a probe `confirmed` when the design cannot rule out alternative explanations. Use `inconclusive` and disclose the gap in `limitations`.
- Do not carry a claim across framework-version bumps without a `regression` record.
