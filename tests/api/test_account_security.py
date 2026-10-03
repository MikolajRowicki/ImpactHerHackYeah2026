import json
import logging
import re
from datetime import timedelta
from pathlib import Path

import pytest
from django.core import signing

from core.models import MailLog, User
from core.services import account_security

from ..factories import PASSWORD, make_user

pytestmark = pytest.mark.django_db

NOW = "2026-10-03T12:00:00+02:00"
GOOD = {"email": "ola@example.com", "password": "tajne-haslo-1", "display_name": "Ola"}
OK = {"status": "ok"}
EXAMPLES = Path(__file__).resolve().parents[2] / "contracts" / "examples"


def signup(api, **changes):
    return api.call("signup", body={**GOOD, **changes})


def token_in(message, screen):
    """The token of the link in a message, as the frontend would read it from the address bar."""
    found = re.search(rf"#/{screen}/(\S+)", message.body)
    assert found, f"no {screen} link in: {message.body}"
    return found.group(1)


def sign_in(api, email, password):
    return api.call("login", body={"email": email, "password": password})


def activation_token_of(outbox, index=-1):
    return token_in(outbox[index], "activate")


def reset_token_of(outbox, index=-1):
    return token_in(outbox[index], "reset")


def inactive_user(email="ola@example.com", password=PASSWORD):
    return make_user("Ola", email=email, password=password, active=False)


# Sign-up


def test_a_new_address_gets_an_inactive_account_and_one_activation_mail(api, outbox):
    result = signup(api)
    assert (result.status, result.body) == (202, OK)
    user = User.objects.get()
    assert (user.email, user.display_name, user.is_active) == ("ola@example.com", "Ola", False)
    assert user.check_password(GOOD["password"])
    assert "sessionid" not in api.client.cookies
    assert api.call("get_me").status == 401
    assert len(outbox) == 1
    assert outbox[0].to == ["ola@example.com"]
    assert "#/activate/" in outbox[0].body


def test_the_address_is_matched_whatever_its_letter_case(api, outbox):
    inactive_user()
    signup(api, email="OLA@Example.com")
    assert User.objects.count() == 1
    assert len(outbox) == 1


def test_the_answer_for_a_new_and_a_known_active_address_is_byte_for_byte_equal(api, outbox):
    new = signup(api)
    make_user("Anna", email="anna@example.com")
    known = signup(api, email="anna@example.com")
    assert known.status == new.status == 202
    assert known.raw.content == new.raw.content
    assert User.objects.count() == 2


def test_the_answer_for_a_known_inactive_address_is_byte_for_byte_equal(api, outbox):
    new = signup(api)
    again = signup(api, email="ola@example.com", display_name="Ola K.")
    assert again.raw.content == new.raw.content


def test_a_second_signup_does_not_change_an_active_account(api, outbox):
    user = make_user("Anna", email="anna@example.com")
    before = (user.password, user.display_name)
    signup(api, email="anna@example.com", password="inne-haslo-123", display_name="Ktoś")
    user.refresh_from_db()
    assert (user.password, user.display_name, user.is_active) == (*before, True)
    assert User.objects.count() == 1
    assert sign_in(api, "anna@example.com", PASSWORD).status == 200


def test_a_known_active_address_gets_a_mail_that_says_so_and_holds_a_working_reset_link(
    api, outbox
):
    make_user("Anna", email="anna@example.com")
    signup(api, email="anna@example.com")
    assert len(outbox) == 1
    assert outbox[0].to == ["anna@example.com"]
    assert "już istnieje" in outbox[0].body
    assert "#/activate/" not in outbox[0].body
    token = reset_token_of(outbox)
    reset = api.call("confirm_password_reset", body={"token": token, "password": "nowe-haslo-123"})
    assert reset.status == 200


def test_the_account_exists_mail_is_counted_by_its_own_kind(api, outbox):
    make_user("Anna", email="anna@example.com")
    signup(api, email="anna@example.com")
    assert list(MailLog.objects.values_list("kind", flat=True)) == ["account_exists"]


def test_a_second_sign_up_cannot_change_an_inactive_account(api, outbox):
    signup(api)
    signup(api, password="drugie-haslo-12", display_name="Ola K.")
    user = User.objects.get()
    assert user.display_name == GOOD["display_name"]
    assert user.check_password(GOOD["password"])
    assert not user.check_password("drugie-haslo-12")
    assert not user.is_active


