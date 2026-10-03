import json

from playwright.sync_api import expect

from .helpers import h1, nav, open_as

PASSWORD = "tajne-haslo-123"
UNAUTHORIZED = {"error": {"code": "unauthorized", "message": "Zaloguj się, aby kontynuować."}}


def sign_out(page):
    page.get_by_role("button", name="Wyloguj").click()
    expect(h1(page)).to_have_text("Zaloguj się")


def sign_in(page, email, password=PASSWORD):
    # Registration has the same field labels, so wait until the sign-in screen is shown.
    expect(h1(page)).to_have_text("Zaloguj się")
    page.get_by_label("Adres e-mail").fill(email)
    page.get_by_label("Hasło").fill(password)
    page.get_by_role("button", name="Zaloguj się").click()


def live_signed_out(page, calls):
    """Live mode against routed answers: nobody is signed in, every other call is recorded."""

    def answer(route):
        calls.append(route.request.url)
        if route.request.url.endswith("/api/v1/me"):
            route.fulfill(status=401, json=UNAUTHORIZED)
        else:
            route.fallback()

    page.route("**/api/v1/**", answer)
    page.goto(f"{page.base}?mock=0#/register")
    expect(h1(page)).to_have_text("Załóż konto")


def test_successful_sign_in_shows_the_start_with_the_name(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)

    sign_in(mock_page, "piotr@example.com")

    expect(h1(mock_page)).to_have_text("Cześć, Piotr")


def test_wrong_credentials_show_the_message_and_keep_the_email(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)

    sign_in(mock_page, "anna@example.com", "zle-haslo-000")

    expect(mock_page.get_by_role("alert")).to_have_text("Nieprawidłowy e-mail lub hasło.")
    expect(mock_page.get_by_label("Adres e-mail")).to_have_value("anna@example.com")
    expect(h1(mock_page)).to_have_text("Zaloguj się")


def test_empty_sign_in_asks_for_the_fields(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)

    mock_page.get_by_role("button", name="Zaloguj się").click()

    expect(mock_page.get_by_text("Wpisz adres e-mail.")).to_be_visible()
    expect(mock_page.get_by_text("Wpisz hasło.")).to_be_visible()


def test_successful_registration_leads_to_starting_or_joining_a_group(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)
    mock_page.get_by_role("link", name="Załóż konto").click()

    mock_page.get_by_label("Jak mamy się do Ciebie zwracać?").fill("Ola")
    mock_page.get_by_label("Adres e-mail").fill("ola@example.com")
    mock_page.get_by_label("Hasło").fill("dlugie-haslo")
    mock_page.get_by_role("button", name="Załóż konto").click()

    expect(h1(mock_page)).to_have_text("Cześć, Ola")
    expect(mock_page.get_by_role("heading", name="Załóż grupę")).to_be_visible()
    expect(mock_page.get_by_role("heading", name="Masz zaproszenie?")).to_be_visible()


def test_short_password_is_explained_and_nothing_is_sent(mock_page):
    calls = []
    live_signed_out(mock_page, calls)

    mock_page.get_by_label("Jak mamy się do Ciebie zwracać?").fill("Ola")
    mock_page.get_by_label("Adres e-mail").fill("ola@example.com")
    mock_page.get_by_label("Hasło").fill("krotkie")
    mock_page.get_by_role("button", name="Załóż konto").click()

    expect(mock_page.get_by_text("Hasło musi mieć co najmniej 8 znaków.")).to_be_visible()
    expect(mock_page.get_by_label("Hasło")).to_have_attribute("aria-invalid", "true")
    assert not any(url.endswith("/auth/register") for url in calls)


def test_server_field_errors_are_shown_next_to_their_fields(mock_page):
    calls = []
    live_signed_out(mock_page, calls)
    body = {
        "error": {
            "code": "validation_error",
            "message": "Popraw zaznaczone pola.",
            "fields": {
                "email": "Konto z tym adresem e-mail już istnieje.",
                "display_name": "To imię jest za długie.",
            },
        }
    }
    mock_page.route("**/api/v1/auth/register", lambda route: route.fulfill(status=422, json=body))

    mock_page.get_by_label("Jak mamy się do Ciebie zwracać?").fill("Ola")
    mock_page.get_by_label("Adres e-mail").fill("anna@example.com")
    mock_page.get_by_label("Hasło").fill("dlugie-haslo")
    mock_page.get_by_role("button", name="Załóż konto").click()

    email = mock_page.get_by_label("Adres e-mail")
    expect(email).to_have_attribute("aria-invalid", "true")
    expect(email).to_have_accessible_description("Konto z tym adresem e-mail już istnieje.")
    name = mock_page.get_by_label("Jak mamy się do Ciebie zwracać?")
    expect(name).to_have_attribute("aria-invalid", "true")
    expect(mock_page.get_by_text("To imię jest za długie.")).to_be_visible()


def test_existing_email_in_the_demo_is_refused_next_to_the_field(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)
    mock_page.get_by_role("link", name="Załóż konto").click()

    mock_page.get_by_label("Jak mamy się do Ciebie zwracać?").fill("Anna")
    mock_page.get_by_label("Adres e-mail").fill("anna@example.com")
    mock_page.get_by_label("Hasło").fill("dlugie-haslo")
    mock_page.get_by_role("button", name="Załóż konto").click()

    expect(mock_page.get_by_text("Konto z tym adresem e-mail już istnieje.")).to_be_visible()


def test_sign_out_shows_sign_in_without_group_sections(mock_page):
    open_as(mock_page, "woman")
    expect(nav(mock_page).get_by_role("link", name="Zadania")).to_be_visible()

    sign_out(mock_page)

    names = nav(mock_page).get_by_role("link").all_inner_texts()
    assert "Zadania" not in names
    assert "Grupa" not in names
    assert "Mój dzień" not in names
    expect(mock_page.get_by_role("button", name="Wyloguj")).to_be_hidden()


def test_invitation_link_while_signed_out_returns_after_sign_in(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)
    mock_page.goto(f"{mock_page.base}#/invite/k3p9x2vb7qd4")
    expect(h1(mock_page)).to_have_text("Anna zaprasza Cię do grupy")

    mock_page.get_by_role("link", name="Zaloguj się").last.click()
    sign_in(mock_page, "piotr@example.com")

    expect(h1(mock_page)).to_have_text("Anna zaprasza Cię do grupy")


def test_signed_out_person_returns_to_the_wanted_address(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)

    mock_page.goto(f"{mock_page.base}#/tasks")
    expect(h1(mock_page)).to_have_text("Zaloguj się")
    sign_in(mock_page, "anna@example.com")

    expect(nav(mock_page).get_by_role("link", name="Zadania")).to_have_attribute(
        "aria-current", "page"
    )


def test_live_sign_in_sends_the_form_and_shows_the_start(mock_page):
    me = json.loads(
        '{"id": 1, "email": "anna@example.com", "display_name": "Anna", "membership": null}'
    )
    sent = []

    def login(route):
        sent.append(route.request.post_data_json)
        route.fulfill(status=200, json=me)

    calls = []
    live_signed_out(mock_page, calls)
    mock_page.route("**/api/v1/auth/login", login)
    mock_page.get_by_role("link", name="Zaloguj się").last.click()
    sign_in(mock_page, "anna@example.com")

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    assert sent == [{"email": "anna@example.com", "password": PASSWORD}]
