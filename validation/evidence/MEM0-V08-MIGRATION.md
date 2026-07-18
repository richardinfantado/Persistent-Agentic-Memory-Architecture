# Mem0 V08 Evidence Migration

**Purpose:** Explain why the records in `mem0-v08-validation.jsonl` are retrospective, which historical artifacts are authoritative, how classifications were mapped, and what R6.3 did not do.

## Why the records are retrospective

The V08 and V08.1 validation scenarios were written and executed in July 2026 as pytest tests (`validation/tests/test_mem0_validation_scenarios.py`). The R6 EvidenceRecord schema and the `build_retrospective_record()` constructor did not exist at that time. The records in this file are therefore `origin=retrospective_reconstruction`: the R6 EvidenceRecord format was applied after the fact to the existing evidence.

Every record carries `harness_commit=null` because V08/V08.1 were run via pytest validation scenarios, not through the R7 conformance harness.

## Authoritative historical artifacts

| Artifact | Commit | SHA-256 |
|---|---|---|
| `validation/reports/mem0_scenario_results.jsonl` (V08.1) | `6ae806b` | `7c9c9cf21bb9cecb...` |
| `validation/environment-manifest.json` (V08.1) | `6ae806b` | `e7abe35cc8b92094...` |
| `validation/reports/mem0_scenario_results.jsonl` (V08 original) | `8871689` | `8e213699228dbd78...` |

The V08.1 JSONL at commit `6ae806b` is the primary authoritative source. It reflects the corrected experiment including the scenario 7 retraction and all eight final classifications. The V08 original JSONL at `8871689` is cited only in the scenario 7 retracted probe record to preserve the original (wrong) claim and its evidence.

## Classification mapping

Classifications for all scenarios except scenario 7 are drawn directly from the V08.1 JSONL at `6ae806b`. Scenario 7 requires two records (a retracted original and a corrected result).

One classification difference from the V08.1 prose report: scenarios 5, 6, and 8 were reported as `emulated` in V08.1's report text, but the R6 schema requires that `emulated` only applies when a PAMSPEC adapter **demonstrably supplied** the behavior during testing. V08/V08.1 used no PAMSPEC adapter — they probed Mem0's public Python API directly. The corrected R6 classification for these scenarios is:

| Scenario | V08.1 prose | R6.3 record | Reason |
|---|---|---|---|
| 5 (delete/tombstone) | emulated | **gap** | No adapter was tested; native sub-reqs preserved | 
| 6 (provenance) | emulated | **gap** | Source_actor fields require adapter; none tested |
| 8 (unknown fields) | emulated | **gap** | Nested-dict case fails; no adapter was tested |

All three carry `adapter_feasibility=feasible` to indicate that a PAMSPEC adapter could close the gap without modifying Mem0 source.

Scenario 2 (identity/history) uses a sub-requirement `history_entries_are_immutable_versions` classified as `emulated` — this is a sub-requirement classification (not a top-level classification), describing that the history-entry ids conceptually function as an emulated version identity. This is valid because sub-requirement `classification` fields are not constrained by the adapter conditional.

## How R6 records supplement rather than replace the original JSONL

The original `validation/reports/mem0_scenario_results.jsonl` at commits `8871689` and `6ae806b` is the primary machine-readable evidence; those files are not modified. The R6 EvidenceRecords in this directory add:

1. Machine-readable lifecycle metadata: `origin`, `recorded_at`, `evidence_observed_at`, `revises` relationships.
2. Formal `spec_commit` binding to the PAMSPEC spec revision in force during the experiment.
3. Explicit sub-requirement decomposition (scenario 5) in the R6 schema shape.
4. The V08→V08.1 retraction chain for scenario 7, expressed as a pair of records rather than prose.

The R6 records point back to the original JSONL via `results_artifact.sha256` and `evidence_commit`. Readers who want the raw per-scenario outputs should go to the authoritative JSONL; the R6 records provide provenance and lifecycle framing.

## What R6.3 did not do

- Did NOT rerun Mem0 or any validation scenario.
- Did NOT change any V08 or V08.1 historical artifact.
- Did NOT modify the EvidenceRecord schema, harness, or emitter.
- Did NOT add new framework scenarios.
- Did NOT reinterpret evidence beyond correcting the emulated→gap reclassification above (which follows directly from the R6 schema's adapter-required rule).
- Did NOT claim native evidence for any scenario — all records use `origin=retrospective_reconstruction`.
