# Decision: MCP Binding Companion Stabilization Deferred to Post-R9 (OD-X1)

## Status

Accepted

## Date

2026-07-19

## Context

The repository contains a PAMSPEC-over-MCP binding profile (`bindings/mcp/`), a `tools.json` definition, and a Python prototype server (`bindings/mcp/server-python/`). The binding defines MCP tools, resources, error mapping, discovery semantics, and idempotency semantics for PAMSPEC operations. CI already runs the MCP adapter tests and they pass.

R8 OD-X1 asked: should the existing MCP binding work be stabilized and formally promoted as a Companion for R9, or deferred?

## Problem

Stabilizing the MCP binding as a formal Companion requires:
1. Auditing the binding for completeness against Core requirements CR-1 through CR-6
2. Writing at least one end-to-end round-trip test through the MCP server
3. Updating governance documents to reflect Companion status

R9's primary purpose is normative consolidation for IETF -00 submission readiness. Adding the MCP audit and test scope to R9 introduces risk of delay and dilutes the submission narrative.

## Proposed Decision

**Defer MCP binding stabilization to a dedicated post-R9 milestone.**

The existing `bindings/mcp/` work remains in the repository as a draft artifact. It will not be promoted to "stable Companion" status during R9. The CI test suite continues to run MCP adapter tests; those tests protect against regressions but do not constitute a formal conformance audit.

This decision does not delete or invalidate any existing MCP work. It declares that R9 will not include the MCP audit, round-trip test, or formal Companion promotion.

## Alternatives Considered

**Stabilize for R9** — Would add an audit pass + one test to R9 scope. The binding prototype is functional and CI passes. However, "stable Companion" implies an audit against Core CR-1–CR-6 was performed and documented; that audit has not been done. Promoting without the audit would overstate the binding's conformance status. Rejected to keep R9 focused.

## Consequences

- OD-X1 is closed. MCP stabilization becomes a named post-R9 milestone.
- `bindings/mcp/` retains its current "draft binding and Python prototype" status in governance documents.
- R9 governance documents note the deferral explicitly.
- The post-R9 MCP milestone will perform: (a) CR-1–CR-6 audit against the binding's tool definitions, (b) at least one round-trip test through the MCP server, (c) formal Companion promotion in governance documents.

## Interoperability Impact

No immediate impact. The MCP binding is non-normative regardless of Companion status. Deferring stabilization does not prevent external implementations from using or referencing the draft binding.

## Security Impact

None for R9. The post-R9 audit should include a review of how the MCP binding handles authentication, scope enforcement at the MCP layer, and error code leakage.

## Privacy Impact

None for R9.

## Open Questions

None. OD-X1 is resolved. Post-R9 MCP milestone is a separate tracked item.

## References

- R8 `R8-OPEN-DECISIONS.md` OD-X1
- R8 `R8-FORMALIZATION-PROPOSAL.md` §5.5 MCP Binding
- `bindings/mcp/` directory
