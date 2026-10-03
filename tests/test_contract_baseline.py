"""The 23 operations of contract v0 never change; new ones may be added."""

import json

from . import contract as c
from .tools import baseline as b

BASELINE = json.loads(b.BASELINE_PATH.read_text(encoding="utf-8"))


def changed(doc, examples_dir, baseline):
    """Names of baseline entries that are missing or differ in the given contract."""
    current = {
        "operations": b.operation_fingerprints(doc, baseline["operations"]),
        "schemas": b.schema_fingerprints(doc, baseline["schemas"]),
        "examples": b.example_fingerprints(examples_dir, baseline["examples"]),
    }
    return sorted(
        f"{kind}: {name}"
        for kind in ("operations", "schemas", "examples")
        for name, expected in baseline[kind].items()
        if current[kind].get(name) != expected
    )


def test_the_baseline_lists_every_v0_operation():
    assert sorted(BASELINE["operations"]) == sorted(b.V0_OPERATIONS)
    assert len(BASELINE["operations"]) == 23


def test_the_baseline_covers_the_example_files_of_v0():
    for operation_id in b.V0_OPERATIONS:
        assert any(name.startswith(f"{operation_id}.") for name in BASELINE["examples"])


def test_v0_operations_schemas_and_examples_are_unchanged():
    assert changed(c.DOC, c.EXAMPLES_DIR, BASELINE) == []


def test_the_guard_names_a_changed_schema_field():
    doc = json.loads(json.dumps(c.DOC))
    doc["components"]["schemas"]["Task"]["properties"]["title"]["maxLength"] = 99
    result = changed(doc, c.EXAMPLES_DIR, BASELINE)
    assert "schemas: Task" in result
    # Every operation that returns a task is named too.
    assert "operations: claim_task" in result


def test_the_guard_names_a_changed_response_status():
    doc = json.loads(json.dumps(c.DOC))
    del doc["paths"]["/api/v1/tasks/{task_id}/claim"]["post"]["responses"]["409"]
    assert changed(doc, c.EXAMPLES_DIR, BASELINE) == ["operations: claim_task"]


def test_the_guard_names_a_removed_operation():
    doc = json.loads(json.dumps(c.DOC))
    del doc["paths"]["/api/v1/self-care"]
    assert changed(doc, c.EXAMPLES_DIR, BASELINE) == ["operations: list_self_care"]


def test_the_guard_names_a_changed_example_file(tmp_path):
    for path in c.example_files():
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "get_me.200.json").write_text('{"id": 99}', encoding="utf-8")
    assert changed(c.DOC, tmp_path, BASELINE) == ["examples: get_me.200.json"]


def test_the_guard_names_a_deleted_example_file(tmp_path):
    for path in c.example_files():
        if path.name != "login.401.json":
            (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    assert changed(c.DOC, tmp_path, BASELINE) == ["examples: login.401.json"]


def test_a_new_operation_schema_and_example_are_allowed(tmp_path):
    doc = json.loads(json.dumps(c.DOC))
    doc["paths"]["/api/v1/new-thing"] = {
        "get": {"operationId": "new_thing", "responses": {"200": {"description": "ok"}}}
    }
    doc["components"]["schemas"]["NewThing"] = {"type": "object"}
    for path in c.example_files():
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "new_thing.200.json").write_text("{}", encoding="utf-8")
    assert changed(doc, tmp_path, BASELINE) == []


def test_a_new_method_on_an_old_path_is_allowed():
    doc = json.loads(json.dumps(c.DOC))
    doc["paths"]["/api/v1/me"]["delete"] = {
        "operationId": "delete_me",
        "responses": {"200": {"description": "ok"}},
    }
    assert changed(doc, c.EXAMPLES_DIR, BASELINE) == []


def test_the_baseline_file_is_what_the_script_writes():
    assert b.build(c.DOC, c.EXAMPLES_DIR) == BASELINE
