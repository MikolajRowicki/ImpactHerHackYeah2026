"""Invitations: issuing, preview, accepting, listing and revoking (spec: group-membership).

The scenario "Constraint holds without the application" is covered in
tests/models/test_constraints.py.
"""

from datetime import timedelta

import pytest

from core import clock
from core.models import Group, Invitation, MailLog, Membership

from ..factories import make_circle, make_group, make_invitation, make_user
from ..helpers import Api
from .test_groups import run_together

pytestmark = pytest.mark.django_db

NOON = "2026-10-03T12:00:00+02:00"
NOT_FOUND = {
    "error": {
        "code": "invitation_not_found",
        "message": "To zaproszenie nie istnieje albo wygasło.",
    }
}


# Issuing


def test_the_woman_invites_a_supporter(api, clock_at):
    clock_at(NOON)
    circle = make_circle()
    result = api.sign_in(circle.anna).call("create_invitation", body={"role": "supporter"})
    assert result.status == 201
    assert result["role"] == "supporter"
    assert 8 <= len(result["token"]) <= 64
    assert result["created_at"] == "2026-10-03T10:00:00Z"
    assert result["expires_at"] == "2026-10-10T10:00:00Z"
    stored = Invitation.objects.get(token=result["token"])
    assert (stored.group, stored.invited_by, stored.used_at) == (circle.group, circle.anna, None)


def test_every_invitation_gets_its_own_token(api):
    circle = make_circle()
    api.sign_in(circle.anna)
    tokens = {api.call("create_invitation", body={"role": "partner"})["token"] for _ in range(5)}
    assert len(tokens) == 5


def test_the_partner_of_a_pending_group_invites_the_woman(api):
    circle = make_circle(status="pending")
    circle.anna.delete()  # a pending group holds only the partner
    result = api.sign_in(circle.piotr).call("create_invitation", body={"role": "woman"})
    assert result.status == 201
    assert result["role"] == "woman"


@pytest.mark.parametrize(
    ("caller", "status", "invited"),
    [
        ("anna", "active", "partner"),
        ("anna", "active", "supporter"),
        ("anna", "pending", "partner"),
        ("anna", "pending", "supporter"),
    ],
)
def test_the_woman_may_invite_partners_and_supporters(api, caller, status, invited):
    circle = make_circle(status=status)
    result = api.sign_in(getattr(circle, caller)).call("create_invitation", body={"role": invited})
    assert result.status == 201


@pytest.mark.parametrize(
    ("caller", "status", "invited"),
    [
        ("piotr", "pending", "supporter"),
        ("piotr", "pending", "partner"),
        ("piotr", "active", "woman"),
        ("piotr", "active", "partner"),
        ("piotr", "active", "supporter"),
        ("anna", "active", "woman"),
        ("anna", "pending", "woman"),
        ("marta", "active", "woman"),
        ("marta", "active", "partner"),
        ("marta", "active", "supporter"),
    ],
)
def test_other_combinations_are_not_allowed(api, caller, status, invited):
    circle = make_circle(status=status)
    result = api.sign_in(getattr(circle, caller)).call("create_invitation", body={"role": invited})
    assert (result.status, result.code) == (403, "role_not_allowed")
    assert result.error["message"] == "Ta rola nie może zapraszać osób w tej roli."
    assert Invitation.objects.count() == 0


def test_a_person_without_a_group_cannot_invite(api):
    result = api.sign_in(make_user()).call("create_invitation", body={"role": "partner"})
    assert (result.status, result.code) == (403, "not_a_member")


@pytest.mark.parametrize(
    ("caller", "invited"), [("anna", "partner"), ("anna", "supporter"), ("piotr", "woman")]
)
def test_a_closed_group_issues_no_invitations(api, caller, invited):
    circle = make_circle(status="closed")
    result = api.sign_in(getattr(circle, caller)).call("create_invitation", body={"role": invited})
    assert (result.status, result.code) == (409, "group_closed")
    assert result.error["message"] == "Ta grupa została zamknięta."
    assert Invitation.objects.count() == 0


