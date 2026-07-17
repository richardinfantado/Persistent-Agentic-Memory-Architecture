# Decision: Portable conformance harness with adapter interface

## Status

Accepted for `-01` consolidation cycle (C11, in response to external
review 2026-07-17).

## Date

2026-07-17

## Context

The `-01` consolidation cycle added JSON test vectors for every -01
feature and unit tests for the Python reference implementation. An
external reviewer noted that this still leaves a gap: the semantic
failures (delegation window, promotion source, snapshot mutation)
are recognized by name in the repository validator but not
*executed* by anything other than the Python reference impl. A
third-party implementation has no portable way to prove behavioral
conformance.

## Problem

Two implementations cannot both claim conformance to
`PAMSPEC-Lite` unless they pass the same behavioral tests. Static
JSON vectors are necessary but not sufficient — they cover shape,
not runtime behavior (idempotency, version conflict, tombstone
blocking, filter defaults, scope isolation).

## Proposed Decision

Add a `conformance/` directory containing:

1. **`harness/adapter.py`** — abstract `Adapter` class defining the
   canonical operation surface (create, read, update, transition,
   delete, query, history, plus Delegation and Subscribe when
   claimed). Adapters translate their implementation's native
   exceptions into `PamspecErrorLike` with stable `.code` /
   `.retryable` fields.
2. **`harness/runner.py`** — discovers `case_*` functions in the
   profile's suite module and executes each against a fresh
   Adapter produced by a factory. Returns a `ConformanceReport`.
3. **`suite/`** — portable behavioral tests. Every function uses
   only the Adapter interface; MUST NOT touch implementation
   internals. Currently: `test_lite.py` (14 cases),
   `test_delegation.py` (7 cases), `test_subscription.py` (4 cases).
4. **`adapters/reference_python.py`** — reference adapter wrapping
   `pamspec_ref.MemoryService`, proving the harness works
   end-to-end.
5. **`tests/test_conformance_reference.py`** — pytest wiring so
   `python -m pytest conformance/tests` runs the suite.

CI extended to run the conformance suite on every push.

## Alternatives Considered

- **Extend the existing JSON test vectors to include operation
  scripts**: rejected because scripting adds a small DSL to
  maintain and does not give implementations a natural in-process
  test hook.
- **Publish only a specification of the tests, no runner**:
  rejected because a runnable harness converges implementations
  faster than a prose spec.
- **Wait for a second implementation before shipping the harness**:
  rejected because a second implementation *needs* the harness in
  order to prove it conforms without inventing its own scaffolding.

## Consequences

- Any implementation can prove PAMSPEC-Lite / -Delegation /
  -Subscribe conformance by writing a ~100-line Adapter subclass
  and running the pytest suite.
- Implementation reports (`reviews/implementation-report-*.md`)
  become straightforward to produce and to verify.
- The harness itself must remain adapter-only — future changes to
  the suite MUST NOT rely on implementation-specific behavior.

## Interoperability Impact

Directly addresses the primary interoperability gap remaining
before external review: portable, executable proof of behavior.

## Security Impact

The harness runs the same authorization-model-independent behavior
across implementations, so weak authorization enforcement in one
implementation cannot silently "pass" a suite designed around
another.

## Privacy Impact

None. All test data is synthetic.

## Unresolved Questions

- Should the harness produce a signed/attested conformance report?
- Should there be a `PAMSPEC-Evaluation` conformance suite that
  validates deterministic-clock and RNG behavior across
  implementations?
- Should conformance report artifacts be uploaded by CI on every
  push to make regression tracking automatic?

## References

- `conformance/README.md`
- `reviews/implementation-report-reference-python.md`
- OpenAI review, 2026-07-17: "The next step should be a reusable
  conformance harness that can test any implementation through a
  standard adapter or endpoint..."
