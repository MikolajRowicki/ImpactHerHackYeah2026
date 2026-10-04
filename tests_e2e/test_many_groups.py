"""One person in many groups: the panel, the switcher and the invitations around them."""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect

from .helpers import change_mock_state, h1, nav, open_as

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"
OWN = "Twoja grupa"
EWAS = "Grupa: Ewa · Bliska osoba"
JULIAS = "Grupa: Julia · Bliska osoba"


def switcher(page):
    return page.get_by_label("Grupa", exact=True)


def nav_names(page):
    return nav(page).get_by_role("link").all_inner_texts()


def invite_to_julias_group(page, role="supporter"):
    """Another mother's group has an open invitation, as if she had sent it."""
    expect(h1(page)).to_be_visible()  # the demo state exists once the first screen is shown
    change_mock_state(
        page,
        f"""s.invitations.push({{ token: "julia-token-1", group_id: 3, role: "{role}",
            invited_by: 103, created_at: "2026-10-03T08:00:00Z",
            expires_at: "2026-10-10T08:00:00Z", used: false }});""",
    )


# The panel


def test_panel_offers_three_choices_to_a_person_without_a_group(mock_page):
    open_as(mock_page, "no_group")

    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()
    for choice in ("Jestem mamą", "Jestem Partnerem", "Poczekam na link od mamy"):
        expect(mock_page.get_by_role("button", name=choice)).to_be_visible()
    expect(switcher(mock_page)).to_have_count(0)


def test_waiting_for_a_link_creates_no_group(mock_page):
    open_as(mock_page, "no_group")

    mock_page.get_by_role("button", name="Poczekam na link od mamy").click()

    expect(mock_page.get_by_text("Poproś mamę o link")).to_be_visible()
    expect(mock_page.get_by_text("Żadna grupa nie została założona.")).to_be_visible()
    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()
    assert nav_names(mock_page) == ["Start", "Pomoc"]


def test_partner_starts_a_group_from_the_panel(mock_page):
    open_as(mock_page, "no_group")

    mock_page.get_by_role("button", name="Jestem Partnerem").click()

    expect(h1(mock_page)).to_have_text("Czekamy na mamę")
    expect(mock_page.get_by_role("heading", name="Zaproś mamę")).to_be_visible()


def test_a_person_with_a_group_adds_another_from_a_dialog_without_the_mother_choice(mock_page):
    open_as(mock_page, "woman")

    mock_page.get_by_role("button", name="Dodaj grupę").click()

    dialog = mock_page.get_by_role("dialog", name="Dodaj grupę")
    expect(dialog.get_by_role("button", name="Jestem Partnerem")).to_be_visible()
    expect(dialog.get_by_role("button", name="Poczekam na link od mamy")).to_be_visible()
    expect(dialog.get_by_role("button", name="Jestem mamą")).to_have_count(0)


def test_a_supporter_who_is_no_mother_yet_can_start_her_own_group_from_the_dialog(mock_page):
    open_as(mock_page, "supporter")

    mock_page.get_by_role("button", name="Dodaj grupę").click()
    mock_page.get_by_role("dialog").get_by_role("button", name="Jestem mamą").click()

    expect(mock_page.get_by_role("dialog")).to_have_count(0)
    expect(h1(mock_page)).to_have_text("Cześć, Marta")
    expect(mock_page.get_by_role("heading", name="Zaproś Partnera i bliskie osoby")).to_be_visible()
    expect(switcher(mock_page).locator("option")).to_have_text(
        [OWN, "Grupa: Anna · Bliska osoba"][::-1]
    )


# The switcher


def test_a_person_with_one_group_sees_its_name_and_no_switcher(mock_page):
    open_as(mock_page, "supporter")

    expect(switcher(mock_page)).to_have_count(0)
    expect(mock_page.locator(".group-bar__name")).to_contain_text("Grupa: Anna · Bliska osoba")


def test_the_switcher_lists_both_groups_with_the_role_in_each(mock_page):
    open_as(mock_page, "both")

    expect(switcher(mock_page).locator("option")).to_have_text([OWN, EWAS])
    expect(switcher(mock_page)).to_have_value("3")