def test_a_supporter_in_a_closed_group_is_still_not_allowed(api):
    circle = make_circle(status="closed")
    result = api.sign_in(circle.marta).call("create_invitation", body={"role": "partner"})
    assert (result.status, result.code) == (403, "role_not_allowed")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"role": "mother"},
        {"role": "partner", "email": "not-an-address"},
        {"role": "partner", "x": 1},
    ],
)
def test_a_bad_invitation_request_names_the_field(api, body):
    api.sign_in(make_circle().anna)
    result = api.call("create_invitation", body=body)
    assert result.status == 422
    assert result.error["fields"]
    assert Invitation.objects.count() == 0


def test_an_email_gets_the_link_and_the_answer_does_not_change(api, outbox, settings):
    settings.APP_BASE_URL = "https://mayday.example/"
    circle = make_circle()
    api.sign_in(circle.anna)
    plain = api.call("create_invitation", body={"role": "supporter"})
    with_mail = api.call(
        "create_invitation", body={"role": "supporter", "email": "Ewa@Example.com"}
    )
    assert plain.status == with_mail.status == 201
    assert set(plain.body) == set(with_mail.body)
    assert len(outbox) == 1
    message = outbox[0]
    assert message.to == ["ewa@example.com"]
    assert f"https://mayday.example/#/invite/{with_mail['token']}" in message.body
    assert "7" in message.body


def test_the_invitation_mail_holds_no_names_and_no_health_data(api, outbox):
    circle = make_circle()
    api.sign_in(circle.anna).call("create_invitation", body={"role": "partner", "email": "p@x.pl"})
    text = outbox[0].subject + outbox[0].body
    for private in ("Anna", "Piotr", "Marta", "depresj", "nastr"):
        assert private not in text
    assert "MaydayMama" in text


def test_the_address_is_not_stored(api):
    circle = make_circle()
    api.sign_in(circle.anna).call(
        "create_invitation", body={"role": "partner", "email": "secret-address@example.com"}
    )
    invitation = Invitation.objects.get()
    values = [str(getattr(invitation, f.name)) for f in Invitation._meta.fields]
    assert not any("secret-address" in v for v in values)
    assert not any("secret-address" in str(v) for v in MailLog.objects.values_list())


def test_a_refused_mail_does_not_change_the_answer(api, outbox):
    circle = make_circle()
    api.sign_in(circle.anna)
    body = {"role": "partner", "email": "p@x.pl"}
    first = api.call("create_invitation", body=body)
    # The mail limits refuse a second message to the same address within a minute.
    second = api.call("create_invitation", body=body)
    assert first.status == second.status == 201
    assert len(outbox) == 1


# Preview


def test_a_valid_token_shows_exactly_four_fields_without_a_session(api, clock_at):
    clock_at(NOON)
    circle = make_circle()
    invitation = make_invitation(circle.group, circle.anna, role="partner", token="open-token-1")
    result = api.call("get_invitation", path={"token": invitation.token})
    assert result.status == 200
    assert result.body == {
        "role": "partner",
        "invited_by_name": "Anna",
        "group_status": "active",
        "expires_at": "2026-10-10T10:00:00Z",
    }


def test_the_preview_shows_a_pending_group_as_pending(api):
    circle = make_circle(status="pending")
    make_invitation(circle.group, circle.piotr, role="woman", token="open-token-1")
    assert api.call("get_invitation", path={"token": "open-token-1"})["group_status"] == "pending"