def test_a_known_inactive_address_gets_a_new_activation_mail_that_works(api, outbox, clock_at):
    moment = clock_at(NOW)
    signup(api)
    clock_at(moment + timedelta(minutes=2))
    signup(api, password="drugie-haslo-12")
    assert len(outbox) == 2
    assert api.call("activate_account", body={"token": activation_token_of(outbox)}).status == 200
    assert sign_in(api, "ola@example.com", GOOD["password"]).status == 200
    assert sign_in(api, "ola@example.com", "drugie-haslo-12").status == 401


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"email": "not-an-address"}, "email"),
        ({"password": "short"}, "password"),
        ({"password": "x" * 129}, "password"),
        ({"display_name": ""}, "display_name"),
        ({"display_name": "   "}, "display_name"),
        ({"display_name": "x" * 61}, "display_name"),
    ],
)
def test_invalid_signup_fields_are_named_in_polish(api, outbox, changes, field):
    result = signup(api, **changes)
    assert result.status == 422
    assert list(result.error["fields"]) == [field]
    assert result.error["fields"][field]
    assert User.objects.count() == 0
    assert outbox == []


def test_the_signup_422_matches_the_contract_example(api):
    result = signup(api, password="short")
    example = json.loads((EXAMPLES / "signup.422.json").read_text())
    assert result.body["error"]["fields"] == example["error"]["fields"]


def test_the_boundary_lengths_are_accepted(api, outbox):
    result = signup(api, password="x" * 8, display_name="y" * 60)
    assert result.status == 202
    assert len(outbox) == 1


def test_unknown_signup_fields_are_refused(api):
    assert api.call("signup", body={**GOOD, "is_active": True}).status == 422


def test_two_signups_at_the_same_moment_do_not_crash(api, outbox, monkeypatch):
    """The second request looked and found nobody, but the first one has created the account."""
    inactive_user()
    real_find = account_security._find
    calls = []

    def find(email, **kwargs):
        calls.append(email)
        return None if len(calls) == 1 else real_find(email, **kwargs)

    monkeypatch.setattr(account_security, "_find", find)
    result = signup(api)
    assert (result.status, result.body) == (202, OK)
    assert User.objects.count() == 1
    assert len(outbox) == 1
    assert "#/activate/" in outbox[0].body


def test_a_lost_race_against_an_active_account_sends_the_account_exists_mail(
    api, outbox, monkeypatch
):
    make_user("Anna", email="anna@example.com")
    real_find = account_security._find
    calls = []

    def find(email, **kwargs):
        calls.append(email)
        return None if len(calls) == 1 else real_find(email, **kwargs)

    monkeypatch.setattr(account_security, "_find", find)
    assert signup(api, email="anna@example.com").status == 202
    assert "już istnieje" in outbox[0].body


# Activation


def test_an_account_cannot_sign_in_until_it_is_activated_and_can_afterwards(api, outbox):
    signup(api)
    assert sign_in(api, "ola@example.com", GOOD["password"]).status == 401
    result = api.call("activate_account", body={"token": activation_token_of(outbox)})
    assert (result.status, result.body) == (200, OK)
    assert "sessionid" not in api.client.cookies
    signed_in = sign_in(api, "ola@example.com", GOOD["password"])
    assert signed_in.status == 200
    assert signed_in["display_name"] == "Ola"


def test_a_used_token_is_refused(api, outbox):
    signup(api)
    token = activation_token_of(outbox)
    assert api.call("activate_account", body={"token": token}).status == 200
    second = api.call("activate_account", body={"token": token})
    assert (second.status, second.code) == (404, "token_invalid")


def test_a_token_works_for_just_under_three_days(api, outbox, clock_at):
    moment = clock_at(NOW)
    signup(api)
    clock_at(moment + timedelta(days=2, hours=23))
    assert api.call("activate_account", body={"token": activation_token_of(outbox)}).status == 200


def test_a_token_older_than_three_days_is_refused(api, outbox, clock_at):
    moment = clock_at(NOW)
    signup(api)
    clock_at(moment + timedelta(days=3, hours=1))
    result = api.call("activate_account", body={"token": activation_token_of(outbox)})
    assert (result.status, result.code) == (404, "token_invalid")
    assert not User.objects.get().is_active


