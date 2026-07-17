# AIMEM technical questions

Open questions from PAMSPEC to the AIMEM author. **These are genuine open questions**, not defect reports. AIMEM's design choices may well be right for AIMEM's stated scope even where they differ from PAMSPEC's. The questions exist so both projects can understand where they align, where they diverge, and where coordination would help.

For each question the mapping to the R2 crosswalk row that raised it is given, so the recipient can see the concrete concern.

Each question quotes the AIMEM section it relates to. Recipient is invited to answer in whatever depth is useful — a one-line "yes/no/in progress" per question is a valid response.

## 1. Extension mechanism at chunk-level or envelope-level

**Concern (R2 crosswalk App. A.4, A.5, A.6):** Several PAMSPEC concepts (distinct version identity, monotonic sequence, event history, additional embedding-space descriptor fields, richer provenance) cannot round-trip through AIMEM without a namespaced extension field or block.

**Question:** Is a namespaced extension mechanism planned for chunk-level or envelope-level fields in a future AIMEM revision? For example, an `x-*` field convention or a reserved `extensions` sub-object per chunk or envelope. If so, is there a preferred namespace prefix for third-party extensions?

---

## 2. Strict expected-version rejection as a profile

**Concern (R2 crosswalk App. A.2):** AIMEM permits consumer discretion in resolving updates (a newer update may be rejected or accepted at the consumer's discretion). PAMSPEC's `version_conflict` mandates rejection of stale expected versions. This is characterized as an unresolved semantic mismatch in the R2 crosswalk, not a fundamental incompatibility.

**Question:** Could a downstream profile of AIMEM define strict expected-version rejection semantics for consumers without contradicting AIMEM's baseline consumer behavior? If so, would such a profile be a natural place to declare that PAMSPEC-conformant consumers behave that way?

---

## 3. Distinct object identity, version identity, and monotonic version ordering

**Concern (R2 crosswalk App. A.1):** AIMEM identifies chunks by `urn:aimem:<producer>:<local-id>` and expresses versioning primarily through idempotent re-import rules. PAMSPEC separates stable object identity (`object_id`) from immutable version identity (`version_id`) and monotonic version sequence.

**Question:** In AIMEM's current model, how should a producer represent (a) distinct version identity separate from object identity and (b) monotonic version ordering within an object's history? Is the intent that AIMEM leaves this to the producer's URN convention, or is a future revision expected to formalize it?

---

## 4. Event history and tombstones as first-class records

**Concern (R2 crosswalk App. A.2, A.3):** PAMSPEC records authoritative state changes in an append-only Event Ledger (event history) and represents deletions as terminal deleted versions (tombstones). AIMEM currently flattens state history into re-import rules and represents erasure via a cascade.

**Question:** In an AIMEM bundle, is the intended way to preserve event history and tombstone records to encode them as ordinary chunks, or is there an intent to introduce non-chunk record types (or a per-envelope history block) that would preserve them as first-class records?

---

## 5. Interchange scope: snapshot only or also authoritative updates

**Question:** Is AIMEM intended primarily as an interchange snapshot format (producer publishes a bundle; consumer imports it once, idempotent re-imports refine it), or is it also intended to represent authoritative update semantics across successive bundles (producer publishes a bundle that updates prior state under conflict rules)? The answer affects how the expected-version question in §2 should be scoped.

---

## 6. Reviewing the PAMSPEC–AIMEM mapping appendix

**Question:** Would the AIMEM author be open to reviewing PAMSPEC's field-and-behavior mapping (Appendix A of the R2 crosswalk in the PAMSPEC repository)? Corrections would be welcomed, particularly where PAMSPEC has misread AIMEM's intent. The mapping is intended as the concrete basis for any future coordination.

---

## 7. Coordination without normative coupling

**Question:** What form of cross-reference or coordination between AIMEM and PAMSPEC would be useful without creating normative coupling in either direction? Examples: a mutual reference in each other's "Related work" sections; a joint appendix in a companion document; a shared IANA registration space; a joint test-vector pack. Or is separation without cross-reference preferable for now?

---

## Framing reminder for the sender

- Do not frame these questions as things AIMEM is obligated to fix.
- Do not imply that PAMSPEC's answers are what AIMEM should adopt.
- Preserve the "genuine open question" tone throughout.
- Any answer is a valid answer, including "not planned" or "out of scope for AIMEM."
