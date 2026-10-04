"""The real backend and the real screen: a mother opens a mother invitation (spec: group-membership,
"Replacing an empty group", and frontend-group, "Open an invitation")."""

import re
import threading

from django.db import connection
from playwright.sync_api import expect

from tests.factories import PASSWORD as FACTORY_PASSWORD
from tests.factories import make_group, make_invitation, make_user

from .test_live_journey import PASSWORD, call, seeded  # noqa: F401  (seeded is a fixture)


def in_thread(django_db_blocker, work):
    """Run database work off the thread of the browser loop, which Django refuses to share."""
    result = {}

    def run():
        result["value"] = work()
        connection.close()

    with django_db_blocker.unblock():
        worker = threading.Thread(target=run)
        worker.start()
        worker.join()
    return result["value"]


def make_waiting_partner(token):
    """Jan started a pending group and invited the mother."""
    jan = make_user("Jan", email=f"jan-{token}@example.com")
    pending = make_group("pending", partner=jan)
    make_invitation(pending, jan, role="woman", token=token)


def sign_in_and_open(page, url, email, password, token):
    page.goto(f"{url}/")
    signed_in = call(page, "login", body={"email": email, "password": password})
    assert signed_in["ok"], signed_in
    page.goto(f"{url}/#/invite/{token}")
    page.reload()


def test_a_mother_with_an_empty_group_joins_the_invited_one(page, seeded, django_db_blocker):  # noqa: F811
    def setup():
        make_waiting_partner("live-mama-1")
        make_group(woman=make_user("Ewa", email="ewa-live-1@example.com"))

    in_thread(django_db_blocker, setup)
    sign_in_and_open(page, seeded, "ewa-live-1@example.com", FACTORY_PASSWORD, "live-mama-1")
    expect(page.get_by_role("heading", level=1)).to_have_text("Jan zaprasza Cię do grupy")
    expect(page.get_by_text(re.compile(r"Jesteś już mamą w swojej grupie"))).to_be_visible()

    page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(page.get_by_role("heading", level=1)).to_have_text("Cześć, Ewa")
    # One group, as the mother: the empty one is gone, so there is no switcher to choose from.
    expect(page.get_by_label("Grupa", exact=True)).to_have_count(0)
    members = call(page, "list_members")["body"]["items"]
    assert sorted(m["display_name"] for m in members) == ["Ewa", "Jan"]


def test_a_mother_with_a_real_group_stays_and_reads_why(page, seeded, django_db_blocker):  # noqa: F811
    in_thread(django_db_blocker, lambda: make_waiting_partner("live-mama-2"))
    sign_in_and_open(page, seeded, "anna@example.com", PASSWORD, "live-mama-2")

    page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(page.get_by_role("alert")).to_have_text(
        re.compile(r"^Jesteś już mamą w innej grupie, w której są dane albo inne osoby\.")
    )
    expect(page.get_by_role("heading", level=1)).to_have_text("Jan zaprasza Cię do grupy")
    expect(page.get_by_role("button", name="Przejdź do swojej grupy")).to_be_visible()
    assert call(page, "get_me")["body"]["membership"]["role"] == "woman"