def test_a_new_link_after_expiry_works(api, outbox, clock_at):
    moment = clock_at(NOW)
    signup(api)
    clock_at(moment + timedelta(days=4))
    api.call("resend_activation", body={"email": "ola@example.com"})
    assert len(outbox) == 2
    assert api.call("activate_account", body={"token": activation_token_of(outbox)}).status == 200


def test_every_refused_token_gets_the_same_answer(api, outbox, clock_at):
    moment = clock_at(NOW)
    signup(api)
    good = activation_token_of(outbox)
    other_salt = signing.TimestampSigner(salt="something-else").sign("1")
    unknown_person = account_security.ClockSigner(salt=account_security.ACTIVATION_SALT).sign("999")
    refused = {
        "forged": good[:-3] + ("aaa" if not good.endswith("aaa") else "bbb"),
        "another person": good.replace(":", ":0", 1),
        "malformed": "not-a-token",
        "garbage": "::::",
        "other salt": other_salt,
        "unknown person": unknown_person,
        "not a number": account_security.ClockSigner(salt=account_security.ACTIVATION_SALT).sign(
            "abc"
        ),
    }
    answers = {name: api.call("activate_account", body={"token": t}) for name, t in refused.items()}
    api.call("activate_account", body={"token": good})
    answers["used"] = api.call("activate_account", body={"token": good})
    clock_at(moment + timedelta(days=5))
    answers["expired"] = api.call("activate_account", body={"token": unknown_person})
    example = json.loads((EXAMPLES / "activate_account.404.json").read_text())
    for name, result in answers.items():
        assert result.status == 404, name
        assert result.body == example, name
        assert result.raw.content == answers["forged"].raw.content, name


def test_a_token_of_an_active_account_is_refused(api):
    user = make_user("Anna", email="anna@example.com")
    token = account_security.activation_token(user)
    result = api.call("activate_account", body={"token": token})
    assert (result.status, result.code) == (404, "token_invalid")


def test_activation_does_not_touch_the_password(api, outbox):
    signup(api)
    api.call("activate_account", body={"token": activation_token_of(outbox)})
    assert User.objects.get().check_password(GOOD["password"])


@pytest.mark.parametrize("body", [{}, {"token": ""}, {"token": "x" * 201}, {"token": "a", "x": 1}])
def test_an_unusable_activation_body_is_a_validation_error(api, body):
    assert api.call("activate_account", body=body).status == 422


# Resending the activation link


def test_resend_gives_identical_answers_and_only_the_inactive_address_gets_mail(api, outbox):
    inactive_user("inactive@example.com")
    make_user("Anna", email="active@example.com")
    answers = {
        name: api.call("resend_activation", body={"email": email})
        for name, email in {
            "inactive": "inactive@example.com",
            "unknown": "nobody@example.com",
            "active": "active@example.com",
        }.items()
    }
    # The same address again at once is throttled; the answer still does not change.
    answers["throttled"] = api.call("resend_activation", body={"email": "inactive@example.com"})
    assert {a.status for a in answers.values()} == {202}
    assert {a.raw.content for a in answers.values()} == {answers["inactive"].raw.content}
    assert answers["inactive"].body == OK
    assert [m.to for m in outbox] == [["inactive@example.com"]]


def test_the_resent_link_activates(api, outbox):
    inactive_user()
    api.call("resend_activation", body={"email": "ola@example.com"})
    assert api.call("activate_account", body={"token": activation_token_of(outbox)}).status == 200
    assert sign_in(api, "ola@example.com", PASSWORD).status == 200


def test_resend_with_a_bad_address_is_a_validation_error(api, outbox):
    result = api.call("resend_activation", body={"email": "nope"})
    assert result.status == 422
    assert "email" in result.error["fields"]
    assert outbox == []


# Password reset