def test_every_unusable_token_gets_the_same_answer(api, clock_at):
    clock_at(NOON)
    circle = make_circle()
    now = clock.now()
    make_invitation(circle.group, circle.anna, token="used-token-1", used_at=now)
    make_invitation(circle.group, circle.anna, token="revoked-token", revoked_at=now)
    make_invitation(circle.group, circle.anna, token="expired-token")
    Invitation.objects.filter(token="expired-token").update(expires_at=now - timedelta(seconds=1))
    answers = {
        name: api.call("get_invitation", path={"token": name})
        for name in ("unknown-token", "used-token-1", "revoked-token", "expired-token", "short")
    }
    for answer in answers.values():
        assert answer.status == 404
        assert answer.body == NOT_FOUND
    assert len({a.raw.content for a in answers.values()}) == 1


def test_a_token_expires_at_its_expiry_moment(api, clock_at):
    clock_at(NOON)
    circle = make_circle()
    invitation = make_invitation(circle.group, circle.anna, token="open-token-1")
    clock_at(invitation.expires_at - timedelta(seconds=1))
    assert api.call("get_invitation", path={"token": "open-token-1"}).status == 200
    clock_at(invitation.expires_at)
    assert api.call("get_invitation", path={"token": "open-token-1"}).status == 404


def test_an_invitation_made_through_the_api_expires_after_seven_days(api, clock_at):
    clock_at(NOON)
    circle = make_circle()
    token = api.sign_in(circle.anna).call("create_invitation", body={"role": "partner"})["token"]
    clock_at("2026-10-10T11:59:59+02:00")
    assert Api().call("get_invitation", path={"token": token}).status == 200
    clock_at("2026-10-10T12:00:00+02:00")
    assert Api().call("get_invitation", path={"token": token}).status == 404


# Accepting


def test_the_woman_accepts_the_invitation_of_a_pending_group(api):
    circle = make_circle(status="pending")
    circle.anna.delete()
    make_invitation(circle.group, circle.piotr, role="woman", token="woman-token-1")
    ola = make_user("Ola")
    result = api.sign_in(ola).call("accept_invitation", path={"token": "woman-token-1"})
    assert result.status == 200
    assert result["membership"] == {
        "group_id": circle.group.pk,
        "role": "woman",
        "group_status": "active",
    }
    circle.group.refresh_from_db()
    assert circle.group.status == "active"
    invitation = Invitation.objects.get(token="woman-token-1")
    assert invitation.used_at is not None
    assert Membership.objects.get(user=ola).invitation == invitation


@pytest.mark.parametrize("role", ["partner", "supporter"])
def test_a_person_joins_with_the_invited_role(api, role):
    circle = make_circle()
    if role == "partner":
        circle.piotr.delete()  # the partner seat is free
    make_invitation(circle.group, circle.anna, role=role, token="role-token-1")
    result = api.sign_in(make_user("Ola")).call("accept_invitation", path={"token": "role-token-1"})
    assert result.status == 200
    assert result["membership"]["role"] == role
    assert result["membership"]["group_status"] == "active"
    names = [m["display_name"] for m in api.call("list_members")["items"]]
    assert "Ola" in names


def test_joining_does_not_activate_a_pending_group_for_a_non_woman(api):
    circle = make_circle(status="pending")
    circle.anna.delete()
    make_invitation(circle.group, circle.piotr, role="supporter", token="sup-token-12")
    result = api.sign_in(make_user("Ola")).call("accept_invitation", path={"token": "sup-token-12"})
    assert result["membership"]["group_status"] == "pending"


def test_a_token_works_once(api):
    circle = make_circle()
    make_invitation(circle.group, circle.anna, token="once-token-1")
    api.sign_in(make_user("Ola"))
    assert api.call("accept_invitation", path={"token": "once-token-1"}).status == 200
    later = (
        Api().sign_in(make_user("Ewa")).call("accept_invitation", path={"token": "once-token-1"})
    )
    assert (later.status, later.code) == (404, "invitation_not_found")
    assert not Membership.objects.filter(user__display_name="Ewa").exists()


