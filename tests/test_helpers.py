"""The test helpers must fail loudly when a response drifts from the contract."""

import pytest

from . import contract as c
from .factories import make_circle, make_user
from .helpers import EXERCISED, Api, Response


def check(operation_id, status, body):
    op = c.operation_by_id()[operation_id][2]
    Api.check_contract(operation_id, op, Response(status, body, None))


ME = {"id": 1, "email": "a@example.com", "display_name": "Anna", "membership": None}


def test_a_matching_response_passes():
    check("get_me", 200, ME)


def test_an_extra_field_fails():
    with pytest.raises(AssertionError, match="breaks the contract"):
        check("get_me", 200, {**ME, "password": "x"})


def test_a_missing_field_fails():
    with pytest.raises(AssertionError, match="breaks the contract"):
        check("get_me", 200, {k: v for k, v in ME.items() if k != "email"})


def test_a_wrong_type_fails():
    with pytest.raises(AssertionError, match="breaks the contract"):
        check("get_me", 200, {**ME, "id": "one"})


def test_an_undeclared_status_fails():
    error = {"error": {"code": "teapot", "message": "x"}}
    with pytest.raises(AssertionError, match="declares"):
        check("get_me", 418, error)


def test_an_error_body_of_another_shape_fails():
    with pytest.raises(AssertionError, match="breaks the contract"):
        check("get_me", 401, {"detail": "Unauthorized"})


def test_a_timestamp_that_is_not_utc_fails():
    group = {
        "id": 1,
        "status": "active",
        "my_role": "woman",
        "created_at": "2026-10-03T10:00:00+02:00",
    }
    with pytest.raises(AssertionError, match="not UTC"):
        check("get_group", 200, group)


def test_calls_are_recorded(api):
    api.call("health")
    assert ("health", 200) in EXERCISED


def test_a_call_through_the_helper_fails_when_the_backend_drifts(api, monkeypatch):
    from core.services import accounts

    real = accounts.me
    monkeypatch.setattr(accounts, "me", lambda user: {**real(user), "id": "not-a-number"})
    api.sign_in(make_user())
    with pytest.raises(Exception, match="get_me|validation|int"):
        api.call("get_me")


def test_the_circle_factory_builds_the_example_people(db):
    circle = make_circle()
    assert [u.display_name for u in (circle.anna, circle.piotr, circle.marta)] == [
        "Anna",
        "Piotr",
        "Marta",
    ]
    assert circle.group.memberships.count() == 3


def test_the_clock_fixture_freezes_and_releases(clock_at):
    from core import clock

    clock_at("2026-10-03T23:30:00+00:00")
    assert clock.today().isoformat() == "2026-10-04"  # past midnight in Warsaw
    assert clock.now().isoformat() == "2026-10-03T23:30:00+00:00"
