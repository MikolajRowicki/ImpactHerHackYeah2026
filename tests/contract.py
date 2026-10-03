"""Helpers that read contracts/openapi.yaml and contracts/examples."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "openapi.yaml"
EXAMPLES_DIR = ROOT / "contracts" / "examples"
METHODS = ("get", "post", "put", "patch", "delete")
UNSAFE = ("post", "put", "patch", "delete")

DOC = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def operations():
    """Yield (method, path, operation) for every operation in the contract."""
    for path, item in DOC["paths"].items():
        for method in METHODS:
            if method in item:
                yield method, path, item[method]


def operation_by_id():
    return {op["operationId"]: (method, path, op) for method, path, op in operations()}


def resolve(node):
    """Follow local $ref links until a real node is reached."""
    while isinstance(node, dict) and "$ref" in node:
        target = DOC
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        node = target
    return node


def json_schema(content_holder):
    return resolve(content_holder)["content"]["application/json"]["schema"]


def response_schema(op, status):
    return json_schema(op["responses"][status])


def request_schema(op):
    return json_schema(op["requestBody"])


def declared_statuses(op):
    return sorted(op["responses"])


def is_success(status):
    return status.startswith("2")


def with_components(schema):
    """A root schema in which '#/components/...' references resolve."""
    return {"components": DOC["components"], **schema}


def reachable_schema_names(schema, seen=None):
    """Names of the components/schemas reachable from a schema."""
    seen = set() if seen is None else seen
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if ref:
            name = ref.rsplit("/", 1)[-1]
            if ref.startswith("#/components/schemas/") and name not in seen:
                seen.add(name)
                reachable_schema_names(DOC["components"]["schemas"][name], seen)
        for value in schema.values():
            reachable_schema_names(value, seen)
    elif isinstance(schema, list):
        for value in schema:
            reachable_schema_names(value, seen)
    return seen


def walk(schema):
    """Yield every dict inside a schema, following $ref."""
    stack, seen = [schema], set()
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            ref = node.get("$ref")
            if ref:
                if ref in seen:
                    continue
                seen.add(ref)
                stack.append(resolve(node))
            yield node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


EXAMPLE_NAME = re.compile(
    r"^(?P<op>[a-z_]+)\.(?P<kind>request|\d{3})(?:\.(?P<variant>[a-z_]+))?\.json$"
)


def example_files():
    return sorted(EXAMPLES_DIR.glob("*.json"))


def load_example(path):
    return json.loads(path.read_text(encoding="utf-8"))
