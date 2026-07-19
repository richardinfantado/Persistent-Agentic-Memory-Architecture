# Pre-Publication Checklist

Resolve or confirm these items before public publication or Datatracker submission:

- Robert Leroux (rl.isapience@gmail.com) is the second-listed formal Internet-Draft co-author and technical reviewer. He is not an editor.
- Confirm whether Robert Leroux contributed additional copyrightable text outside Git and, if so, confirm permission to publish it under the repository documentation license.
- Repository license migration is documented in `LICENSE.md`; preserve attribution and revisit if pre-publication contributor history changes.
- Confirm all newly added references before future revisions promote any informative source to normative status.
- Confirm that OpenBrain remains only informative and non-normative.
- Confirm that PAMSPEC remains an individual contribution and does not imply IETF adoption, RFC publication, or working-group status.
- Confirm that generated Internet-Draft artifacts match `draft-infantado-agent-memory-architecture.md`.
- Do not submit to the IETF Datatracker until the editor intentionally initiates submission.

## R9 Normative Consolidation — Submission Readiness Items

- [x] OD-C4 resolved: idempotency restart durability MUST added to draft §Consistency and Concurrency (`decisions/0031-idempotency-durability-scope.md`).
- [x] OD-P1 resolved: `case_scope_mutation_rejected` and `case_bundle_output_is_deterministic` added to PAMSPEC-Lite; suite now 17 cases; registry entries added; evidence emitter count assertions updated.
- [x] OD-X1 resolved: MCP binding stabilization deferred to post-R9 milestone (`decisions/0032-mcp-companion-stabilization-deferred.md`).
- [x] CR-7 normative MUST added to draft §Query and Retrieval Model (envelope stability, deterministic serialization).
- [x] PAMSPEC-Delegation and PAMSPEC-Subscribe profile sections added to draft §Interoperability and Conformance.
- [x] CONSISTENCY-MATRIX.md updated: idempotency durability note; CR-7 row added; Subscribe profile corrected to PAMSPEC-Subscribe; Delegation profile updated to include PAMSPEC-Delegation.
- [ ] Run `python scripts/validate_repository.py` and confirm clean pass before submitting.
- [ ] Post-R9 backlog (not blocking -00): MCP binding formal Companion audit (CR-1–CR-6 against binding definitions, one round-trip test); R10 TypeScript implementation; IETF Datatracker submission (separate intentional act).
