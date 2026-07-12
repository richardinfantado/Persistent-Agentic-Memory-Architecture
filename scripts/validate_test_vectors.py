from pathlib import Path
import json
from jsonschema import Draft202012Validator, validate, ValidationError

root = Path(__file__).resolve().parents[1]
schemas = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in (root / "schemas").glob("*.schema.json")}
for schema in schemas.values():
    Draft202012Validator.check_schema(schema)

def validate_valid(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if "query" in data:
        validate(data, schemas["query.schema.json"])
    elif "relationship_id" in data:
        validate(data, schemas["relationship.schema.json"])
    elif "event_id" in data:
        validate(data, schemas["memory-event.schema.json"])
    else:
        validate(data, schemas["memory-object.schema.json"])

for path in (root / "test-vectors" / "valid").glob("*.json"):
    validate_valid(path)

semantic_rules = {
    "version_id_reuse", "silent_overwrite", "lifecycle_transition",
    "validation_transition", "embedding_space_required",
    "embedding_space_comparison", "cross_scope_policy_required"
}
for path in (root / "test-vectors" / "invalid").glob("*.json"):
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    if "semanticRule" in wrapper:
        if wrapper["semanticRule"] not in semantic_rules:
            raise SystemExit(f"unknown semantic rule in {path}")
        continue
    schema_name = wrapper.get("schema")
    instance = wrapper.get("instance")
    expected = wrapper.get("expected_failure")
    if schema_name and expected in {"version_conflict", "duplicate_operation", "legal_hold", "access_denied"}:
        validate(instance, schemas[schema_name])
        if instance.get("code") != expected:
            raise SystemExit(f"{path} expected code {expected}")
        continue
    try:
        validate(instance, schemas[schema_name])
    except ValidationError:
        continue
    raise SystemExit(f"invalid vector unexpectedly passed schema: {path}")
print("schema validation, valid vectors, and expected invalid-vector failures passed")
