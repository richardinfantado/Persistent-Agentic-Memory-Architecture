# Test Vectors

Valid vectors in `valid/` are expected to pass JSON syntax and applicable schema validation. Invalid vectors in `invalid/` are expected to fail either JSON Schema validation or named semantic rules.

## Running

```sh
python scripts/validate_test_vectors.py
```

The validator loads every `schemas/0.1-draft/*.schema.json`, routes each vector to the correct schema (see `schema_for_valid()` in the script), and confirms:

1. Every valid vector passes its target schema.
2. Every invalid vector either fails schema validation (for `expected_failure` in `{invalid_object, invalid_request}`) or is a named semantic rule known to the validator.

## Invalid vector shapes

```json
{
  "expected_failure": "invalid_object",
  "schema": "delegation.schema.json",
  "instance": { ... a malformed delegation ... }
}
```

or (for semantic failures that require runtime enforcement, not schema alone):

```json
{
  "semanticRule": "delegation_window_inverted",
  "expected_failure": "policy_denied",
  "instance": { ... }
}
```

Semantic rules currently recognized: `version_id_reuse`, `silent_overwrite`, `lifecycle_transition`, `validation_transition`, `cross_dimension_transition`, `cross_scope_policy_required`, `embedding_space_required`, `embedding_space_comparison`, `delegation_window_inverted`, `attestation_window_inverted`, `promote_source_must_be_working_memory`, `evaluation_snapshot_membership_frozen`.

## Coverage

Positive coverage spans every standard object type (`claim`, `decision`, `task`, `artifact`, `observation`, `entity`, `summary`, `tool_invocation`, `tool_result`, `working_memory`), Relationship Objects, Event Ledger entries, Delegation Objects, Subscription descriptors (semantic), and Evaluation Snapshots.

Negative coverage spans each state dimension's forbidden transitions, cross-scope policy failures, missing required fields, out-of-range quality signals, inverted delegation/attestation windows, promotion of a non-working-memory source, mutated sealed snapshots, and every top-level schema's principal required-field violations.