def test_switching_changes_the_navigation_and_the_start(mock_page):
    open_as(mock_page, "both")
    expect(h1(mock_page)).to_have_text("Cześć, Julia")
    assert nav_names(mock_page) == ["Start", "Mój dzień", "Zadania", "Grupa", "Pomoc"]

    switcher(mock_page).select_option(label=EWAS)

    expect(mock_page.get_by_text("Bliska osoba", exact=True).first).to_be_visible()
    assert nav_names(mock_page) == ["Start", "Pytania", "Zadania", "Grupa", "Pomoc"]
    expect(mock_page.get_by_role("link", name="Pytania")).to_be_visible()

    switcher(mock_page).select_option(label=OWN)

    assert nav_names(mock_page) == ["Start", "Mój dzień", "Zadania", "Grupa", "Pomoc"]
    expect(mock_page.get_by_text("Mama", exact=True).first).to_be_visible()


def test_the_selected_group_is_remembered_in_this_browser(mock_page):
    open_as(mock_page, "both")
    switcher(mock_page).select_option(label=EWAS)
    expect(mock_page.get_by_role("link", name="Pytania")).to_be_visible()

    mock_page.reload()

    expect(switcher(mock_page)).to_have_value("4")
    expect(mock_page.get_by_role("link", name="Pytania")).to_be_visible()


def test_a_remembered_group_the_person_left_is_not_used(mock_page):
    open_as(mock_page, "both")
    switcher(mock_page).select_option(label=EWAS)
    change_mock_state(
        mock_page,
        """const julia = s.people.find((p) => p.id === 103);
        julia.memberships = julia.memberships.filter((m) => m.group_id !== 4);""",
    )

    mock_page.reload()

    expect(h1(mock_page)).to_have_text("Cześć, Julia")
    expect(switcher(mock_page)).to_have_count(0)
    expect(mock_page.get_by_role("link", name="Mój dzień")).to_be_visible()


def test_the_group_travels_in_the_header_of_group_calls_only(mock_page):
    memberships = {
        "items": [
            {"group_id": 1, "role": "woman", "group_status": "active", "woman_name": "Anna"},
            {"group_id": 2, "role": "supporter", "group_status": "active", "woman_name": "Ewa"},
        ]
    }
    seen = []

    def example(name):
        return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))

    def answer(route):
        request = route.request
        path = urlparse(request.url).path
        group = request.headers.get("x-group-id")
        seen.append((path, group))
        second = group == "2"
        me = example("get_me.200.supporter.json" if second else "get_me.200.json")
        me["membership"]["group_id"] = 2 if second else 1
        bodies = {
            "/api/v1/me": me,
            "/api/v1/me/memberships": memberships,
            "/api/v1/summary": example(
                "get_summary.200.supporter.json" if second else "get_summary.200.json"
            ),
            "/api/v1/tasks": example("list_tasks.200.json"),
            "/api/v1/members": example("list_members.200.json"),
            "/api/v1/self-care": example("list_self_care.200.json"),
        }
        if path in bodies:
            route.fulfill(status=200, json=bodies[path])
        else:
            route.fulfill(status=404, json={"error": {"code": "not_found", "message": "Brak."}})

    mock_page.route("**/api/v1/**", answer)
    mock_page.goto(f"{mock_page.base}?mock=0#/")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    switcher(mock_page).select_option(label="Grupa: Ewa · Bliska osoba")
    expect(mock_page.get_by_role("link", name="Pytania")).to_be_visible()
    # The start of the other group is on screen once its role shows above the heading.
    expect(mock_page.locator(".page-head__eyebrow")).to_have_text("Bliska osoba")

    after = seen[seen.index(("/api/v1/me/memberships", None)) :]
    switched = [call for call in after if call[0] in ("/api/v1/tasks", "/api/v1/summary")]
    assert switched[-2:] and all(group == "2" for _, group in switched[-2:]), seen
    assert all(group is None for path, group in seen if path == "/api/v1/me/memberships")


# Invitations with other groups


def test_a_mother_accepts_a_supporter_invitation_and_gets_both_groups(mock_page):
    open_as(mock_page, "woman")
    invite_to_julias_group(mock_page)

    mock_page.goto(f"{mock_page.base}?mock=1#/invite/julia-token-1")
    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(switcher(mock_page).locator("option")).to_have_text([OWN, JULIAS])
    expect(switcher(mock_page)).to_have_value("3")
    assert nav_names(mock_page) == ["Start", "Pytania", "Zadania", "Grupa", "Pomoc"]


