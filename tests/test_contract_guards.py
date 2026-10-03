import re

import pytest

from . import contract as c

RESOURCE_PREFIXES = {
    "health": "/api/v1/health",
    "authentication": "/api/v1/auth/",
    "current user": "/api/v1/me",
    "group": "/api/v1/groups",
    "members": "/api/v1/members",
    "invitations": "/api/v1/invitations",
    "check-ins": "/api/v1/check-ins",
    "observations": "/api/v1/observations",
    "summary": "/api/v1/summary",
    "tasks": "/api/v1/tasks",
    "self-care": "/api/v1/self-care",
}
GROUP_ROLES = {"woman", "partner", "supporter"}


def operation_params():
    return [pytest.param(op, id=op["operationId"]) for _, _, op in c.operations()]


def test_all_resources_are_present():
    paths = list(c.DOC["paths"])
    for resource, prefix in RESOURCE_PREFIXES.items():
        assert any(p.startswith(prefix) for p in paths), f"no path for {resource}"


def test_every_path_is_under_the_api_prefix():
    assert all(p.startswith("/api/v1/") for p in c.DOC["paths"])


# Conventions


@pytest.mark.parametrize("op", operation_params())
def test_every_operation_declares_roles(op):
    roles = op.get("x-roles")
    assert roles, "x-roles is missing"
    assert set(roles) <= GROUP_ROLES | {"anyone", "signed_in"}


def is_public(op):
    return op.get("security") == []


@pytest.mark.parametrize("op", operation_params())
def test_protected_operations_declare_401(op):
    if "anyone" in op["x-roles"]:
        assert is_public(op) or "security" in op
        return
    assert "401" in op["responses"]


def test_protected_operations_use_the_session_cookie():
    default = c.DOC["security"]
    assert default == [{"sessionCookie": []}]
    for _, _, op in c.operations():
        if "anyone" not in op["x-roles"]:
            security = op.get("security", default)
            assert any("sessionCookie" in requirement for requirement in security)


def test_unsafe_methods_carry_the_csrf_header():
    for method, path, op in c.operations():
        if method in c.UNSAFE:
            security = op.get("security", [])
            assert any("csrfHeader" in r for r in security), f"{method} {path}"


@pytest.mark.parametrize("op", operation_params())
def test_group_role_operations_declare_403(op):
    if set(op["x-roles"]) & GROUP_ROLES:
        assert "403" in op["responses"]


@pytest.mark.parametrize("op", operation_params())
def test_operations_with_a_body_declare_422(op):
    if "requestBody" in op:
        assert "422" in op["responses"]


@pytest.mark.parametrize("op", operation_params())
def test_path_parameter_operations_declare_404(op):
    has_param = any(c.resolve(p)["in"] == "path" for p in op.get("parameters", []))
    if has_param:
        assert "404" in op["responses"]


@pytest.mark.parametrize("op", operation_params())
def test_error_responses_use_the_common_shape(op):
    for status in op["responses"]:
        if not c.is_success(status):
            schema = c.response_schema(op, status)
            assert schema == {"$ref": "#/components/schemas/Error"}, status


def test_error_schema_has_code_message_and_optional_fields():
    error = c.DOC["components"]["schemas"]["Error"]["properties"]["error"]
    assert set(error["required"]) == {"code", "message"}
    assert set(error["properties"]) == {"code", "message", "fields"}


def test_every_point_in_time_is_a_utc_date_time():
    for name, schema in c.DOC["components"]["schemas"].items():
        for prop, definition in schema.get("properties", {}).items():
            if prop.endswith("_at"):
                assert definition.get("format") == "date-time", f"{name}.{prop}"
                assert "UTC" in definition.get("description", ""), f"{name}.{prop}"


def test_example_timestamps_end_with_z():
    for path in c.example_files():
        text = path.read_text(encoding="utf-8")
        for value in re.findall(r'"(\d{4}-\d{2}-\d{2}T[^"]*)"', text):
            assert value.endswith("Z"), f"{path.name}: {value}"