def test_a_reset_request_gives_identical_answers_and_only_a_known_address_gets_mail(api, outbox):
    make_user("Anna", email="anna@example.com")
    inactive_user("inactive@example.com")
    known = api.call("request_password_reset", body={"email": "anna@example.com"})
    unknown = api.call("request_password_reset", body={"email": "nobody@example.com"})
    inactive = api.call("request_password_reset", body={"email": "inactive@example.com"})
    throttled = api.call("request_password_reset", body={"email": "anna@example.com"})
    assert known.status == 202
    assert known.body == OK
    assert {r.raw.content for r in (known, unknown, inactive, throttled)} == {known.raw.content}
    assert [m.to for m in outbox] == [["anna@example.com"]]


def test_a_valid_token_sets_the_new_password(api, outbox):
    user = make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    result = api.call(
        "confirm_password_reset",
        body={"token": reset_token_of(outbox), "password": "nowe-haslo-123"},
    )
    assert (result.status, result.body) == (200, OK)
    assert sign_in(api, "anna@example.com", PASSWORD).status == 401
    assert sign_in(api, "anna@example.com", "nowe-haslo-123").status == 200
    user.refresh_from_db()
    assert user.check_password("nowe-haslo-123")


def test_confirming_a_reset_does_not_sign_the_person_in(api, outbox):
    make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    api.call(
        "confirm_password_reset",
        body={"token": reset_token_of(outbox), "password": "nowe-haslo-123"},
    )
    assert "sessionid" not in api.client.cookies
    assert api.call("get_me").status == 401


def test_a_reset_token_works_once(api, outbox):
    make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    token = reset_token_of(outbox)
    assert (
        api.call(
            "confirm_password_reset", body={"token": token, "password": "nowe-haslo-123"}
        ).status
        == 200
    )
    again = api.call("confirm_password_reset", body={"token": token, "password": "trzecie-haslo-1"})
    assert (again.status, again.code) == (404, "token_invalid")
    assert sign_in(api, "anna@example.com", "nowe-haslo-123").status == 200


def test_a_reset_token_works_for_just_under_an_hour(api, outbox, clock_at):
    moment = clock_at(NOW)
    make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    clock_at(moment + timedelta(minutes=59))
    result = api.call(
        "confirm_password_reset",
        body={"token": reset_token_of(outbox), "password": "nowe-haslo-123"},
    )
    assert result.status == 200


def test_a_reset_token_older_than_an_hour_is_refused(api, outbox, clock_at):
    moment = clock_at(NOW)
    make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    clock_at(moment + timedelta(hours=1, minutes=1))
    result = api.call(
        "confirm_password_reset",
        body={"token": reset_token_of(outbox), "password": "nowe-haslo-123"},
    )
    assert (result.status, result.code) == (404, "token_invalid")
    assert sign_in(api, "anna@example.com", PASSWORD).status == 200


def test_every_refused_reset_token_gets_the_same_answer(api, outbox):
    user = make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    good = reset_token_of(outbox)
    uid, secret = good.split("-", 1)
    other_uid = account_security.urlsafe_base64_encode(b"999")
    refused = {
        "altered": f"{uid}-{secret[:-2]}{'aa' if not secret.endswith('aa') else 'bb'}",
        "another person": f"{other_uid}-{secret}",
        "malformed": "not-a-token",
        "no separator": "abcdef",
        "bad id": f"%%%-{secret}",
        "not a number": f"{account_security.urlsafe_base64_encode(b'abc')}-{secret}",
        "empty parts": "-",
    }
    answers = {
        name: api.call("confirm_password_reset", body={"token": t, "password": "nowe-haslo-123"})
        for name, t in refused.items()
    }
    for name, result in answers.items():
        assert (result.status, result.code) == (404, "token_invalid"), name
        assert result.raw.content == answers["altered"].raw.content, name
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_a_reset_token_of_an_inactive_account_is_refused(api):
    user = inactive_user()
    token = account_security.reset_token(user)
    result = api.call("confirm_password_reset", body={"token": token, "password": "nowe-haslo-123"})
    assert (result.status, result.code) == (404, "token_invalid")


def test_a_reset_ends_the_other_sessions_of_the_person(api, browser, outbox):
    user = make_user("Anna", email="anna@example.com")
    phone, laptop, other_person = browser(user), browser(user), browser(make_user("Piotr"))
    assert phone.call("get_me").status == 200
    api.call("request_password_reset", body={"email": "anna@example.com"})
    api.call(
        "confirm_password_reset",
        body={"token": reset_token_of(outbox), "password": "nowe-haslo-123"},
    )
    assert phone.call("get_me").status == 401
    assert laptop.call("get_me").status == 401
    assert other_person.call("get_me").status == 200


