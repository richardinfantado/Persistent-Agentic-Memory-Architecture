# PAMSPEC vs AMP — validation note

**AMP** — "A Vendor-Neutral Wire Format for Agent Memory Operations" (June 2026 preprint). Proposes: a vendor-neutral memory-operation model; memory types; adapters for Mem0, Letta, Cognee, and other stores; a conformance suite; governance hooks; and framing as complementary to MCP.

This is a concise validation note, not a full crosswalk. R2 already produced the broad standards crosswalk (AIMEM, SAIHM, FAF, Portable Agent Memory); AMP was surfaced by the R8 review as an additional overlap to check. Only overlaps and distinctions relevant to R8's actual evidence — as corrected under V08.1 and V08.2 — are addressed here.

## Overlap surface

AMP overlaps PAMSPEC directly on:

- **Common CRUD operations** (create/read/update/delete + history/search).
- **A wire format** for those operations across frameworks.
- **Memory types** as a vocabulary.
- **Adapters** for Mem0, Letta, and similar stores.
- **A conformance suite**.
- **Governance hooks**.

Under R8's evidence, PAMSPEC therefore cannot distinguish itself by any of those six axes alone. AMP already occupies them.

## What R8 evidence says PAMSPEC's distinct contribution is (V08.1/V08.2)

**V08.1 correction.** V08 of this note listed *authoritative-vs-derived integrity* as one of PAMSPEC's two distinct contributions, on the strength of the V08 scenario-7 finding. That finding was retracted in the V08.1 corrective pass: a properly-controlled experiment (five distinctive control memories + direct fetch of the target's stored embedding from the underlying Chroma collection before and after `update(text=...)`) shows Mem0 DOES refresh the vector — L2 delta ≈ 1.374, old-query rank moved 0→7, new-query rank moved absent→2 (zero-based; matches `mem0_scenario_results.jsonl` exactly). See the reversal notice in `real-framework-validation-report.md`.

Under the corrected evidence, PAMSPEC's demonstrated distinct contribution — that this sprint can actually show — is a **single cluster**:

1. **Stable identity + strict update contract.** Scope immutability (scenario 1, doubly established including cross-tenant visibility), expected-version conflict rejection (scenario 3), and idempotency-key semantics (scenario 4). These are correctness properties on the *authoritative* update path that Mem0 does not enforce today.

The authoritative-vs-derived-integrity argument remains architecturally interesting but is **not evidenced by this sprint**. Classification: architecturally retained, empirically unproven by the current Mem0 sprint. Making an empirical case would require a framework or storage path where an authoritative update demonstrably leaves derived artefacts stale — Mem0 2.0.12 with Chroma is not that framework.

Whether AMP addresses the demonstrated distinct contribution above is the follow-up question. Based on AMP's stated scope as a wire format for operations, plus adapters and governance hooks:

- AMP is well-positioned to standardize the CRUD operation surface. That surface, on its own, does not require nor guarantee scope immutability, expected-version rejection, or idempotency-key semantics — those are behavioral contracts *between* the operations and *around* the authoritative store, not the operation surface itself.
- AMP's governance hooks might or might not cover the three demonstrated gaps. Without reading AMP more thoroughly (the R8 review flagged the preprint but did not require a full field-mapping), this note cannot claim with confidence whether AMP already has these gaps closed.

## Recommendation

**Do not create another broad crosswalk.** R2 covered the broad crosswalks; AMP was flagged after R2 landed. Do these two focused things instead:

1. **Read the AMP preprint against the three demonstrated GAPs above** (V08.1/V08.2 narrowed the earlier four-question form to three by dropping derived-artifact refresh — which Mem0 supplies natively). Specifically ask:
   - Does AMP mandate that scope is immutable on update?
   - Does AMP require expected-version rejection semantics?
   - Does AMP define idempotency-key semantics for its create operation?

   If AMP answers *yes* to all three, PAMSPEC's demonstrated distinct contribution has narrowed further and the venue decision needs re-examination. If AMP answers *no* to any, that answer is precisely PAMSPEC's defensible contribution.
2. **Coordinate with the AMP author** (add to the R6a coordination targets when outreach is later authorized) so that whatever PAMSPEC does define is not a duplicative name for something AMP already covers.

If PAMSPEC's demonstrated distinction cannot survive the AMP comparison after that read, say so plainly in a follow-up note. The R8 evidence would still be useful — it identifies real framework failures — but the standards-venue story would need to be re-argued.

**Explicit non-conclusion:** this note does NOT claim PAMSPEC is more distinct than AMP, or that AMP misses these properties. It says: PAMSPEC's *demonstrated* distinct contribution — from R8 evidence, as corrected under V08.1/V08.2 — is **stable-identity-plus-strict-update-contract**, a single cluster comprising the three gaps above. Whether AMP already covers those is the follow-up question to answer against the preprint, not against a hypothetical.
