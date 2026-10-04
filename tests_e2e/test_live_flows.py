"""Behaviour against a real backend's answers, routed, where the mock cannot show the problem."""

import json
from pathlib import Path

from playwright.sync_api import expect

from .helpers import h1, live, nav

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"


def example(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def ok(name):
    return (200, example(name))


def me_with(group_status=None, role="partner", account_id=2, name="Piotr"):
    membership = (
        {"group_id": 1, "role": role, "group_status": group_status} if group_status else None
    )
    return {
        "id": account_id,
        "email": "piotr@example.com",
        "display_name": name,
        "membership": membership,
    }


def test_start_notices_that_the_mother_accepted_meanwhile(mock_page):
    answers = {
        "GET /api/v1/me": (200, me_with("pending")),
        "GET /api/v1/summary": ok("get_summary.200.partner.json"),
        "GET /api/v1/tasks": ok("list_tasks.200.json"),
    }
    live(mock_page, answers)
    expect(h1(mock_page)).to_have_text("Czekamy na mamę")

    # Anna accepts the invitation on her phone.
    answers["GET /api/v1/me"] = (200, me_with("active"))
    nav(mock_page).get_by_role("link", name="Start").click()

    expect(h1(mock_page)).to_have_text("Cześć, Piotr")
    expect(nav(mock_page).get_by_role("link", name="Pytania")).to_be_visible()


def test_try_again_reads_the_session_again_after_being_removed(mock_page):
    answers = {
        "GET /api/v1/me": (200, me_with("active")),
        "GET /api/v1/tasks": (403, example("list_tasks.403.json")),
    }
    live(mock_page, answers, "/tasks")
    expect(mock_page.get_by_text("Nie należysz do żadnej grupy.")).to_be_visible()

    answers["GET /api/v1/me"] = (200, me_with(None))
    mock_page.get_by_role("button", name="Spróbuj ponownie").click()

    expect(h1(mock_page)).to_have_text("To miejsce jest dla kogoś innego")
    names = nav(mock_page).get_by_role("link").all_inner_texts()
    assert "Zadania" not in names


def test_done_control_follows_the_account_id_not_the_membership_id(mock_page):
    # Membership ids (7, 8) differ from account ids (12, 13) on purpose.
    task = {
        "id": 40,
        "title": "Zrobić zakupy",
        "details": None,
        "status": "claimed",
        "created_by": {"id": 13, "display_name": "Marta"},
        "claimed_by": {"id": 12, "display_name": "Piotr"},
        "created_at": "2026-10-03T10:00:00Z",
        "completed_at": None,
    }
    members = {
        "items": [
            {
                "id": 7,
                "display_name": "Piotr",
                "role": "partner",
                "joined_at": "2026-10-03T09:00:00Z",
            },
            {
                "id": 8,
                "display_name": "Marta",
                "role": "supporter",
                "joined_at": "2026-10-03T09:00:00Z",
            },
        ]
    }
    answers = {
        "GET /api/v1/me": (200, me_with("active", account_id=12)),
        "GET /api/v1/tasks": (200, {"items": [task]}),
        "GET /api/v1/members": (200, members),
    }
    live(mock_page, answers, "/tasks")

    item = mock_page.get_by_role("region", name="W toku").get_by_role("listitem")
    expect(item).to_contain_text("Zajmuje się: Ty")
    expect(item).to_contain_text("Dodane przez: Marta")
    expect(item.get_by_role("button", name="Oznacz jako zrobione")).to_be_visible()


def test_missing_title_sends_nothing(mock_page):
    answers = {
        "GET /api/v1/me": (200, me_with("active")),
        "GET /api/v1/tasks": ok("list_tasks.200.json"),
    }
    calls = live(mock_page, answers, "/tasks")
    expect(h1(mock_page)).to_have_text("Zadania")

    mock_page.get_by_role("button", name="Dodaj zadanie").click()

    expect(mock_page.get_by_text("Wpisz krótki tytuł zadania.")).to_be_visible()
    assert "POST /api/v1/tasks" not in calls


def test_missing_check_in_choice_sends_nothing(mock_page):
    answers = {
        "GET /api/v1/me": ok("get_me.200.json"),
        "GET /api/v1/check-ins": ok("list_check_ins.200.json"),
    }
    calls = live(mock_page, answers, "/check-in")
    expect(h1(mock_page)).to_have_text("Mój dzień")

    mock_page.get_by_role("group", name="Jak się dziś czujesz?").get_by_label("Dobrze").check()
    mock_page.get_by_role("button", name="Zapisz wpis").click()

    sleep = mock_page.get_by_role("group", name="Jak Ci się spało?")
    expect(sleep.get_by_text("Wybierz jedną z odpowiedzi.")).to_be_visible()
    assert "POST /api/v1/check-ins" not in calls


def test_signing_in_from_the_navigation_still_returns_to_the_invitation(mock_page):
    answers = {
        "GET /api/v1/me": (401, example("get_me.401.json")),
        "GET /api/v1/invitations/k3p9x2vb7qd4": ok("get_invitation.200.json"),
        "POST /api/v1/auth/login": (200, me_with(None)),
    }
    live(mock_page, answers, "/invite/k3p9x2vb7qd4")
    expect(h1(mock_page)).to_have_text("Anna zaprasza Cię do grupy")

    nav(mock_page).get_by_role("link", name="Zaloguj się").click()
    expect(h1(mock_page)).to_have_text("Zaloguj się")
    mock_page.get_by_label("Adres e-mail").fill("piotr@example.com")
    mock_page.get_by_label("Hasło").fill("tajne-haslo-123")
    answers["GET /api/v1/me"] = (200, me_with(None))
    mock_page.get_by_role("button", name="Zaloguj się").click()

    expect(h1(mock_page)).to_have_text("Anna zaprasza Cię do grupy")
    expect(mock_page.get_by_role("button", name="Przyjmij zaproszenie")).to_be_visible()


def test_first_sign_in_after_a_redirect_lands_on_starting_a_group(mock_page):
    answers = {
        "GET /api/v1/me": (401, example("get_me.401.json")),
        "POST /api/v1/auth/login": (200, me_with(None, name="Ola")),
    }
    live(mock_page, answers, "/tasks")
    expect(h1(mock_page)).to_have_text("Zaloguj się")

    mock_page.get_by_label("Adres e-mail").fill("ola@example.com")
    mock_page.get_by_label("Hasło").fill("dlugie-haslo")
    answers["GET /api/v1/me"] = (200, me_with(None, name="Ola"))
    mock_page.get_by_role("button", name="Zaloguj się").click()

    expect(h1(mock_page)).to_have_text("Cześć, Ola")
    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()


def test_signup_sends_the_form_and_opens_no_session(mock_page):
    answers = {
        "GET /api/v1/me": (401, example("get_me.401.json")),
        "POST /api/v1/auth/signup": (202, example("signup.202.json")),
    }
    calls = live(mock_page, answers, "/register")
    expect(h1(mock_page)).to_have_text("Załóż konto")

    mock_page.get_by_label("Jak mamy się do Ciebie zwracać?").fill("Ola")
    mock_page.get_by_label("Adres e-mail").fill("ola@example.com")
    mock_page.get_by_label("Hasło").fill("dlugie-haslo")
    mock_page.get_by_role("button", name="Załóż konto").click()

    expect(h1(mock_page)).to_have_text("Sprawdź skrzynkę")
    assert "POST /api/v1/auth/signup" in calls
    assert "POST /api/v1/auth/register" not in calls
