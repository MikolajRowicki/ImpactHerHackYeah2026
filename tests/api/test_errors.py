"""Every error the running API produces has the common shape, also the ones Django makes."""

import json

import pytest

from ..factories import make_user

pytestmark = pytest.mark.django_db


def assert_error_shape(response, status, code):
    body = json.loads(response.content)
    assert response.status_code == status
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["message"]
    assert set(body["error"]) <= {"code", "message", "fields"}
    return body["error"]


def test_unknown_path(api):
    response = api.client.get("/api/v1/no-such-thing")
    assert_error_shape(response, 404, "not_found")


def test_unknown_path_with_a_post(api):
    response = api.client.post(
        "/api/v1/no-such-thing",
        "{}",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=api.csrf_token(),
    )
    assert_error_shape(response, 404, "not_found")


def test_wrong_method(api):
    response = api.client.delete("/api/v1/health", HTTP_X_CSRFTOKEN=api.csrf_token())
    assert_error_shape(response, 405, "method_not_allowed")


def test_malformed_json(api):
    response = api.client.post(
        "/api/v1/auth/login",
        "{not json",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=api.csrf_token(),
    )
    assert_error_shape(response, 422, "validation_error")


def test_validation_errors_carry_a_message_per_field(api):
    result = api.call("login", body={"email": "not-an-address", "password": ""})
    assert result.status == 422
    assert result.code == "validation_error"
    assert set(result.error["fields"]) == {"email", "password"}
    assert all(message for message in result.error["fields"].values())


def test_missing_body_fields_are_named(api):
    result = api.call("register", body={})
    assert set(result.error["fields"]) == {"email", "password", "display_name"}


def test_unknown_body_fields_are_refused(api):
    result = api.call("login", body={"email": "a@example.com", "password": "x", "admin": True})
    assert result.status == 422
    assert "admin" in result.error["fields"]


def test_no_session_gives_401(api):
    result = api.call("get_me")
    assert (result.status, result.code) == (401, "unauthorized")


def test_unexpected_failure_gives_500_without_detail(api, monkeypatch):
    def boom(user):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("core.services.accounts.me", boom)
    api.sign_in(make_user())
    response = api.client.get("/api/v1/me")
    error = assert_error_shape(response, 500, "server_error")
    assert "secret" not in response.content.decode()
    assert "RuntimeError" not in response.content.decode()
    assert "fields" not in error


def test_a_post_without_the_csrf_header_is_refused_and_changes_nothing(api):
    user = make_user()
    api.sign_in(user)
    response = api.call("logout", csrf=False, check=False)
    assert (response.status, response.code) == (403, "csrf_failed")
    # The session is still there.
    assert api.call("get_me").status == 200


def test_a_public_post_needs_the_csrf_header_too(api):
    make_user(email="anna@example.com")
    result = api.call(
        "login",
        body={"email": "anna@example.com", "password": "correct-horse-battery"},
        csrf=False,
        check=False,
    )
    assert (result.status, result.code) == (403, "csrf_failed")


def test_a_wrong_csrf_token_is_refused(api):
    response = api.client.post(
        "/api/v1/auth/login", "{}", content_type="application/json", HTTP_X_CSRFTOKEN="wrong"
    )
    assert_error_shape(response, 403, "csrf_failed")


def test_a_get_needs_no_csrf_header(api):
    assert api.call("health", csrf=False).status == 200


def test_a_delete_without_the_csrf_header_is_refused_and_changes_nothing(api):
    user = make_user()
    api.sign_in(user)
    result = api.call("delete_account", csrf=False, check=False)
    assert (result.status, result.code) == (403, "csrf_failed")
    assert api.call("get_me").status == 200
