# R6 Evidence Emitter — Follow-up Items

Items deferred from the R6.2 gate. Do not merge a new subprocess-backed
native conformance flow without first closing the relevant item.

## R6-FOLLOWUP-01: Per-case subprocess identity parity

**Status:** deferred — in-process path complete, subprocess path not yet blocked.

**Current behavior:** Per-case adapter identity consistency is fully enforced
for in-process adapters (those implementing `evidence_identity()`). The runner
captures `adapter.evidence_identity()` per case and the emitter rejects any
drift from the probe identity.

Subprocess adapters expose identity through `adapter.info` at the probe level,
but the per-case identity path only calls `adapter.evidence_identity()`, which
subprocess adapters do not implement. As a result, a subprocess factory that
returns a different subprocess identity on one case invocation is not detected.

**Impact:** No current R6.2 evidence flow depends on a changing subprocess
adapter factory. reference-python is in-process; its per-case drift is fully
enforced.

**Required before closing:**
- Runner must capture full `_collect_adapter_info(adapter)` per case (not just
  `evidence_identity()`), exposing both subprocess and in-process identity
  uniformly.
- Emitter must resolve per-case identity through `_resolved_runtime_identity`
  (the same function used for the probe) and require that EVERY case has a
  complete resolvable identity that matches the probe.
- Tests: subprocess adapter version changes on one case; subprocess
  implementation version changes on one case; one case returns no runtime
  identity; one case returns a partial runtime identity; identity getter raises
  for one case; all subprocess case identities match.

**Restriction until closed:**
- reference-python native evidence: allowed (in-process path, fully enforced).
- Subprocess-backed native evidence: NOT ALLOWED until this item is closed.
  Subprocess adapters may be used for probes or non-native (retrospective)
  evidence.
- No subprocess implementation may claim full R6 native-emission conformance.