@pytest.mark.django_db(transaction=True)
def test_two_simultaneous_accepts_give_one_membership_and_one_404():
    circle = make_circle()
    make_invitation(circle.group, circle.anna, token="race-token-1")
    browsers = [Api().sign_in(make_user(name)) for name in ("Ola", "Ewa")]
    results = run_together(
        [lambda b=b: b.call("accept_invitation", path={"token": "race-token-1"}) for b in browsers]
    )
    assert sorted(r.status for r in results) == [200, 404]
    assert [r.code for r in results if r.status == 404] == ["invitation_not_found"]
    assert Membership.objects.filter(group=circle.group).count() == 4
    assert Membership.objects.filter(invitation__token="race-token-1").count() == 1


def test_a_member_of_other_groups_can_accept_a_partner_or_supporter_invitation(api):
    circle = make_circle()
    other = make_group(woman=make_user("Ewa"))
    make_invitation(other, other.memberships.get().user, token="other-token-1")
    result = api.sign_in(circle.marta).call("accept_invitation", path={"token": "other-token-1"})
    assert result.status == 200
    assert result["membership"] == {
        "group_id": other.pk,
        "role": "supporter",
        "group_status": "active",
    }
    assert Invitation.objects.get(token="other-token-1").used_at is not None
    assert set(Membership.objects.filter(user=circle.marta).values_list("group_id", flat=True)) == {
        circle.group.pk,
        other.pk,
    }


def test_a_person_who_is_already_the_woman_cannot_accept_a_woman_invitation(api):
    circle = make_circle()
    pending = make_group("pending", partner=make_user("Jan"))
    make_invitation(pending, pending.memberships.get().user, role="woman", token="woman-token-2")
    result = api.sign_in(circle.anna).call("accept_invitation", path={"token": "woman-token-2"})
    assert (result.status, result.code) == (409, "already_in_group")
    assert result.error["message"] == "Należysz już do grupy."
    assert Invitation.objects.get(token="woman-token-2").used_at is None
    assert Group.objects.get(pk=pending.pk).status == "pending"


def test_a_supporter_elsewhere_can_become_the_woman_of_a_pending_group(api):
    circle = make_circle()
    pending = make_group("pending", partner=make_user("Jan"))
    make_invitation(pending, pending.memberships.get().user, role="woman", token="woman-token-3")
    result = api.sign_in(circle.marta).call("accept_invitation", path={"token": "woman-token-3"})
    assert result.status == 200
    assert result["membership"]["role"] == "woman"
    assert Group.objects.get(pk=pending.pk).status == "active"
    assert Membership.objects.filter(user=circle.marta).count() == 2


def test_the_same_person_accepting_twice_is_refused_the_second_time(api):
    circle = make_circle()
    make_invitation(circle.group, circle.anna, token="twice-token-1")
    api.sign_in(make_user("Ola"))
    assert api.call("accept_invitation", path={"token": "twice-token-1"}).status == 200
    again = api.call("accept_invitation", path={"token": "twice-token-1"})
    assert (again.status, again.code) == (409, "already_in_group")


def test_a_second_woman_is_refused_and_the_invitation_stays_unused(api):
    circle = make_circle()
    make_invitation(circle.group, circle.piotr, role="woman", token="woman-token-1")
    ola = make_user("Ola")
    result = api.sign_in(ola).call("accept_invitation", path={"token": "woman-token-1"})
    assert (result.status, result.code) == (409, "role_taken")
    assert Invitation.objects.get(token="woman-token-1").used_at is None
    assert not Membership.objects.filter(user=ola).exists()
    assert api.call("get_me")["membership"] is None


def test_a_group_closed_after_the_invitation_refuses_and_keeps_it_unused(api):
    circle = make_circle()
    make_invitation(circle.group, circle.anna, token="late-token-12")
    api.sign_in(circle.anna).call("close_group")
    ola = make_user("Ola")
    result = Api().sign_in(ola).call("accept_invitation", path={"token": "late-token-12"})
    assert (result.status, result.code) == (409, "group_closed")
    assert result.error["message"] == "Ta grupa została zamknięta."
    assert Invitation.objects.get(token="late-token-12").used_at is None
    assert not Membership.objects.filter(user=ola).exists()


