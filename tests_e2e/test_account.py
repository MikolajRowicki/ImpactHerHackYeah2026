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


def sign_up(page, name, email, password="dlugie-haslo"):
    page.get_by_role("link", name="Załóż konto").click()
    expect(h1(page)).to_have_text("Załóż konto")
    page.get_by_label("Jak mamy się do Ciebie zwracać?").fill(name)
    page.get_by_label("Adres e-mail").fill(email)
    page.get_by_label("Hasło").fill(password)
    page.get_by_role("button", name="Załóż konto").click()


def test_successful_registration_confirms_the_email_then_leads_to_a_group(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)

    sign_up(mock_page, "Ola", "ola@example.com")
    expect(h1(mock_page)).to_have_text("Sprawdź skrzynkę")
    expect(mock_page.get_by_text("Jeśli adres jest poprawny, dostaniesz wiadomość")).to_be_visible()
    mock_page.get_by_role("link", name="Demo: otwórz link z wiadomości").click()
    expect(h1(mock_page)).to_have_text("Konto jest aktywne")
    mock_page.get_by_role("link", name="Zaloguj się").last.click()
    sign_in(mock_page, "ola@example.com", "dlugie-haslo")

    expect(h1(mock_page)).to_have_text("Cześć, Ola")
    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()
    for choice in ("Jestem mamą", "Jestem Partnerem", "Poczekam na link od mamy"):
        expect(mock_page.get_by_role("button", name=choice)).to_be_visible()


def test_sign_in_before_activation_offers_a_new_link(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)
    sign_up(mock_page, "Ola", "ola@example.com")
    expect(h1(mock_page)).to_have_text("Sprawdź skrzynkę")
    mock_page.get_by_role("link", name="Zaloguj się").last.click()

    sign_in(mock_page, "ola@example.com", "dlugie-haslo")

    expect(mock_page.get_by_role("alert")).to_have_text("Nieprawidłowy e-mail lub hasło.")
    mock_page.get_by_role("button", name="Wyślij link aktywacyjny jeszcze raz").click()
    expect(mock_page.get_by_text("Jeśli adres jest poprawny i konto czeka")).to_be_visible()


def test_used_activation_link_says_it_no_longer_works(mock_page):
    open_as(mock_page, "woman", "/activate/nieznany-kod")

    expect(h1(mock_page)).to_have_text("Ten link już nie działa")
    expect(mock_page.get_by_text("Ten link jest nieprawidłowy albo wygasł.")).to_be_visible()
    expect(
        mock_page.get_by_role("button", name="Wyślij link aktywacyjny jeszcze raz")
    ).to_be_visible()


def test_forgot_password_then_reset_and_sign_in_with_the_new_one(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)
    mock_page.get_by_role("link", name="Nie pamiętasz hasła?").click()
    expect(h1(mock_page)).to_have_text("Nowe hasło")

    mock_page.get_by_label("Adres e-mail").fill("anna@example.com")
    mock_page.get_by_role("button", name="Wyślij link").click()
    expect(mock_page.get_by_text("Jeśli adres jest poprawny, dostaniesz wiadomość")).to_be_visible()
    mock_page.get_by_role("link", name="Demo: otwórz link z wiadomości").click()
    expect(h1(mock_page)).to_have_text("Ustaw nowe hasło")
    mock_page.get_by_label("Nowe hasło").fill("krotkie")
    mock_page.get_by_role("button", name="Zapisz nowe hasło").click()
    expect(mock_page.get_by_text("Hasło musi mieć co najmniej 8 znaków.")).to_be_visible()
    mock_page.get_by_label("Nowe hasło").fill("nowe-haslo-456")
    mock_page.get_by_role("button", name="Zapisz nowe hasło").click()
    expect(h1(mock_page)).to_have_text("Hasło jest zmienione")
    mock_page.get_by_role("link", name="Zaloguj się").last.click()

    sign_in(mock_page, "anna@example.com", "nowe-haslo-456")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")


def test_forgot_password_answer_is_the_same_for_an_unknown_address(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)
    mock_page.goto(f"{mock_page.base}#/forgot")
    expect(h1(mock_page)).to_have_text("Nowe hasło")

    mock_page.get_by_label("Adres e-mail").fill("nikt@example.com")
    mock_page.get_by_role("button", name="Wyślij link").click()

    expect(mock_page.get_by_text("Jeśli adres jest poprawny, dostaniesz wiadomość")).to_be_visible()


def test_invalid_reset_link_offers_a_new_one(mock_page):
    open_as(mock_page, "woman", "/reset/nieznany-kod")
    mock_page.get_by_label("Nowe hasło").fill("nowe-haslo-456")
    mock_page.get_by_role("button", name="Zapisz nowe hasło").click()

    expect(mock_page.get_by_role("alert")).to_contain_text("Ten link jest nieprawidłowy")
    mock_page.get_by_role("link", name="Poproś o nowy link").click()
    expect(h1(mock_page)).to_have_text("Nowe hasło")


