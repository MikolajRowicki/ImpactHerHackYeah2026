"""Runs last. Every operation must have been exercised with its success status by the API tests."""

from pathlib import Path

import pytest

from . import contract as c
from .helpers import EXERCISED


def test_every_operation_is_exercised_with_its_success_status(request):
    tested = {Path(str(item.path)).name for item in request.session.items}
    required = {path.name for path in (Path(__file__).parent / "api").glob("test_*.py")}
    if not required <= tested:
        pytest.skip("Only part of the suite ran; the check needs every tests/api file.")
    missing = []
    for operation_id, (_, _, op) in c.operation_by_id().items():
        success = {int(s) for s in op["responses"] if c.is_success(s)}
        if not {status for name, status in EXERCISED if name == operation_id} & success:
            missing.append(operation_id)
    assert not missing, f"no test calls these operations with a success status: {missing}"