def test_a_weak_password_is_refused_and_the_token_still_works(api, outbox):
    user = make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    token = reset_token_of(outbox)
    weak = api.call("confirm_password_reset", body={"token": token, "password": "short"})
    assert weak.status == 422
    assert weak.error["fields"]["password"] == "Hasło musi mieć co najmniej 8 znaków."
    # Signing in would end the link too (Django hashes the last sign-in), so the row is checked.
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    strong = api.call("confirm_password_reset", body={"token": token, "password": "nowe-haslo-123"})
    assert strong.status == 200
    assert sign_in(api, "anna@example.com", "nowe-haslo-123").status == 200


def test_the_password_boundaries_of_a_reset(api, outbox, clock_at):
    clock_at(NOW)
    make_user("Anna", email="anna@example.com")
    api.call("request_password_reset", body={"email": "anna@example.com"})
    token = reset_token_of(outbox)
    too_long = api.call("confirm_password_reset", body={"token": token, "password": "x" * 129})
    assert too_long.status == 422
    ok = api.call("confirm_password_reset", body={"token": token, "password": "x" * 128})
    assert ok.status == 200
    assert sign_in(api, "anna@example.com", "x" * 128).status == 200


# Changing the password


def test_the_right_current_password_sets_the_new_one(api, browser):
    user = make_user("Anna", email="anna@example.com")
    api.sign_in(user)
    result = api.call(
        "change_password", body={"current_password": PASSWORD, "new_password": "nowe-haslo-123"}
    )
    assert (result.status, result.body) == (200, OK)
    other = browser()
    assert sign_in(other, "anna@example.com", PASSWORD).status == 401
    assert sign_in(other, "anna@example.com", "nowe-haslo-123").status == 200


def test_a_wrong_current_password_is_refused_and_nothing_changes(api):
    user = make_user("Anna", email="anna@example.com")
    api.sign_in(user)
    result = api.call(
        "change_password",
        body={"current_password": "wrong-wrong", "new_password": "nowe-haslo-123"},
    )
    assert result.status == 422
    assert result.error["fields"] == {"current_password": "Obecne hasło jest nieprawidłowe."}
    user.refresh_from_db()
    assert user.check_password(PASSWORD)
    assert api.call("get_me").status == 200


def test_the_current_session_continues_and_the_other_sessions_end(browser):
    user = make_user("Anna", email="anna@example.com")
    here, elsewhere = browser(user), browser(user)
    assert elsewhere.call("get_me").status == 200
    here.call(
        "change_password", body={"current_password": PASSWORD, "new_password": "nowe-haslo-123"}
    )
    assert here.call("get_me").status == 200
    assert elsewhere.call("get_me").status == 401


def test_a_weak_new_password_is_refused(api):
    user = make_user("Anna", email="anna@example.com")
    api.sign_in(user)
    result = api.call(
        "change_password", body={"current_password": PASSWORD, "new_password": "short"}
    )
    assert result.status == 422
    assert list(result.error["fields"]) == ["new_password"]
    user.refresh_from_db()
    assert user.check_password(PASSWORD)


def test_an_empty_current_password_is_named(api):
    api.sign_in(make_user())
    result = api.call(
        "change_password", body={"current_password": "", "new_password": "nowe-haslo-123"}
    )
    assert result.status == 422
    assert "current_password" in result.error["fields"]


def test_changing_the_password_needs_a_session(api):
    result = api.call(
        "change_password", body={"current_password": PASSWORD, "new_password": "nowe-haslo-123"}
    )
    assert (result.status, result.code) == (401, "unauthorized")


# Mail: limits and failures at the level of the operations


def test_the_same_link_twice_within_a_minute_sends_one_mail_and_two_equal_answers(
    api, outbox, clock_at
):
    moment = clock_at(NOW)
    inactive_user()
    first = api.call("resend_activation", body={"email": "ola@example.com"})
    clock_at(moment + timedelta(seconds=30))
    second = api.call("resend_activation", body={"email": "ola@example.com"})
    assert first.raw.content == second.raw.content
    assert len(outbox) == 1
    clock_at(moment + timedelta(seconds=61))
    api.call("resend_activation", body={"email": "ola@example.com"})
    assert len(outbox) == 2


