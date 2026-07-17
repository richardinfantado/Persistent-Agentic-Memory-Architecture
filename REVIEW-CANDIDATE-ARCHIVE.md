# PAMSPEC Review-Candidate Archive

> **No revision of this document has been submitted to or posted by the IETF Datatracker.**
> Active development lives at `draft-infantado-agent-memory-architecture-latest` (see `pamspec-version.json`, key `active_development_docname`). The next possible Datatracker revision, whenever a first submission occurs, will be `-00`.

## What this archive contains

`review-candidates/` preserves internally generated RFCXML/TXT/HTML renderings of the draft source at specific points in time. Each candidate has:

- A `MANIFEST.md` recording the source commit, generation date, build toolchain, per-file SHA-256 checksums, the purpose the rendering served, and an explicit "never submitted to IETF" statement.
- The three rendering files (`rendering.xml`, `rendering.txt`, `rendering.html`) under neutral names — file names deliberately do not carry an IETF revision suffix, because none of these files were assigned an IETF revision.

Candidates are archived after they have served their internal review purpose. They are read-only historical records; they MUST NOT be regenerated in place.

## Current archive

- [`2026-07-18/candidate-a/`](review-candidates/2026-07-18/candidate-a/) — early rendering from the semantic-consistency correction pass (source commit `5d3dd27`). Formerly named `draft-infantado-agent-memory-architecture-00.{xml,txt,html}` at the repository root; renamed and moved under R1.
- [`2026-07-18/candidate-b/`](review-candidates/2026-07-18/candidate-b/) — later rendering from the enhancement + consolidation cycles (source commit `b1ec925`). Formerly named `draft-infantado-agent-memory-architecture-01.{xml,txt,html}` at the repository root; renamed and moved under R1.

## Why the previous naming was corrected

Prior versions of this file (`CORRECTION-BASELINE.md`, replaced by this file in R1) described these renderings as "frozen baseline artifacts corresponding to the initial published `-00` submission" and referred to a "`-01` numbered release procedure." No such submission occurred. Retaining that language would misrepresent this project's IETF status to any reader landing on the repository. The renderings themselves are preserved intact — only the misleading naming, top-level placement, and framing were changed.

## How to produce a new rendering

Active development renders `latest` artifacts on demand:

```bash
python -m pip install -r requirements.txt
gem install kramdown-rfc          # requires Ruby 3.3+
python scripts/build_draft.py all
```

Outputs land in `build/` and use the `latest` docname. They are not archived unless a specific milestone justifies preservation.

The `Build Internet-Draft` GitHub Actions workflow also builds `latest` on every push and uploads the artifacts under the `draft-latest` artifact name for the last workflow run.

## How and when a Datatracker revision would be produced

If and when this project pursues an IETF individual submission, a dedicated release procedure will:

1. Verify the review-candidate-archive contract (no top-level numbered files, no false-publication language anywhere).
2. Build the exact XML that would be submitted, with `docname` set to `draft-infantado-agent-memory-architecture-00` for the first submission.
3. Submit through https://datatracker.ietf.org/submit/ under a specific author's Datatracker account.
4. On acceptance, add a `posted_datatracker_revisions[]` entry to `pamspec-version.json` and archive the submitted rendering with its Datatracker-assigned URL.

Until step 3 has actually occurred, the repository MUST NOT declare any Datatracker revision as posted, frozen, or otherwise published.