# Privacy


def schema_names_reachable_from_responses():
    """Map schema name -> operation ids whose responses can return it."""
    found = {}
    for _, _, op in c.operations():
        for status in op["responses"]:
            for name in c.reachable_schema_names(c.response_schema(op, status)):
                found.setdefault(name, set()).add(op["operationId"])
    return found


def test_check_ins_are_readable_only_by_the_woman():
    ops = c.operation_by_id()
    for operation_id in ("create_check_in", "list_check_ins"):
        assert ops[operation_id][2]["x-roles"] == ["woman"]
    returned_by = schema_names_reachable_from_responses()
    assert returned_by["CheckIn"] == {"create_check_in", "list_check_ins"}
    assert returned_by["CheckInList"] == {"list_check_ins"}


def test_self_care_is_only_for_the_woman():
    assert c.operation_by_id()["list_self_care"][2]["x-roles"] == ["woman"]


def test_individual_answers_are_never_returned_except_as_question_choices():
    returned_by = schema_names_reachable_from_responses()
    assert returned_by["AnswerValue"] == {"list_observation_questions"}
    assert "ObservationRequest" not in returned_by


def test_summary_has_no_individual_answer_and_no_author():
    ops = c.operation_by_id()
    schema = c.response_schema(ops["get_summary"][2], "200")
    reachable = c.reachable_schema_names(schema)
    assert not reachable & {"AnswerValue", "Person", "CheckIn", "Member", "ObservationRequest"}
    forbidden = {
        "answer",
        "answers",
        "question_id",
        "author",
        "created_by",
        "user_id",
        "display_name",
    }
    for node in c.walk(schema):
        assert not forbidden & set(node.get("properties", {}))


def test_observation_answers_are_closed_values_without_free_text():
    ops = c.operation_by_id()
    schema = c.request_schema(ops["create_observation"][2])
    free_text_names = {"note", "notes", "comment", "text", "description", "message"}
    for node in c.walk(schema):
        assert not free_text_names & set(node.get("properties", {}))
        if node.get("type") == "string":
            assert "enum" in node or "pattern" in node, f"free text string: {node}"


# Permissions


def test_only_the_woman_closes_the_group_and_removes_members():
    ops = c.operation_by_id()
    assert ops["close_group"][2]["x-roles"] == ["woman"]
    assert ops["remove_member"][2]["x-roles"] == ["woman"]


def test_invitation_rules():
    op = c.operation_by_id()["create_invitation"][2]
    assert op["x-roles"] == ["woman", "partner"]
    assert "supporter" not in op["x-roles"]
    assert op["x-invite-rules"] == {"woman": ["partner", "supporter"], "partner": ["woman"]}
    assert op["x-partner-invites-only-while"] == "pending"
    assert "403" in op["responses"]


def test_a_supporter_cannot_create_a_group():
    op = c.operation_by_id()["create_group"][2]
    role = c.resolve(c.request_schema(op))["properties"]["role"]
    assert set(role["enum"]) == {"woman", "partner"}


def test_pending_group_accepts_no_data():
    expected = {
        "create_check_in",
        "create_observation",
        "create_task",
        "claim_task",
        "complete_task",
    }
    marked = {op["operationId"] for _, _, op in c.operations() if op.get("x-requires-active-group")}
    assert marked == expected
    ops = c.operation_by_id()
    for operation_id in expected:
        assert "409" in ops[operation_id][2]["responses"]
    pending = c.load_example(c.EXAMPLES_DIR / "create_check_in.409.json")
    assert pending["error"]["code"] == "group_pending"


# Implemented routes are declared


def normalise(path):
    return re.sub(r"\{[^}]+\}", "{}", path)


def implemented_routes():
    from core.api import api

    for path, item in api.get_openapi_schema()["paths"].items():
        for method in item:
            yield method, normalise(path)


