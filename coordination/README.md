# PAMSPEC Adjacent-Author Coordination Package (R6a)

**Status: prepared, not sent.** Nothing in this directory has been transmitted to any external party. This package exists so the maintainer can review, adjust, and send the outreach when ready. Sending requires separate explicit authorization.

## Purpose

Prepare accurate, respectful, technically specific coordination material for authors and groups working in adjacent agent-memory interoperability areas. The goal is differentiation and coordination, not endorsement, adoption, or ownership of the space.

## Contents

- `contact-matrix.md` — verified author, revision, stream, and contact-method data for AIMEM, SAIHM (+ W3C AI Agent Memory Interoperability CG), FAF/FAFM, and (as academic/research entry) Portable Agent Memory. Every row cites a primary source and access date. No inferred or scraped contact information.
- `pamspec-positioning-note.md` — the one-page description the outreach messages link to. States PAMSPEC's current status precisely, including submission status (`not_submitted`), current development docname (`-latest`), and what PAMSPEC does and does not claim.
- `aimem-technical-questions.md` — seven open technical questions for the AIMEM author, each mapped to a specific documented gap in the R2 crosswalk. The questions are framed as genuine open questions, not as defect reports.
- `outreach-drafts/aimem.md` — draft message to the AIMEM author.
- `outreach-drafts/saihm-w3c.md` — draft message to the SAIHM author / W3C AI Agent Memory Interoperability CG.
- `outreach-drafts/faf.md` — draft message to the FAF/FAFM author.
- `coordination-log-template.md` — template for recording each outreach round (sent-at, recipient, subject, response, next action).

Portable Agent Memory does not have an outreach draft in this package. Its arXiv abstract page does not publish a plaintext contact address; academic outreach requires an additional verification step (retrieve the PDF front matter) before a draft is prepared.

## Constraints observed by this package

- Coordination material only. **No message has been sent.**
- No repository architecture, schema, profile, or conformance behavior changed.
- No new PAMSPEC feature proposed.
- All language reflects `ietf_submission_status = "not_submitted"` and `next_datatracker_revision = "00"`.
- No claim of priority, standardhood, endorsement, or coordination-already-in-progress.
- Contact information is drawn exclusively from primary sources (draft Authors' Addresses sections, datatracker pages, W3C CG page).

## What sending requires

Before any message is sent:

1. Explicit maintainer approval per message.
2. Confirmation that the recipient contact remains published in the primary source (contacts can move; re-check on the day of sending).
3. Recording the send in `coordination-log-template.md` copied into `coordination-log-<recipient>-<YYYY-MM-DD>.md`.
4. If a response is received, log it in the same file and pause before further action so the maintainer can decide.

## Do NOT

- Do NOT paste PAMSPEC contact addresses into unrelated venues.
- Do NOT copy any recipient's private contact data (LinkedIn, personal blogs, etc.) into this repository.
- Do NOT re-frame the AIMEM technical questions as defect reports; they are open questions.
- Do NOT publish outreach content on public lists as coordination "outcomes" until the recipient has responded.
