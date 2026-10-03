import json
import re

from playwright.sync_api import expect

from .helpers import h1, nav, open_as

NOT_ALLOWED = "To miejsce jest dla kogoś innego"


def nav_names(page):
    expect(nav(page).get_by_role("link").first).to_be_visible()
    return nav(page).get_by_role("link").all_inner_texts()


def test_mother_navigation(mock_page):
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    assert nav_names(mock_page) == ["Start", "Mój dzień", "Zadania", "Grupa", "Pomoc"]


def test_loved_one_navigation(mock_page):
    for perspective, name in (("partner", "Piotr"), ("supporter", "Marta")):
        open_as(mock_page, perspective)
        expect(h1(mock_page)).to_have_text(f"Cześć, {name}")

        assert nav_names(mock_page) == ["Start", "Pytania", "Zadania", "Grupa", "Pomoc"]


def test_no_group_navigation_offers_no_data_sections(mock_page):
    open_as(mock_page, "no_group")
    expect(h1(mock_page)).to_contain_text("Anna")

    names = nav_names(mock_page)
    assert "Mój dzień" not in names
    assert "Pytania" not in names
    assert "Zadania" not in names


def test_current_place_is_marked(mock_page):
    open_as(mock_page, "woman")
    nav(mock_page).get_by_role("link", name="Zadania").click()

    expect(nav(mock_page).get_by_role("link", name="Zadania")).to_have_attribute(
        "aria-current", "page"
    )
    expect(nav(mock_page).get_by_role("link", name="Start")).not_to_have_attribute(
        "aria-current", "page"
    )


def test_focus_moves_to_the_new_heading_after_navigation(mock_page):
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    nav(mock_page).get_by_role("link", name="Pomoc").click()

    expect(h1(mock_page)).to_have_text("Pomoc")
    expect(h1(mock_page)).to_be_focused()


def test_loved_one_opening_the_check_in_gets_a_calm_explanation(mock_page):
    open_as(mock_page, "partner", "/check-in")

    expect(h1(mock_page)).to_have_text(NOT_ALLOWED)
    expect(mock_page.get_by_text("To miejsce należy do mamy.")).to_be_visible()
    mock_page.get_by_role("link", name="Wróć na start").click()
    expect(h1(mock_page)).to_have_text("Cześć, Piotr")


def test_mother_opening_the_questions_gets_a_calm_explanation(mock_page):
    open_as(mock_page, "woman", "/questions")

    expect(h1(mock_page)).to_have_text(NOT_ALLOWED)
    expect(mock_page.get_by_role("link", name="Wróć na start")).to_be_visible()


def test_pending_group_keeps_data_places_closed(mock_page):
    open_as(mock_page, "pending", "/tasks")

    expect(h1(mock_page)).to_have_text(NOT_ALLOWED)
    expect(
        mock_page.get_by_text("Grupa zacznie działać, gdy mama przyjmie zaproszenie.")
    ).to_be_visible()


def test_unknown_hash_shows_not_found_with_a_way_back(mock_page):
    open_as(mock_page, "woman", "/nie-ma-takiej")

    expect(h1(mock_page)).to_have_text("Nie ma takiej strony")
    mock_page.get_by_role("link", name="Wróć na początek").click()
    expect(h1(mock_page)).to_have_text("Cześć, Anna")


def test_help_is_reachable_from_any_screen_signed_in_or_not(mock_page):
    open_as(mock_page, "partner", "/tasks")
    nav(mock_page).get_by_role("link", name="Pomoc").click()
    expect(h1(mock_page)).to_have_text("Pomoc")

    mock_page.get_by_role("button", name="Wyloguj").click()
    expect(h1(mock_page)).to_have_text("Zaloguj się")
    nav(mock_page).get_by_role("link", name="Pomoc").click()
    expect(h1(mock_page)).to_have_text("Pomoc")


def test_help_place_shows_no_phone_number(mock_page):
    open_as(mock_page, "woman", "/help")
    expect(h1(mock_page)).to_have_text("Pomoc")
    expect(mock_page.get_by_text("Kontakty pojawią się wkrótce")).to_be_visible()

    text = mock_page.locator("main").inner_text()
    assert not re.search(r"\d{3}", text), text
    assert mock_page.locator("main a[href^='tel:']").count() == 0


def test_failed_call_shows_the_error_message_and_try_again_reloads(mock_page):
    answers = [
        (500, {"error": {"code": "server_error", "message": "Serwer chwilowo odpoczywa."}}),
        (401, {"error": {"code": "unauthorized", "message": "Zaloguj się, aby kontynuować."}}),
    ]

    def answer(route):
        status, body = answers[0]
        route.fulfill(status=status, content_type="application/json", body=json.dumps(body))

    mock_page.route("**/api/v1/me", answer)
    mock_page.goto(f"{mock_page.base}?mock=0#/")

    expect(mock_page.get_by_text("Serwer chwilowo odpoczywa.")).to_be_visible()
    answers.pop(0)
    mock_page.get_by_role("button", name="Spróbuj ponownie").click()

    expect(h1(mock_page)).to_have_text("Zaloguj się")


def test_failed_call_without_an_error_body_shows_a_general_message(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=0#/")

    expect(mock_page.get_by_text("Nie udało się wczytać danych.")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Spróbuj ponownie")).to_be_visible()


def test_every_screen_has_landmarks_and_one_main_heading(mock_page):
    for path in ("/", "/help", "/tasks", "/group", "/check-in", "/nie-ma"):
        open_as(mock_page, "woman", path)
        expect(h1(mock_page)).to_have_count(1)
        expect(mock_page.get_by_role("banner")).to_have_count(1)
        expect(mock_page.get_by_role("main")).to_have_count(1)
        expect(nav(mock_page)).to_have_count(1)
