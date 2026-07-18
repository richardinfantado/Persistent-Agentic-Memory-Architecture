# BUILD RECEIPT — draft-infantado-agent-memory-architecture-00

## Baseline

| Field | Value |
|---|---|
| Baseline commit (full SHA) | `61d0e166e8ef4a393f0cbf533d652285a622e918` |
| Baseline commit message | `merge: R9 normative consolidation — OD-C4/OD-P1/OD-X1 resolved, PAMSPEC-Lite 17 cases` |
| Branch | `publication/00-submission-readiness` |
| Branch point | `main` at `61d0e166e8ef4a393f0cbf533d652285a622e918` |
| Publication commit | `90cb33502bcb37297aefd8bf1ceea7b7280f9e94` |

## Build Environment

| Component | Version |
|---|---|
| OS | Windows 11 Pro 10.0.26200 |
| Python | 3.14.5 |
| xml2rfc | 3.34.0 |
| kramdown-rfc | 1.7.39 (kramdown-rfc2629 gem) |
| Ruby | 3.3.11 (x64-mingw-ucrt) |
| idnits | NOT AVAILABLE (not installed on build host) |

## Commands Run (in order)

```
# Step 1 — Verify baseline
git log --oneline -3
git status
git diff HEAD
git rev-parse HEAD

# Step 2 — Create publication branch
git checkout -b publication/00-submission-readiness

# Step 3 — Validate repository
python scripts/validate_repository.py
python scripts/validate_test_vectors.py

# Step 4 — Run test suites
PYTHONPATH=implementations/reference-python  python -m pytest implementations/reference-python/tests -q --tb=short
PYTHONPATH=implementations/reference-python;bindings/mcp/server-python  python -m pytest bindings/mcp/server-python/tests -q --tb=short
PYTHONPATH=.;implementations/reference-python  python -m pytest conformance/tests -q --tb=short

# Step 5 — Build submission candidate (first build)
python scripts/build_draft.py submission-candidate --revision 00 --confirm-submission-candidate

# Step 6 — Compute SHA-256 (build 1)
Get-FileHash submission-candidates/00/draft-infantado-agent-memory-architecture-00.xml -Algorithm SHA256
Get-FileHash submission-candidates/00/draft-infantado-agent-memory-architecture-00.txt -Algorithm SHA256
Get-FileHash submission-candidates/00/draft-infantado-agent-memory-architecture-00.html -Algorithm SHA256

# Step 7 — Build submission candidate (second build — reproducibility check)
python scripts/build_draft.py submission-candidate --revision 00 --confirm-submission-candidate

# Step 8 — Compare SHA-256 (build 2 vs build 1) — ALL MATCHED

# Step 9 — Copy artifacts to publication/00/
Copy-Item submission-candidates/00/*.xml publication/00/
Copy-Item submission-candidates/00/*.txt publication/00/
Copy-Item submission-candidates/00/*.html publication/00/
```

## Build Warnings

| Warning | Source | Classification |
|---|---|---|
| `The document date (2026-07-11) is more than 3 days away from today's date` | xml2rfc | Non-blocking. The draft's `date:` field is set to 2026-07-11 (the freeze date for this R9 baseline). xml2rfc emits this advisory when the document date is not within 3 days of the current wall-clock date. The draft date does not prevent submission; it is a cosmetic advisory only. IETF Datatracker accepts a past date. |

No other warnings or errors were produced.

## Validation Results

| Validator | Command | Result |
|---|---|---|
| Repository metadata | `python scripts/validate_repository.py` | PASS — "repository metadata, draft-name, and JSON syntax checks passed; evidence chains validated: 3 file(s)" |
| Test vectors | `python scripts/validate_test_vectors.py` | PASS — "schema profile, examples, valid vectors, and expected invalid vectors passed" |
| Reference implementation tests | `python -m pytest implementations/reference-python/tests` | PASS — 24 passed |
| MCP adapter tests | `python -m pytest bindings/mcp/server-python/tests` | PASS — 6 passed |
| Conformance suite | `python -m pytest conformance/tests` | PASS — 143 passed |
| xml2rfc --v3 --strict (XML validation) | invoked by build script via `xml2rfc --v3 --strict` | PASS (validated.xml produced; advisory date warning only) |
| idnits | N/A | NOT AVAILABLE — idnits not installed on build host. MANUAL CHECK REQUIRED before actual Datatracker upload. |

## Reproducible Build Check

Two consecutive invocations of `python scripts/build_draft.py submission-candidate --revision 00 --confirm-submission-candidate` produced byte-identical output for all three artifact formats.

| Artifact | Build 1 SHA-256 | Build 2 SHA-256 | Match |
|---|---|---|---|
| XML | `8A41577CEC13AFD1451121C5E7D9DE9F2C58C5D0774AC807C1BA2B740CB87FEE` | `8A41577CEC13AFD1451121C5E7D9DE9F2C58C5D0774AC807C1BA2B740CB87FEE` | YES |
| TXT | `441214720126F6CFBA6CE5B7E6F33F265C946CA328948BB6BCA3C525CA1FD784` | `441214720126F6CFBA6CE5B7E6F33F265C946CA328948BB6BCA3C525CA1FD784` | YES |
| HTML | `0B4ADC6D33219869430897E29531B5069FC7B92DBAFE69645EB84F70851A8FAF` | `0B4ADC6D33219869430897E29531B5069FC7B92DBAFE69645EB84F70851A8FAF` | YES |

Build is fully reproducible: identical hashes across both invocations.

## Artifact SHA-256 Hashes (publication/00/ copies)

| File | SHA-256 |
|---|---|
| `draft-infantado-agent-memory-architecture-00.xml` | `8A41577CEC13AFD1451121C5E7D9DE9F2C58C5D0774AC807C1BA2B740CB87FEE` |
| `draft-infantado-agent-memory-architecture-00.txt` | `441214720126F6CFBA6CE5B7E6F33F265C946CA328948BB6BCA3C525CA1FD784` |
| `draft-infantado-agent-memory-architecture-00.html` | `0B4ADC6D33219869430897E29531B5069FC7B92DBAFE69645EB84F70851A8FAF` |

## Worktree Status at Artifact Freeze

```
git status: publication/00/ files created and staged for commit;
submission-candidates/00/ files also created by build script.
No source file modifications.
```

## Files Changed

| File | Change |
|---|---|
| `submission-candidates/00/draft-infantado-agent-memory-architecture-00.xml` | Created by build script |
| `submission-candidates/00/draft-infantado-agent-memory-architecture-00.txt` | Created by build script |
| `submission-candidates/00/draft-infantado-agent-memory-architecture-00.html` | Created by build script |
| `publication/00/draft-infantado-agent-memory-architecture-00.xml` | Copied from submission-candidates/00/ |
| `publication/00/draft-infantado-agent-memory-architecture-00.txt` | Copied from submission-candidates/00/ |
| `publication/00/draft-infantado-agent-memory-architecture-00.html` | Copied from submission-candidates/00/ |
| `publication/00/BUILD-RECEIPT.md` | Created (this file) |
| `publication/00/SUBMISSION-CHECKLIST.md` | Created |
| `publication/00/SUBMISSION-MANIFEST.json` | Created |
| `publication/00/GO-NO-GO.md` | Created |

No Internet-Draft source file (`draft-infantado-agent-memory-architecture.md`) was modified during this publication pass.
