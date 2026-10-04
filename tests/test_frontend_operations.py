import re

from . import contract as c

TABLE = c.ROOT / "src" / "frontend" / "js" / "operations.js"
ROW = re.compile(r'^\s+(\w+): \["(\w+)", "([^"]+)", (\d{3})\],$', re.MULTILINE)


def frontend_operations():
    return {
        name: (method, path, int(status))
        for name, method, path, status in ROW.findall(TABLE.read_text(encoding="utf-8"))
    }


def contract_operations():
    result = {}
    for method, path, op in c.operations():
        success = next(int(s) for s in sorted(op["responses"]) if c.is_success(s))
        result[op["operationId"]] = (method.upper(), path, success)
    return result


def test_frontend_operation_table_matches_the_contract():
    # Operations added after v0 may be missing until the frontend adopts them; the ones it lists
    # must be exact, and it must still list every v0 operation.
    from .tools.baseline import V0_OPERATIONS

    frontend, contract = frontend_operations(), contract_operations()
    assert {name: contract.get(name) for name in frontend} == frontend
    assert set(V0_OPERATIONS) <= set(frontend)


def test_frontend_adopts_the_group_operations():
    assert {
        "list_memberships",
        "leave_group",
        "list_invitations",
        "revoke_invitation",
        "delete_account",
    } <= set(frontend_operations())
