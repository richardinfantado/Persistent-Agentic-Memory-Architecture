# PAMSPEC Real-Framework Validation Sprint

**Branch:** `validation/08-real-framework-proof`

**Purpose:** Determine whether PAMSPEC solves real agent-memory problems that an ordinary versioned document store does not, by running PAMSPEC's requirements against an unmodified production-oriented agent-memory framework.

This branch is **implementation-and-evidence**, not governance. It does NOT add new ADRs, reorganize schemas, or rewrite the Internet-Draft. It produces a Mem0 subprocess adapter, a real-framework validation report, a short (≤ 500-word) `what-pamspec-is-for.md`, and three practitioner-outreach drafts.

## Selected framework

**Mem0 OSS**, pinned via `validation/requirements.txt`. Selected because:

- Its public API exposes CRUD + history + filtering + export directly usable through the R7 subprocess protocol.
- Its public issue tracker contains failures (scope mutation, cross-tenant leakage, migration data loss) that directly probe PAMSPEC's scope and identity model.
- It is production-oriented, widely used, and independent of the PAMSPEC repo.

Mem0 source is not modified. Where Mem0 cannot represent a PAMSPEC requirement natively, the adapter records the gap; it does NOT silently emulate away the incompatibility.

## Adapter model

The adapter follows the R7 versioned JSON-lines subprocess protocol (see `conformance/harness/PROTOCOL.md`). Every operation is classified into one of five buckets:

- **Native pass** — Mem0 supports the requirement directly.
- **Adapter-emulated** — the adapter fills the gap; a fresh Mem0-only user would not see this behavior.
- **Framework gap** — the requirement cannot be met with Mem0's current API.
- **PAMSPEC requirement questionable** — evidence suggests the requirement itself is unnecessary or artificial.
- **Not testable** — the scenario cannot be probed with Mem0's public API without modifying Mem0.

A high pass count is not the objective. The objective is discovering which PAMSPEC semantics are real and portable.

## Layout

- `mem0-adapter/` — Mem0 subprocess adapter and its Mem0 configuration.
- `tests/` — pytest wiring that drives the adapter through the eight validation scenarios.
- `reports/` — `real-framework-validation-report.md` (evidence output), `issue-mapping.md` (public-issue → PAMSPEC-requirement mapping), `amp-comparison-note.md` (concise validation note against AMP).
- `what-pamspec-is-for.md` — 500-word maximum core statement. Drafted after evidence exists, not before.
- `outreach-drafts/` — three practitioner-outreach drafts (Mem0 maintainer/contributor, Letta maintainer/active user, LangGraph maintainer/active stateful-agent builder). Prepared, not sent.

## Ground rules

- Mem0 source MUST NOT be modified.
- Do NOT add ADRs.
- Do NOT reorganize schemas.
- Do NOT rewrite the Internet-Draft.
- Do NOT force test outcomes to look green.
- A test failure is a useful result — record it honestly.
- Do NOT add new PAMSPEC memory features to make results look stronger.
