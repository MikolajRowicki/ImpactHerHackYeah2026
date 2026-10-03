import pytest
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate

from . import contract as c


def validator_for(schema):
    return Draft202012Validator(c.with_components(schema), format_checker=FormatChecker())


def test_document_validates():
    validate(c.DOC)


def example_params():
    return [pytest.param(path, id=path.name) for path in c.example_files()]


@pytest.mark.parametrize("path", example_params())
def test_example_matches_its_schema(path):
    match = c.EXAMPLE_NAME.match(path.name)
    assert match, f"{path.name} does not follow <operationId>.<status|request>[.<variant>].json"
    operations = c.operation_by_id()
    assert match["op"] in operations, f"{path.name}: unknown operationId"
    _, _, op = operations[match["op"]]
    if match["kind"] == "request":
        assert "requestBody" in op, f"{path.name}: the operation has no request body"
        schema = c.request_schema(op)
    else:
        assert match["kind"] in op["responses"], f"{path.name}: status is not declared"
        schema = c.response_schema(op, match["kind"])
    errors = sorted(validator_for(schema).iter_errors(c.load_example(path)), key=str)
    assert not errors, "; ".join(f"{list(e.path)}: {e.message}" for e in errors)


def operation_params():
    return [pytest.param(op, id=op["operationId"]) for _, _, op in c.operations()]


@pytest.mark.parametrize("op", operation_params())
def test_every_declared_response_has_an_example(op):
    names = {p.name for p in c.example_files()}
    for status in c.declared_statuses(op):
        expected = f"{op['operationId']}.{status}.json"
        assert expected in names, f"missing example {expected}"


@pytest.mark.parametrize("op", operation_params())
def test_every_operation_with_a_body_has_a_request_example(op):
    if "requestBody" in op:
        names = {p.name for p in c.example_files()}
        assert f"{op['operationId']}.request.json" in names


@pytest.mark.parametrize("op", operation_params())
def test_every_operation_has_a_success_example(op):
    assert any(c.is_success(s) for s in op["responses"])