def test_a_closed_group_is_reported_before_a_person_who_is_already_in_a_group(api):
    circle = make_circle(status="closed")
    other = make_group(woman=make_user("Ewa"))
    make_invitation(circle.group, circle.anna, token="late-token-12")
    result = api.sign_in(other.memberships.get().user).call(
        "accept_invitation", path={"token": "late-token-12"}
    )
    assert (result.status, result.code) == (409, "group_closed")


@pytest.mark.parametrize("kind", ["unknown", "revoked", "expired"])
def test_an_unusable_token_cannot_be_accepted(api, kind):
    circle = make_circle()
    invitation = make_invitation(circle.group, circle.anna, token="bad-token-123")
    if kind == "revoked":
        Invitation.objects.filter(pk=invitation.pk).update(revoked_at=invitation.created_at)
    if kind == "expired":
        Invitation.objects.filter(pk=invitation.pk).update(
            expires_at=invitation.created_at - timedelta(seconds=1)
        )
    token = "nobody-token" if kind == "unknown" else invitation.token
    ola = make_user("Ola")
    result = api.sign_in(ola).call("accept_invitation", path={"token": token})
    assert result.status == 404
    assert result.body == NOT_FOUND
    assert not Membership.objects.filter(user=ola).exists()


def test_accepting_needs_a_session(api):
    result = api.call("accept_invitation", path={"token": "some-token-12"})
    assert (result.status, result.code) == (401, "unauthorized")


# The journey that starts with the partner


def test_the_partner_first_journey(api, browser):
    piotr = browser(make_user("Piotr"))
    assert piotr.call("create_group", body={"role": "partner"})["status"] == "pending"
    invitation = piotr.call("create_invitation", body={"role": "woman", "email": "a@example.com"})
    assert [i["token"] for i in piotr.call("list_invitations")["items"]] == [invitation["token"]]

    preview = Api().call("get_invitation", path={"token": invitation["token"]})
    assert (preview["role"], preview["invited_by_name"], preview["group_status"]) == (
        "woman",
        "Piotr",
        "pending",
    )

    anna = browser(make_user("Anna"))
    me = anna.call("accept_invitation", path={"token": invitation["token"]})
    assert me["membership"]["role"] == "woman"
    assert me["membership"]["group_status"] == "active"
    assert piotr.call("get_group")["status"] == "active"
    assert piotr.call("get_me")["membership"]["group_status"] == "active"
    assert [m["role"] for m in anna.call("list_members")["items"]] == ["partner", "woman"]
    # The invitation is used: it is gone from the list, and the partner is now a plain partner.
    assert anna.call("list_invitations")["items"] == []
    assert piotr.call("list_invitations").code == "forbidden"
    assert piotr.call("create_invitation", body={"role": "woman"}).code == "role_not_allowed"
    assert anna.call("create_invitation", body={"role": "supporter"}).status == 201


# Listing and revoking


def test_the_list_holds_only_unused_invitations_of_the_group_newest_first(api, clock_at):
    circle = make_circle()
    other = make_group(woman=make_user("Ewa"))
    api.sign_in(circle.anna)
    clock_at("2026-10-03T08:00:00+00:00")
    first = api.call("create_invitation", body={"role": "partner"})["token"]
    clock_at("2026-10-03T09:00:00+00:00")
    second = api.call("create_invitation", body={"role": "supporter"})["token"]
    clock_at("2026-10-03T10:00:00+00:00")
    used = api.call("create_invitation", body={"role": "supporter"})["token"]
    revoked = api.call("create_invitation", body={"role": "supporter"})["token"]
    Invitation.objects.filter(token=used).update(used_at=clock_at("2026-10-03T10:30:00+00:00"))
    api.call("revoke_invitation", path={"token": revoked})
    make_invitation(other, other.memberships.get().user, token="other-token-1")
    result = api.call("list_invitations")
    assert [i["token"] for i in result["items"]] == [second, first]
    assert [i["role"] for i in result["items"]] == ["supporter", "partner"]
    assert all(set(i) == {"token", "role", "created_at", "expires_at"} for i in result["items"])


