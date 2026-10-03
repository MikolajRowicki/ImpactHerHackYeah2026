from playwright.sync_api import expect

NOTICE = "Tryb demonstracyjny"


def test_mock_call_shows_example_data_and_sends_no_api_request(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")

    expect(mock_page.get_by_text("Zalogowano jako Anna.")).to_be_visible()
    expect(mock_page.get_by_text("Rola: mama")).to_be_visible()
    assert mock_page.api_requests == []


def test_mock_variant_shows_another_role(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1&variant=partner")

    expect(mock_page.get_by_text("Zalogowano jako Piotr.")).to_be_visible()
    expect(mock_page.get_by_text("Rola: partner lub partnerka")).to_be_visible()


def test_mock_mode_is_remembered_until_it_is_turned_off(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")
    expect(mock_page.get_by_text("Zalogowano jako Anna.")).to_be_visible()

    mock_page.goto(f"{mock_page.base}#/inna-strona")
    expect(mock_page.get_by_role("heading", name="Nie ma takiej strony")).to_be_visible()
    expect(mock_page.get_by_role("status")).to_contain_text(NOTICE)

    mock_page.goto(f"{mock_page.base}#/")
    expect(mock_page.get_by_text("Zalogowano jako Anna.")).to_be_visible()

    mock_page.goto(f"{mock_page.base}?mock=0#/")
    expect(mock_page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()
    expect(mock_page.get_by_text(NOTICE)).to_have_count(0)


def test_notice_is_visible_on_every_screen(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")
    expect(mock_page.get_by_role("status")).to_contain_text(NOTICE)

    mock_page.goto(f"{mock_page.base}#/inna-strona")
    expect(mock_page.get_by_role("heading", name="Nie ma takiej strony")).to_be_visible()
    expect(mock_page.get_by_role("status")).to_contain_text(NOTICE)


def test_without_mock_the_page_calls_the_api_and_shows_no_notice(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=0")

    # A plain static server has no API, so the live call fails and the page says so.
    expect(mock_page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()
    expect(mock_page.get_by_text(NOTICE)).to_have_count(0)
    assert any(url.endswith("/api/v1/me") for url in mock_page.api_requests)


def test_a_route_named_like_an_object_property_is_not_found(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1#constructor")

    expect(mock_page.get_by_role("heading", name="Nie ma takiej strony")).to_be_visible()
