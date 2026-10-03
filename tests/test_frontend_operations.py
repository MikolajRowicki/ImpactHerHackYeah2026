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
    assert frontend_operations() == contract_operations()