def test_change_password_checks_the_current_one(mock_page):
    open_as(mock_page, "woman")
    mock_page.get_by_role("link", name="Moje konto").click()
    expect(h1(mock_page)).to_have_text("Moje konto")

    mock_page.get_by_label("Obecne hasło").fill("zle-haslo")
    mock_page.get_by_label("Nowe hasło").fill("nowe-haslo-456")
    mock_page.get_by_role("button", name="Zmień hasło").click()
    expect(mock_page.get_by_text("Obecne hasło jest nieprawidłowe.")).to_be_visible()

    mock_page.get_by_label("Obecne hasło").fill(PASSWORD)
    mock_page.get_by_role("button", name="Zmień hasło").click()
    expect(mock_page.get_by_text("Hasło jest zmienione.")).to_be_visible()


def test_short_password_is_explained_and_nothing_is_sent(mock_page):
    calls = []
    live_signed_out(mock_page, calls)

    mock_page.get_by_label("Jak mamy się do Ciebie zwracać?").fill("Ola")
    mock_page.get_by_label("Adres e-mail").fill("ola@example.com")
    mock_page.get_by_label("Hasło").fill("krotkie")
    mock_page.get_by_role("button", name="Załóż konto").click()

    expect(mock_page.get_by_text("Hasło musi mieć co najmniej 8 znaków.")).to_be_visible()
    expect(mock_page.get_by_label("Hasło")).to_have_attribute("aria-invalid", "true")
    assert not any(url.endswith("/auth/signup") for url in calls)


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
    mock_page.route("**/api/v1/auth/signup", lambda route: route.fulfill(status=422, json=body))

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


def test_existing_email_gets_the_same_answer_as_a_new_one(mock_page):
    open_as(mock_page, "woman")
    sign_out(mock_page)

    sign_up(mock_page, "Anna", "anna@example.com")

    expect(h1(mock_page)).to_have_text("Sprawdź skrzynkę")
    expect(mock_page.get_by_text("już istnieje")).to_have_count(0)


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

    def current(route):
        # Like a real backend: signed in once the login was accepted.
        if sent:
            route.fulfill(status=200, json=me)
        else:
            route.fulfill(status=401, json=UNAUTHORIZED)

    calls = []
    live_signed_out(mock_page, calls)
    mock_page.route("**/api/v1/auth/login", login)
    mock_page.route("**/api/v1/me", current)
    mock_page.route(
        "**/api/v1/me/memberships", lambda route: route.fulfill(status=200, json={"items": []})
    )
    mock_page.get_by_role("link", name="Zaloguj się").last.click()
    sign_in(mock_page, "anna@example.com")

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    assert sent == [{"email": "anna@example.com", "password": PASSWORD}]


# Deleting the account


def delete_dialog(page):
    page.get_by_role("button", name="Usuń konto").click()
    return page.get_by_role("dialog", name="Usunąć konto?")


def test_the_mother_is_warned_that_her_group_goes_too(mock_page):
    open_as(mock_page, "woman", "/account")

    dialog = delete_dialog(mock_page)

    expect(dialog).to_contain_text("usuniemy też całą grupę razem z jej danymi")


def test_a_supporter_gets_no_group_warning(mock_page):
    open_as(mock_page, "supporter", "/account")

    dialog = delete_dialog(mock_page)

    expect(dialog).to_contain_text("Tego nie da się cofnąć.")
    expect(dialog).not_to_contain_text("całą grupę")


def test_canceling_keeps_the_account(mock_page):
    open_as(mock_page, "supporter", "/account")

    delete_dialog(mock_page).get_by_role("button", name="Anuluj").click()

    expect(h1(mock_page)).to_have_text("Moje konto")
    nav(mock_page).get_by_role("link", name="Start").click()
    expect(h1(mock_page)).to_have_text("Cześć, Marta")


def test_deleting_signs_the_person_out_and_the_account_is_gone(mock_page):
    open_as(mock_page, "supporter", "/account")

    delete_dialog(mock_page).get_by_role("button", name="Usuń konto").click()

    expect(mock_page.get_by_role("button", name="Wyloguj")).to_have_count(0)
    expect(mock_page.get_by_role("link", name="Zaloguj się").first).to_be_visible()
    mock_page.goto(f"{mock_page.base}?mock=1#/login")
    sign_in(mock_page, "marta@example.com", "tajne-haslo-123")
    expect(mock_page.get_by_role("alert")).to_have_text("Nieprawidłowy e-mail lub hasło.")


def test_a_deleted_mothers_group_is_gone_for_the_others(mock_page):
    open_as(mock_page, "woman", "/account")
    delete_dialog(mock_page).get_by_role("button", name="Usuń konto").click()
    expect(mock_page.get_by_role("button", name="Wyloguj")).to_have_count(0)

    open_as(mock_page, "supporter")

    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()