def test_at_most_three_reset_mails_per_hour(api, outbox, clock_at):
    moment = clock_at(NOW)
    make_user("Anna", email="anna@example.com")
    answers = []
    for minute in (0, 2, 4, 6):
        clock_at(moment + timedelta(minutes=minute))
        answers.append(api.call("request_password_reset", body={"email": "anna@example.com"}))
    assert len(outbox) == 3
    assert len({a.raw.content for a in answers}) == 1


def test_the_daily_limit_sends_nothing_logs_an_error_and_changes_no_answer(
    api, outbox, clock_at, caplog
):
    moment = clock_at(NOW)
    before = signup(api, email="first@example.com")
    outbox.clear()
    for number in range(200):
        MailLog.objects.create(kind="x", key_hash=f"k{number}", created_at=moment)
    make_user("Anna", email="anna@example.com")
    with caplog.at_level(logging.ERROR):
        signup_answer = signup(api, email="new@example.com")
        reset_answer = api.call("request_password_reset", body={"email": "anna@example.com"})
    assert outbox == []
    assert "daily limit" in caplog.text
    assert signup_answer.raw.content == before.raw.content == reset_answer.raw.content
    assert User.objects.filter(email="new@example.com").exists()


def test_a_mail_server_that_is_down_still_gives_the_same_answer_and_a_new_link_can_be_asked(
    api, outbox, settings, caplog, clock_at
):
    moment = clock_at(NOW)
    before = signup(api, email="other@example.com")
    settings.EMAIL_BACKEND = "tests.helpers.FailingEmailBackend"
    with caplog.at_level(logging.DEBUG):
        down = signup(api)
    assert down.raw.content == before.raw.content
    user = User.objects.get(email="ola@example.com")
    assert "mail delivery failed" in caplog.text
    assert f"user_id={user.pk}" in caplog.text
    assert "ola@example.com" not in caplog.text
    assert "#/activate/" not in caplog.text
    outbox.clear()
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    clock_at(moment + timedelta(minutes=2))
    api.call("resend_activation", body={"email": "ola@example.com"})
    assert len(outbox) == 1
    assert api.call("activate_account", body={"token": activation_token_of(outbox)}).status == 200


def test_the_limits_hold_across_two_fresh_browsers(browser, outbox, clock_at):
    clock_at(NOW)
    inactive_user()
    first, second = browser(), browser()
    first.call("resend_activation", body={"email": "ola@example.com"})
    answer = second.call("resend_activation", body={"email": "ola@example.com"})
    assert answer.status == 202
    assert len(outbox) == 1
    assert MailLog.objects.filter(kind="activation").count() == 1


def test_links_start_with_the_base_url(api, outbox, settings):
    settings.APP_BASE_URL = "https://mayday.example.org/app/"
    inactive_user()
    make_user("Anna", email="anna@example.com")
    api.call("resend_activation", body={"email": "ola@example.com"})
    api.call("request_password_reset", body={"email": "anna@example.com"})
    assert "https://mayday.example.org/app/#/activate/" in outbox[0].body
    assert "https://mayday.example.org/app/#/reset/" in outbox[1].body


def test_a_base_url_without_a_trailing_slash_gives_one_slash(api, outbox, settings):
    settings.APP_BASE_URL = "https://mayday.example.org"
    inactive_user()
    api.call("resend_activation", body={"email": "ola@example.com"})
    assert "https://mayday.example.org/#/activate/" in outbox[0].body


def test_the_clock_signer_follows_the_frozen_clock(clock_at):
    moment = clock_at(NOW)
    signer = account_security.ClockSigner(salt="s")
    token = signer.sign("7")
    clock_at(moment + timedelta(seconds=100))
    assert signer.unsign(token, max_age=101) == "7"
    with pytest.raises(signing.SignatureExpired):
        signer.unsign(token, max_age=99)


def test_a_malformed_address_is_refused_when_asking_for_a_reset(api):
    result = api.call("request_password_reset", body={"email": "not-an-address"})
    assert result.status == 422
    assert "email" in result.error["fields"]
