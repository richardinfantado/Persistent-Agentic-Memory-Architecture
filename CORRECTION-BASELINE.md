# PAMSPEC Revision and Artifact Baseline

Starting commit for the -00 corrective pass: `5d3dd27a2f52c0e36ae8dd2842b49347b1ab5dd3`

Corrective branch for that pass: `fix/semantic-consistency-00`

## Artifact policy

- **`draft-infantado-agent-memory-architecture-{00}.{xml,txt,html}`** are frozen baseline artifacts corresponding to the initial published `-00` submission. They MUST NOT be regenerated in place. They are preserved for archival and reproducibility.
- **`draft-infantado-agent-memory-architecture-latest.{xml,txt,html}`** are development artifacts produced by `python scripts/build_draft.py all` from the current `draft-infantado-agent-memory-architecture.md` source. They reflect the current unreleased state.
- **`release/NN/`** artifacts are produced by `python scripts/build_draft.py release --revision NN` for an intentional numbered submission. They are reviewed under the release branch and only then promoted to top-level `draft-infantado-agent-memory-architecture-NN.{xml,txt,html}`.

## Frozen `-00` artifact checksums

| Artifact | SHA-256 |
| --- | --- |
| `draft-infantado-agent-memory-architecture-00.xml` | `E19746A821AA17561ADA9E76C5C5977CB0804CE0995AB10D80091734E6E4CD8D` |
| `draft-infantado-agent-memory-architecture-00.txt` | `63238E2A3B6C6F9122C0FC063E4BEAC006AE1EB7B66902D2B459626BA7FAB366` |
| `draft-infantado-agent-memory-architecture-00.html` | `37B4DDFDF6F6B1404A4BE1B51807EF4CEDBA48132C5C8346EDEA4A31A49D95F8` |

## Current divergence: `-00` frozen vs. `-latest` source

The active `draft-infantado-agent-memory-architecture.md` source has substantially advanced beyond the `-00` frozen artifacts through the `-01` enhancement cycle (P1–P10) and the consolidation cycle (C1–C10). Reviewers landing on the `-00` numbered files will see the smaller, earlier surface; the current source is authoritative for review.

To view the current surface as RFCXML/TXT/HTML:

- CI: every push to a branch runs `.github/workflows/build-internet-draft.yml` which produces `draft-...-latest.{xml,txt,html}` as workflow artifacts.
- Local: `python -m pip install -r requirements.txt`, then `gem install kramdown-rfc` (requires Ruby 3.3+), then `python scripts/build_draft.py all`. Outputs land in `build/`.

## `-01` numbered release procedure

When `-01` is ready for submission:

1. Confirm all schema, repository, reference implementation, and MCP adapter tests pass.
2. Confirm `CONSISTENCY-MATRIX.md` covers every normative concept in the current source.
3. Trigger the `workflow_dispatch` on `Build Internet-Draft` with `revision: 01`.
4. Download the `draft-release-01` workflow artifact.
5. Review the contents.
6. Commit to `release/01/` on the release branch.
7. Promote to top-level `draft-infantado-agent-memory-architecture-01.{xml,txt,html}` in a distinct commit.
8. Add SHA-256 rows to this file for the newly frozen `-01` artifacts.
9. Update `pamspec-version.json` `frozen_internet_draft_revision` to `"01"`.

Ruby / kramdown-rfc / xml2rfc are not available on every developer machine, so the release cut is executed by CI rather than any individual workstation. This preserves reproducibility and keeps the frozen artifacts SHA-256-verifiable against the exact source they were generated from.