def test_expired_invitations_are_not_listed(api, clock_at):
    clock_at(NOON)
    circle = make_circle()
    api.sign_in(circle.anna).call("create_invitation", body={"role": "partner"})
    clock_at("2026-10-10T12:00:00+02:00")
    assert api.call("list_invitations")["items"] == []


def test_a_revoked_token_answers_404_on_preview_and_leaves_the_list(api):
    circle = make_circle()
    api.sign_in(circle.anna)
    token = api.call("create_invitation", body={"role": "partner"})["token"]
    assert api.call("revoke_invitation", path={"token": token}).body == {"status": "ok"}
    assert Api().call("get_invitation", path={"token": token}).body == NOT_FOUND
    assert api.call("list_invitations")["items"] == []
    accept = Api().sign_in(make_user("Ola")).call("accept_invitation", path={"token": token})
    assert accept.status == 404


def test_revoking_twice_is_not_found_the_second_time(api):
    circle = make_circle()
    api.sign_in(circle.anna)
    token = api.call("create_invitation", body={"role": "partner"})["token"]
    api.call("revoke_invitation", path={"token": token})
    again = api.call("revoke_invitation", path={"token": token})
    assert (again.status, again.code) == (404, "invitation_not_found")


def test_a_used_unknown_or_foreign_token_cannot_be_revoked(api):
    circle = make_circle()
    other = make_group(woman=make_user("Ewa"))
    make_invitation(other, other.memberships.get().user, token="foreign-token")
    make_invitation(
        circle.group, circle.anna, token="used-token-1", used_at=circle.group.created_at
    )
    api.sign_in(circle.anna)
    for token in ("foreign-token", "used-token-1", "unknown-token"):
        result = api.call("revoke_invitation", path={"token": token})
        assert (result.status, result.code) == (404, "invitation_not_found")
        assert result.body == NOT_FOUND
    assert Invitation.objects.get(token="foreign-token").revoked_at is None
    assert Invitation.objects.get(token="used-token-1").revoked_at is None


def test_the_partner_of_a_pending_group_lists_and_revokes(api):
    circle = make_circle(status="pending")
    circle.anna.delete()
    api.sign_in(circle.piotr)
    token = api.call("create_invitation", body={"role": "woman"})["token"]
    assert len(api.call("list_invitations")["items"]) == 1
    assert api.call("revoke_invitation", path={"token": token}).status == 200
    assert api.call("list_invitations")["items"] == []


@pytest.mark.parametrize("who", ["piotr", "marta"])
def test_others_cannot_list_or_revoke_in_an_active_group(api, who):
    circle = make_circle()
    make_invitation(circle.group, circle.anna, token="open-token-1")
    api.sign_in(getattr(circle, who))
    listed = api.call("list_invitations")
    revoked = api.call("revoke_invitation", path={"token": "open-token-1"})
    for result in (listed, revoked):
        assert (result.status, result.code) == (403, "forbidden")
        assert result.error["message"] == "Zaproszeniami zarządza właścicielka grupy."
    assert Invitation.objects.get(token="open-token-1").revoked_at is None


def test_a_person_without_a_group_cannot_manage_invitations(api):
    api.sign_in(make_user())
    assert api.call("list_invitations").code == "not_a_member"
    assert api.call("revoke_invitation", path={"token": "open-token-1"}).code == "not_a_member"


@pytest.mark.parametrize(
    ("operation", "path"),
    [("list_invitations", None), ("revoke_invitation", {"token": "open-token-1"})]
    + [("create_invitation", None)],
)
def test_managing_invitations_needs_a_session(api, operation, path):
    result = api.call(operation, path=path, body={"role": "partner"})
    assert (result.status, result.code) == (401, "unauthorized")
