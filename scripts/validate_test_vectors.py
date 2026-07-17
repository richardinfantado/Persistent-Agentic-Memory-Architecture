from pathlib import Path
import json

from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "0.1-draft"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


schemas = {path.name: load_json(path) for path in SCHEMA_DIR.glob("*.schema.json")}
registry = Registry()
for schema in schemas.values():
    Draft202012Validator.check_schema(schema)
    registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))


def validate_instance(name: str, instance):
    Draft202012Validator(schemas[name], registry=registry).validate(instance)


def schema_for_valid(data):
    if "code" in data and "retryable" in data:
        return "error.schema.json"
    if "query" in data:
        return "query.schema.json"
    if "delegation_id" in data:
        return "delegation.schema.json"
    if "relationship_id" in data:
        return "relationship.schema.json"
    if "event_id" in data:
        return "memory-event.schema.json"
    if "subscription_id" in data and "start_sequence" in data:
        return "subscription.schema.json"
    return "memory-object.schema.json"


for path in (ROOT / "examples").glob("*.json"):
    data = load_json(path)
    if path.name == "version-chain.json":
        continue
    validate_instance(schema_for_valid(data), data)

for path in (ROOT / "test-vectors" / "valid").glob("*.json"):
    data = load_json(path)
    validate_instance(schema_for_valid(data), data)

semantic_rules = {
    "version_id_reuse",
    "silent_overwrite",
    "lifecycle_transition",
    "validation_transition",
    "cross_dimension_transition",
    "cross_scope_policy_required",
    "embedding_space_required",
    "embedding_space_comparison",
}

for path in (ROOT / "test-vectors" / "invalid").glob("*.json"):
    wrapper = load_json(path)
    if "semanticRule" in wrapper:
        if wrapper["semanticRule"] not in semantic_rules:
            raise SystemExit(f"unknown semantic rule in {path}")
        continue

    instance = wrapper["instance"]
    expected = wrapper["expected_failure"]
    if expected in {"version_conflict", "duplicate_operation", "legal_hold", "access_denied"}:
        validate_instance("error.schema.json", instance)
        if instance["code"] != expected:
            raise SystemExit(f"{path} expected code {expected}")
        continue

    try:
        validate_instance(wrapper["schema"], instance)
    except ValidationError:
        continue
    raise SystemExit(f"invalid vector unexpectedly passed: {path}")

print("schema profile, examples, valid vectors, and expected invalid vectors passed")
