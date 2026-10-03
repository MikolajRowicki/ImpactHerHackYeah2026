import pytest

from core.models import User

from ..factories import PASSWORD, make_circle, make_user

pytestmark = pytest.mark.django_db

GOOD = {"email": "Ola@Example.com", "password": "tajne-haslo-1", "display_name": "Ola"}


# Registration (the v0 operation)


def test_registration_creates_an_account_and_a_session(api):
    result = api.call("register", body=GOOD)
    assert result.status == 201
    assert result["email"] == "ola@example.com"
    assert result["display_name"] == "Ola"
    assert result["membership"] is None
    assert "sessionid" in api.client.cookies
    assert api.call("get_me").status == 200


def test_the_password_is_stored_as_a_hash(api):
    api.call("register", body=GOOD)
    user = User.objects.get()
    assert user.password != GOOD["password"]
    assert user.check_password(GOOD["password"])


@pytest.mark.parametrize("email", ["ola@example.com", "OLA@EXAMPLE.COM", "Ola@Example.com"])
def test_a_duplicate_email_is_refused_in_any_letter_case(api, email):
    make_user("Ola", email="ola@example.com")
    result = api.call("register", body={**GOOD, "email": email})
    assert result.status == 422
    assert result.error["fields"]["email"]
    assert User.objects.count() == 1


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"email": "not-an-address"}, "email"),
        ({"password": "short"}, "password"),
        ({"password": "x" * 129}, "password"),
        ({"display_name": ""}, "display_name"),
        ({"display_name": "x" * 61}, "display_name"),
    ],
)
def test_invalid_fields_are_named(api, changes, field):
    result = api.call("register", body={**GOOD, **changes})
    assert result.status == 422
    assert list(result.error["fields"]) == [field]
    assert User.objects.count() == 0


def test_the_boundary_lengths_are_accepted(api):
    body = {**GOOD, "password": "x" * 8, "display_name": "y" * 60}
    assert api.call("register", body=body).status == 201


def test_registration_can_be_switched_off(api, settings):
    settings.ALLOW_LEGACY_REGISTER = False
    result = api.call("register", body=GOOD)
    assert result.status == 422
    assert "e-mail" in result.error["fields"]["email"]
    assert User.objects.count() == 0
    assert "sessionid" not in api.client.cookies


# Sign in and out


def test_correct_credentials_start_a_session(api):
    make_user("Anna", email="anna@example.com")
    result = api.call("login", body={"email": "ANNA@example.com", "password": PASSWORD})
    assert result.status == 200
    assert result["display_name"] == "Anna"
    assert "sessionid" in api.client.cookies


def test_a_wrong_password_and_an_unknown_email_give_the_same_answer(api):
    make_user("Anna", email="anna@example.com")
    wrong = api.call("login", body={"email": "anna@example.com", "password": "nope-nope"})
    unknown = api.call("login", body={"email": "nobody@example.com", "password": "nope-nope"})
    assert (wrong.status, wrong.code) == (401, "invalid_credentials")
    assert wrong.body == unknown.body
    assert wrong.raw.content == unknown.raw.content


def test_an_inactive_account_cannot_sign_in(api):
    make_user("Anna", email="anna@example.com", active=False)
    wrong = api.call("login", body={"email": "anna@example.com", "password": "nope-nope"})
    inactive = api.call("login", body={"email": "anna@example.com", "password": PASSWORD})
    assert inactive.status == 401
    assert inactive.raw.content == wrong.raw.content
    assert "aktywowane" in inactive.error["message"]
    assert "sessionid" not in api.client.cookies


def test_signing_out_ends_the_session(api):
    api.sign_in(make_user())
    assert api.call("logout").status == 200
    assert api.call("get_me").status == 401


def test_signing_out_needs_a_session(api):
    assert api.call("logout").status == 401


# The current person


def test_a_person_without_a_group_has_no_membership(api):
    user = make_user("Anna", email="anna@example.com")
    result = api.sign_in(user).call("get_me")
    assert result.body == {
        "id": user.pk,
        "email": "anna@example.com",
        "display_name": "Anna",
        "membership": None,
    }


@pytest.mark.parametrize(
    ("who", "role"), [("anna", "woman"), ("piotr", "partner"), ("marta", "supporter")]
)
def test_a_member_sees_group_role_and_status(api, who, role):
    circle = make_circle()
    result = api.sign_in(getattr(circle, who)).call("get_me")
    assert result["membership"] == {
        "group_id": circle.group.pk,
        "role": role,
        "group_status": "active",
    }


def test_a_pending_group_is_shown_as_pending(api):
    circle = make_circle(status="pending")
    result = api.sign_in(circle.piotr).call("get_me")
    assert result["membership"]["group_status"] == "pending"


# Protected operations


def implemented_protected_operations():
    from core.api import api as ninja_api

    from .. import contract as c

    implemented = {
        op["operationId"]
        for item in ninja_api.get_openapi_schema()["paths"].values()
        for op in item.values()
    }
    for operation_id, (_, _, op) in c.operation_by_id().items():
        if operation_id in implemented and "anyone" not in op["x-roles"]:
            yield operation_id


@pytest.mark.parametrize("operation_id", sorted(implemented_protected_operations()))
def test_protected_operations_need_a_session(api, operation_id):
    from .. import contract as c

    _, template, _ = c.operation_by_id()[operation_id]
    path = {name: "1" for name in __import__("re").findall(r"\{(\w+)\}", template)}
    result = api.call(operation_id, body={}, path=path, query={"topic": "how_are_you"})
    assert (result.status, result.code) == (401, "unauthorized")


# Preferences


def test_preferences_default(api):
    result = api.sign_in(make_user()).call("get_preferences")
    assert result.body == {"voivodeship": None, "email_reminders": True}


def test_a_valid_voivodeship_is_saved(api):
    api.sign_in(make_user())
    saved = api.call("update_preferences", body={"voivodeship": "malopolskie"})
    assert saved.body == {"voivodeship": "malopolskie", "email_reminders": True}
    assert api.call("get_preferences").body == saved.body


def test_reminders_can_be_turned_off_and_a_voivodeship_cleared(api):
    api.sign_in(make_user())
    api.call("update_preferences", body={"voivodeship": "slaskie", "email_reminders": False})
    result = api.call("update_preferences", body={"voivodeship": None})
    assert result.body == {"voivodeship": None, "email_reminders": False}


def test_fields_that_are_left_out_keep_their_value(api):
    api.sign_in(make_user())
    api.call("update_preferences", body={"voivodeship": "slaskie"})
    result = api.call("update_preferences", body={"email_reminders": False})
    assert result.body == {"voivodeship": "slaskie", "email_reminders": False}


def test_an_unknown_voivodeship_is_refused(api):
    api.sign_in(make_user())
    result = api.call("update_preferences", body={"voivodeship": "narnia"})
    assert result.status == 422
    assert "voivodeship" in result.error["fields"]
    assert api.call("get_preferences")["voivodeship"] is None


def test_an_empty_update_is_refused(api):
    api.sign_in(make_user())
    assert api.call("update_preferences", body={}).status == 422