def declared_routes():
    return {(method, normalise(path)) for method, path, _ in c.operations()}


def undeclared_routes(implemented, declared):
    return [route for route in implemented if route not in declared]


def test_every_implemented_route_is_declared():
    undeclared = undeclared_routes(implemented_routes(), declared_routes())
    assert not undeclared, f"routes missing from contracts/openapi.yaml: {undeclared}"


def test_the_guard_reports_a_route_without_a_contract_entry():
    extra = [("get", "/api/v1/not-in-the-contract"), ("delete", "/api/v1/health")]
    assert undeclared_routes(extra, declared_routes()) == extra


def test_health_response_matches_the_contract_example(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == c.load_example(c.EXAMPLES_DIR / "health.200.json")


def test_example_names_in_the_readme_exist():
    text = (c.ROOT / "contracts" / "README.md").read_text(encoding="utf-8")
    names = re.findall(r"`([a-z_]+\.[a-z0-9_]+\.json)`", text)
    assert names
    existing = {p.name for p in c.example_files()}
    for name in names:
        assert name in existing, f"README mentions {name}, which is not in contracts/examples"


def test_a_group_created_by_a_partner_is_pending():
    created = c.load_example(c.EXAMPLES_DIR / "create_group.201.partner.json")
    assert (created["my_role"], created["status"]) == ("partner", "pending")
    me = c.load_example(c.EXAMPLES_DIR / "get_me.200.pending.json")
    assert me["membership"]["group_status"] == "pending"
    created_by_woman = c.load_example(c.EXAMPLES_DIR / "create_group.201.json")
    assert created_by_woman["status"] == "active"


def test_a_closed_group_has_a_declared_answer():
    description = c.DOC["components"]["responses"]["GroupPending"]["description"]
    assert "group_pending" in description
    assert "group_closed" in description
    closed = c.load_example(c.EXAMPLES_DIR / "create_task.409.closed.json")
    assert closed["error"]["code"] == "group_closed"


def test_validation_errors_carry_a_message_per_field():
    for path in c.example_files():
        if path.name.endswith(".422.json"):
            fields = c.load_example(path)["error"].get("fields")
            assert fields, f"{path.name} has no per-field messages"
            assert all(isinstance(m, str) and m for m in fields.values())


SUMMARY_PROPERTIES = {
    "audience",
    "trend",
    "statements",
    "care_reminder",
    "narrative",
    "text",
    "source",
    "generated_at",
}


def test_summary_holds_only_general_fields():
    schema = c.response_schema(c.operation_by_id()["get_summary"][2], "200")
    found = set()
    for node in c.walk(schema):
        found |= set(node.get("properties", {}))
    assert found <= SUMMARY_PROPERTIES, (
        f"unexpected summary fields: {sorted(found - SUMMARY_PROPERTIES)}"
    )


def test_every_date_time_is_marked_utc():
    for name, schema in c.DOC["components"]["schemas"].items():
        for node in c.walk(schema):
            for prop, definition in node.get("properties", {}).items():
                if isinstance(definition, dict) and definition.get("format") == "date-time":
                    assert "UTC" in definition.get("description", ""), f"{name}.{prop}"


def leaf_routes(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if hasattr(pattern, "url_patterns"):
            yield from leaf_routes(pattern.url_patterns, route)
        else:
            yield route


def test_no_url_pattern_under_the_api_prefix_is_undeclared():
    from django.urls import get_resolver

    declared = {normalise(path) for _, path, _ in c.operations()}
    api_routes = [r for r in leaf_routes(get_resolver().url_patterns) if r.startswith("api/v1/")]
    # django-ninja adds one empty pattern at its root; it has no operation behind it.
    api_routes = [r for r in api_routes if r != "api/v1/"]
    undeclared = [
        r for r in api_routes if normalise("/" + re.sub(r"<[^>]+>", "{}", r)) not in declared
    ]
    assert not undeclared, f"URL patterns under /api/v1 missing from the contract: {undeclared}"
