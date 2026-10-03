from playwright.sync_api import expect

from .helpers import h1, open_as

NOTICE = "Tryb demonstracyjny"


def notice(page):
    return page.get_by_role("region", name=NOTICE)


def test_mock_call_shows_example_data_and_sends_no_api_request(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    expect(mock_page.get_by_text("Mama", exact=True)).to_be_visible()
    assert mock_page.api_requests == []


def test_mock_variant_shows_another_role(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1&variant=partner")

    expect(h1(mock_page)).to_have_text("Cześć, Piotr")
    expect(mock_page.get_by_text("Partner lub partnerka", exact=True)).to_be_visible()


def test_mock_mode_is_remembered_until_it_is_turned_off(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    mock_page.goto(f"{mock_page.base}#/inna-strona")
    expect(h1(mock_page)).to_have_text("Nie ma takiej strony")
    expect(notice(mock_page)).to_contain_text(NOTICE)

    mock_page.goto(f"{mock_page.base}#/")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    mock_page.goto(f"{mock_page.base}?mock=0#/")
    expect(mock_page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()
    expect(mock_page.get_by_text(NOTICE)).to_have_count(0)


def test_notice_is_visible_on_every_screen(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")
    expect(notice(mock_page)).to_contain_text(NOTICE)

    mock_page.goto(f"{mock_page.base}#/inna-strona")
    expect(h1(mock_page)).to_have_text("Nie ma takiej strony")
    expect(notice(mock_page)).to_contain_text(NOTICE)


def test_without_mock_the_page_calls_the_api_and_shows_no_notice(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=0")

    # A plain static server has no API, so the live call fails and the page says so.
    expect(mock_page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()
    expect(mock_page.get_by_text(NOTICE)).to_have_count(0)
    assert any(url.endswith("/api/v1/me") for url in mock_page.api_requests)


def test_a_route_named_like_an_object_property_is_not_found(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1#constructor")

    expect(h1(mock_page)).to_have_text("Nie ma takiej strony")


def test_switch_to_partner_shows_his_start_with_his_summary(mock_page):
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    notice(mock_page).get_by_label("Pokaż jako").select_option(label="Partner (Piotr)")

    expect(h1(mock_page)).to_have_text("Cześć, Piotr")
    expect(
        mock_page.get_by_text("Z odpowiedzi bliskich wynika, że ostatnio jest jej trudniej")
    ).to_be_visible()
    assert mock_page.api_requests == []


def test_every_perspective_can_be_picked(mock_page):
    open_as(mock_page, "woman")
    picker = notice(mock_page).get_by_label("Pokaż jako")
    for label, heading in (
        ("Bliska osoba (Marta)", "Cześć, Marta"),
        ("Osoba bez grupy", "Cześć, Anna"),
        ("Grupa czeka na mamę", "Czekamy na mamę"),
        ("Mama (Anna)", "Cześć, Anna"),
    ):
        picker.select_option(label=label)
        expect(h1(mock_page)).to_have_text(heading)


def test_no_perspective_switch_in_live_mode(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=0")
    expect(mock_page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()

    expect(mock_page.get_by_label("Pokaż jako")).to_have_count(0)
    expect(mock_page.get_by_role("button", name="Zacznij demo od nowa")).to_have_count(0)


def test_demo_changes_survive_a_reload(mock_page):
    open_as(mock_page, "woman")
    mock_page.get_by_role("button", name="Wyloguj").click()
    expect(h1(mock_page)).to_have_text("Zaloguj się")

    mock_page.reload()

    expect(h1(mock_page)).to_have_text("Zaloguj się")
    expect(notice(mock_page).get_by_label("Pokaż jako")).to_have_value("")
    assert mock_page.api_requests == []


def test_reset_brings_back_the_contract_examples(mock_page):
    open_as(mock_page, "woman")
    mock_page.get_by_role("button", name="Wyloguj").click()
    expect(h1(mock_page)).to_have_text("Zaloguj się")

    notice(mock_page).get_by_role("button", name="Zacznij demo od nowa").click()

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    expect(
        mock_page.get_by_text("W ostatnich dniach było trochę trudniej niż zwykle.")
    ).to_be_visible()


def test_turning_mock_off_clears_the_demo_state(mock_page):
    open_as(mock_page, "woman")
    mock_page.get_by_role("button", name="Wyloguj").click()
    expect(h1(mock_page)).to_have_text("Zaloguj się")

    mock_page.goto(f"{mock_page.base}?mock=0#/help")
    expect(h1(mock_page)).to_have_text("Pomoc")
    mock_page.goto(f"{mock_page.base}?mock=1#/")

    expect(h1(mock_page)).to_have_text("Cześć, Anna")