def test_accepting_the_invitation_of_a_group_one_is_in_keeps_the_screen_and_says_why(mock_page):
    open_as(mock_page, "partner", "/invite/k3p9x2vb7qd4")

    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(mock_page.get_by_role("alert")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Przyjmij zaproszenie")).to_be_visible()


def test_a_mother_cannot_accept_a_second_mother_invitation(mock_page):
    open_as(mock_page, "woman")
    invite_to_julias_group(mock_page, "woman")

    mock_page.goto(f"{mock_page.base}?mock=1#/invite/julia-token-1")
    mock_page.get_by_role("button", name="Przyjmij zaproszenie").click()

    expect(mock_page.get_by_role("alert")).to_be_visible()
    expect(switcher(mock_page)).to_have_count(0)


# Leaving


def test_a_supporter_leaves_one_group_and_the_other_is_shown(mock_page):
    open_as(mock_page, "both")
    switcher(mock_page).select_option(label=EWAS)
    nav(mock_page).get_by_role("link", name="Grupa").click()

    mock_page.get_by_role("button", name="Opuść grupę").click()
    dialog = mock_page.get_by_role("dialog", name="Opuścić grupę?")
    dialog.get_by_role("button", name="Opuść grupę").click()

    expect(h1(mock_page)).to_have_text("Cześć, Julia")
    expect(switcher(mock_page)).to_have_count(0)
    expect(mock_page.get_by_role("link", name="Mój dzień")).to_be_visible()


def test_leaving_the_last_group_shows_the_panel(mock_page):
    open_as(mock_page, "supporter", "/group")

    mock_page.get_by_role("button", name="Opuść grupę").click()
    mock_page.get_by_role("dialog").get_by_role("button", name="Opuść grupę").click()

    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()
    assert nav_names(mock_page) == ["Start", "Pomoc"]


def test_canceling_keeps_the_group(mock_page):
    open_as(mock_page, "supporter", "/group")

    mock_page.get_by_role("button", name="Opuść grupę").click()
    mock_page.get_by_role("dialog").get_by_role("button", name="Anuluj").click()

    expect(h1(mock_page)).to_have_text("Grupa")


def test_the_mother_of_an_active_group_has_no_leave_control(mock_page):
    open_as(mock_page, "woman", "/group")

    expect(h1(mock_page)).to_have_text("Twoja grupa")
    expect(mock_page.get_by_role("button", name="Opuść grupę")).to_have_count(0)


# Issued invitations


def test_the_mother_sees_the_issued_invitation_and_revokes_it(mock_page):
    open_as(mock_page, "woman", "/group")

    issued = mock_page.get_by_role("region", name="Wysłane zaproszenia")
    expect(issued.get_by_role("listitem")).to_have_count(1)
    expect(issued).to_contain_text("Partner")
    expect(issued).to_contain_text("Ważne do")

    issued.get_by_role("button", name="Cofnij zaproszenie: Partner").click()

    expect(issued.get_by_text("Żadne zaproszenie nie czeka na przyjęcie.")).to_be_visible()
    mock_page.goto(f"{mock_page.base}?mock=1#/invite/k3p9x2vb7qd4")
    expect(h1(mock_page)).to_have_text("Ten link już nie działa")


def test_a_new_invitation_appears_in_the_list(mock_page):
    open_as(mock_page, "woman", "/group")

    mock_page.get_by_role("button", name="Utwórz link zaproszenia").click()

    issued = mock_page.get_by_role("region", name="Wysłane zaproszenia")
    expect(issued.get_by_role("listitem")).to_have_count(2)


def test_a_supporter_sees_no_invitation_list(mock_page):
    open_as(mock_page, "supporter", "/group")

    expect(h1(mock_page)).to_have_text("Grupa")
    expect(mock_page.get_by_role("region", name="Wysłane zaproszenia")).to_have_count(0)


def test_the_partner_of_a_pending_group_sees_the_list(mock_page):
    open_as(mock_page, "pending", "/group")

    expect(mock_page.get_by_role("region", name="Wysłane zaproszenia")).to_be_visible()
    assert re.search("Zaproś mamę", mock_page.locator("main").inner_text())
