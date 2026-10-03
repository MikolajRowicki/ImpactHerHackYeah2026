"""Fingerprint of the frozen v0 contract.

`python -m tests.tools.baseline` writes contracts/baseline/v0.json. The guard test computes the
same fingerprint again and compares. Operations, schemas and example files that are not listed in
the baseline are new and are ignored.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "contracts" / "baseline" / "v0.json"

# The operations of contract v0. New operations never join this list.
V0_OPERATIONS = (
    "health",
    "register",
    "login",
    "logout",
    "get_me",
    "create_group",
    "get_group",
    "close_group",
    "list_members",
    "remove_member",
    "create_invitation",
    "get_invitation",
    "accept_invitation",
    "create_check_in",
    "list_check_ins",
    "list_observation_questions",
    "create_observation",
    "get_summary",
    "list_tasks",
    "create_task",
    "claim_task",
    "complete_task",
    "list_self_care",
)
METHODS = ("get", "post", "put", "patch", "delete")


def digest(value) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_refs(doc: dict, node, trail=()):
    """A copy of node in which every local $ref is replaced by what it points to."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if ref:
            if ref in trail:
                return {"$recursive": ref}
            target = doc
            for part in ref.removeprefix("#/").split("/"):
                target = target[part]
            return resolve_refs(doc, target, (*trail, ref))
        return {key: resolve_refs(doc, value, trail) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve_refs(doc, value, trail) for value in node]
    return node


def operation_fingerprints(doc: dict, operation_ids=V0_OPERATIONS) -> dict:
    found = {}
    for path, item in doc["paths"].items():
        for method in METHODS:
            op = item.get(method)
            if op and op["operationId"] in operation_ids:
                effective = {"security": doc.get("security", []), **op}
                found[op["operationId"]] = {
                    "method": method,
                    "path": path,
                    "sha256": digest(resolve_refs(doc, effective)),
                }
    return dict(sorted(found.items()))


def reachable_schemas(doc: dict, operation_ids=V0_OPERATIONS) -> set[str]:
    """Names of the component schemas that the given operations can reach."""
    names: set[str] = set()

    def visit(node):
        if isinstance(node, dict):
            ref = node.get("$ref", "")
            if ref.startswith("#/components/schemas/") and ref.rsplit("/", 1)[-1] not in names:
                name = ref.rsplit("/", 1)[-1]
                names.add(name)
                visit(doc["components"]["schemas"][name])
            elif ref:
                target = doc
                for part in ref.removeprefix("#/").split("/"):
                    target = target[part]
                visit(target)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    for item in doc["paths"].values():
        for method in METHODS:
            op = item.get(method)
            if op and op["operationId"] in operation_ids:
                visit(op)
    return names


def schema_fingerprints(doc: dict, names=None) -> dict:
    schemas = doc["components"]["schemas"]
    chosen = reachable_schemas(doc) if names is None else set(names)
    return {
        name: digest(resolve_refs(doc, schemas[name])) for name in sorted(chosen) if name in schemas
    }


def example_fingerprints(examples_dir: Path, names=None) -> dict:
    files = sorted(examples_dir.glob("*.json"))
    if names is None:
        files = [path for path in files if path.name.split(".")[0] in V0_OPERATIONS]
    else:
        files = [path for path in files if path.name in names]
    # The parsed content is hashed, so line endings and indentation do not matter.
    return {path.name: digest(json.loads(path.read_text(encoding="utf-8"))) for path in files}


def build(doc: dict, examples_dir: Path) -> dict:
    return {
        "version": "v0",
        "operations": operation_fingerprints(doc),
        "schemas": schema_fingerprints(doc),
        "examples": example_fingerprints(examples_dir),
    }


def main() -> int:
    import yaml

    doc = yaml.safe_load((ROOT / "contracts" / "openapi.yaml").read_text(encoding="utf-8"))
    baseline = build(doc, ROOT / "contracts" / "examples")
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"{BASELINE_PATH.relative_to(ROOT)}: {len(baseline['operations'])} operations, "
        f"{len(baseline['schemas'])} schemas, {len(baseline['examples'])} examples"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
