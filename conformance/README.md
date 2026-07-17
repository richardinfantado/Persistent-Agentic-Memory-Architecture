# PAMSPEC Conformance Harness

Portable, implementation-agnostic conformance test suite. Drives any
PAMSPEC implementation through a stable adapter interface and reports
which conformance profile requirements are met.

## Why this exists

Static JSON test vectors under `test-vectors/` prove that a given
document validates against a schema. They do **not** prove that an
implementation *behaves correctly* — that it rejects a stale
expected version with `version_conflict`, enforces a delegation's
time window, refuses to overwrite a tombstone, and so on.

The conformance harness runs behavioral tests through an adapter.
An implementation is conformant if the harness's tests for the
profile it claims pass green.

## Layout

- `harness/adapter.py` — abstract `Adapter` interface. Every
  implementation writes a small class that satisfies this.
- `harness/runner.py` — loads the suite, drives the adapter,
  collects results, produces `ConformanceReport` with human-readable
  `summary()` AND machine-readable `to_json()`. JSON reports include
  adapter/implementation metadata (name, version, protocol version,
  spec commit, supported profiles) and the harness's own git commit
  for suite-version pinning.
- `harness/subprocess_adapter.py` — talks to any implementation over
  a versioned JSON-lines stdio protocol (see `harness/PROTOCOL.md`).
  Same suite drives in-process and subprocess adapters.
- `harness/PROTOCOL.md` — versioned harness subprocess protocol
  (v1). This is transport plumbing only; it defines nothing about
  PAMSPEC memory semantics.
- `adapters/reference_python.py` — in-process adapter wrapping the
  Python reference implementation.
- `adapters/reference_python_subprocess.py` — subprocess wrapper
  exposing the same reference implementation over the harness
  stdio protocol.
- `adapters/broken/` — seven **negative-control adapters**, each
  deliberately violating one property. `tests/test_broken_adapters.py`
  asserts each broken adapter fails its designated suite case. If a
  broken adapter starts passing, either the property no longer holds
  or the suite case no longer asserts it — both are bugs.
- `suite/` — the portable behavioral tests. Only use the adapter
  interface; MUST NOT touch implementation internals.
  - `test_lite.py` — PAMSPEC-Lite behavior
  - `test_delegation.py` — Delegation Object enforcement
  - `test_subscription.py` — Subscribe operation
- `adapters/` — one adapter per implementation.
  - `reference_python.py` — reference Python implementation
    (proves the harness works end-to-end).
- `tests/` — pytest cases wiring adapters to the suite.

## Adding a new implementation

1. Write `conformance/adapters/<yourimpl>.py` — a class that
   subclasses `Adapter` and delegates each method to your
   implementation.
2. Write `conformance/tests/test_conformance_<yourimpl>.py` — a
   pytest module that instantiates your adapter and runs the
   suite:
   ```python
   from conformance.harness.runner import run_profile
   from conformance.adapters.yourimpl import YourAdapter
   def test_yourimpl_lite():
       report = run_profile("PAMSPEC-Lite", YourAdapter())
       assert report.passed
   ```
3. Run:
   ```
   PYTHONPATH=conformance python -m pytest conformance/tests
   ```
4. Publish the resulting report under
   `reviews/implementation-report-<yourimpl>.md`.

## Coverage matrix

| Profile | Suite module | Adapter methods used |
| --- | --- | --- |
| `PAMSPEC-Lite` | `suite/test_lite.py` | create, read, update, transition, delete, query, history |
| `PAMSPEC-Core` (delegation) | `suite/test_delegation.py` | grant_delegation, check_delegation, revoke_delegation |
| `PAMSPEC-Ledger` (subscribe) | `suite/test_subscription.py` | subscribe, poll_subscription, close_subscription, plus create |

Additional profiles (semantic query, evaluation snapshots,
attestation) will follow as adapters gain coverage.

## Design principles

1. **Behavioral, not structural.** The harness verifies what
   happens when an operation runs, not just document shape.
2. **Adapter-only surface.** Suite tests interact with the
   implementation only through the adapter interface. Swapping
   implementations requires only a new adapter class.
3. **Normalized errors.** Adapters translate implementation-native
   exceptions into `PamspecErrorLike` with `.code`, `.message`,
   `.retryable` fields — the same taxonomy as the spec's Error
   Model.
4. **Profile-scoped.** Each suite module targets a single profile
   or feature set. An implementation of `PAMSPEC-Lite` is not
   penalized for lacking delegation.
