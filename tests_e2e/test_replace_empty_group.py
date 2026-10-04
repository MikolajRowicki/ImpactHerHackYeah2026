"""A mother opens a mother invitation (spec: frontend-group, "Open an invitation")."""

import json
import re

from playwright.sync_api import expect

from .helpers import change_mock_state, h1, open_as

LINK = "/invite/mama-token-1"
NOTICE = re.compile(r"Jesteś już mamą w swojej grupie\. Jeśli jest pusta")
CONTENT_MESSAGE = re.compile(r"^Jesteś już mamą w innej grupie, w której są dane albo inne osoby\.")


def invite_the_mother(page):
    """A partner's pending group has an open invitation for the mother."""
    expect(h1(page)).to_be_visible()  # the demo state exists once the first screen is shown
    change_mock_state(
        page,
        """s.invitations.push({ token: "mama-token-1", group_id: 2, role: "woman",
            invited_by: 102, created_at: "2026-10-03T08:00:00Z",
            expires_at: "2026-10-10T08:00:00Z", used: false });""",
    )


def mock_groups(page):
    return json.loads(page.evaluate("sessionStorage.getItem('mock-state')"))["groups"]


def test_a_mother_is_told_before_she_accepts_a_mother_invitation(mock_page):
    open_as(mock_page, "both")
    invite_the_mother(mock_page)

    mock_page.goto(f"{mock_page.base}#{LINK}")

    expect(mock_page.get_by_text(NOTICE)).to_be_visible()
    expect(mock_page.get_by_text("najpierw ją zamknij i usuń")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Przejdź do swojej grupy")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Przyjmij zaproszenie")).to_be_visible()


def test_a_person_who_is_not_a_mother_sees_no_notice(mock_page):
    open_as(mock_page, "no_group")
    invite_the_mother(mock_page)

    mock_page.goto(f"{mock_page.base}#{LINK}")

    expect(mock_page.get_by_role("button", name="Przyjmij zaproszenie")).to_be_visible()
    expect(mock_page.get_by_text(NOTICE)).to_have_count(0)
    expect(mock_page.get_by_role("button", name="Przejdź do swojej grupy")).to_have_count(0)


def test_a_partner_invitation_shows_no_notice_to_a_mother(mock_page):
    open_as(mock_page, "both", "/invite/k3p9x2vb7qd4")

    expect(mock_page.get_by_role("button", name="Przyjmij zaproszenie")).to_be_visible()
    expect(mock_page.get_by_text(NOTICE)).to_have_count(0)


def test_the_link_leads_to_the_group_screen_of_the_mother(mock_page):
    open_as(mock_page, "both")
    invite_the_mother(mock_page)
    mock_page.goto(f"{mock_page.base}#{LINK}")

    mock_page.get_by_role("button", name="Przejdź do swojej grupy").click()

    expect(mock_page).to_have_url(re.compile(r"#/group$"))
    expect(mock_page.get_by_role("region", name="Osoby w grupie")).to_be_visible()


def test_an_empty_group_is_replaced_when_the_mother_accepts(mock_page):
    open_as(mock_page, "both")
    invite_the_mother(mock_page)
    mock_page.goto(f"{mock_page.base}#{LINK}")

    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(h1(mock_page)).to_have_text("Cześć, Julia")
    switcher = mock_page.get_by_label("Grupa", exact=True)
    expect(switcher.locator("option")).to_have_text(["Grupa: Ewa · Bliska osoba", "Twoja grupa"])
    expect(switcher.locator("option:checked")).to_have_text("Twoja grupa")
    assert sorted(g["id"] for g in mock_groups(mock_page)) == [1, 2, 4]


def test_a_group_with_content_stays_and_the_message_says_why(mock_page):
    open_as(mock_page, "woman")  # Anna's group holds tasks and check-ins
    invite_the_mother(mock_page)
    mock_page.goto(f"{mock_page.base}#{LINK}")

    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(mock_page.get_by_role("alert")).to_have_text(CONTENT_MESSAGE)
    expect(h1(mock_page)).to_have_text(re.compile(r"zaprasza Cię do grupy$"))
    expect(mock_page.get_by_role("button", name="Przejdź do swojej grupy")).to_be_visible()
    assert sorted(g["id"] for g in mock_groups(mock_page)) == [1, 2, 3, 4]
