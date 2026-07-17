# Examples

These examples illustrate candidate Memory Objects, events, queries, and errors aligned with Sections 8 through 14.

## Files

- `claim.json` — a `claim` Memory Object
- `decision.json` — a `decision` Memory Object
- `task.json` — a `task` Memory Object
- `artifact.json` — an `artifact` Memory Object
- `version-chain.json` — successive versions of a single object
- `lifecycle-transition.json` — a lifecycle transition event
- `semantic-query.json` — a semantic query using an Embedding Space
- `concurrent-update-conflict.json` — an expected-version conflict error

Additional example object types (`tool_invocation`, `tool_result`, `working_memory`, Delegation Object, Evaluation Snapshot, event with `resource_usage`) live in [`../test-vectors/valid/`](../test-vectors/valid/) since they double as positive test vectors.

Every example validates against the corresponding `schemas/0.1-draft/*.schema.json` under `python scripts/validate_test_vectors.py`.

