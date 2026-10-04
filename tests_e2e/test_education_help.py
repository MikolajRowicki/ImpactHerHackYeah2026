"""Education and the help place: general places that need no group (specs: frontend-education,
frontend-help)."""

import json
from urllib.parse import urlparse

from playwright.sync_api import expect

from .helpers import h1, live, nav, open_as
from .test_live_flows import example, me_with


def test_a_person_without_a_group_opens_education_with_a_link_to_help(mock_page):
    open_as(mock_page, "no_group")
    mock_page.get_by_role("link", name="Wiedza").first.click()

    expect(h1(mock_page)).to_have_text("Wiedza o depresji poporodowej")
    for title in (
        "Czym jest depresja poporodowa",
        "Baby blues a depresja poporodowa",
        "Co warto zauważyć",
        "Jak może wspierać bliska osoba",
        "Kiedy i gdzie szukać pomocy",
    ):
        expect(mock_page.get_by_role("heading", name=title)).to_be_visible()
    expect(
        mock_page.get_by_role("link", name="Zobacz telefony wsparcia i ścieżkę pomocy")
    ).to_be_visible()


def test_education_is_the_same_for_a_mother_and_a_supporter(mock_page):
    texts = []
    for perspective in ("woman", "supporter"):
        open_as(mock_page, perspective, "/education")
        expect(h1(mock_page)).to_have_text("Wiedza o depresji poporodowej")
        texts.append(mock_page.locator("main").inner_text())

    assert texts[0] == texts[1]


def test_education_says_it_is_not_a_diagnosis(mock_page):
    open_as(mock_page, "woman", "/education")

    expect(mock_page.get_by_text("To ogólne informacje, nie diagnoza.")).to_be_visible()


def test_start_without_a_group_offers_the_panel_education_and_help(mock_page):
    open_as(mock_page, "no_group")

    expect(mock_page.get_by_role("heading", name="Co chcesz zrobić?")).to_be_visible()
    main = mock_page.locator("main")
    expect(main.get_by_role("link", name="Wiedza")).to_be_visible()
    expect(main.get_by_role("link", name="Pomoc")).to_be_visible()


def test_education_is_in_the_navigation_of_every_signed_in_person(mock_page):
    for perspective in ("no_group", "pending", "woman", "partner", "supporter"):
        open_as(mock_page, perspective)
        expect(nav(mock_page).get_by_role("link", name="Wiedza")).to_be_visible()


# Help


def test_help_shows_every_crisis_line_and_step_in_order(mock_page):
    open_as(mock_page, "woman", "/help")
    expect(h1(mock_page)).to_have_text("Pomoc")

    answer = json.loads(
        (
            __import__("pathlib").Path(__file__).resolve().parents[1]
            / "contracts"
            / "examples"
            / "get_help.200.general.json"
        ).read_text(encoding="utf-8")
    )
    for line in answer["crisis_lines"]:
        item = mock_page.get_by_role("listitem").filter(has_text=line["name"])
        expect(item).to_contain_text(line["hours"])
        expect(item).to_contain_text(line["description"])
    steps = mock_page.get_by_role("list").filter(
        has=mock_page.get_by_role("heading", level=3, name="Porozmawiaj z kimś zaufanym")
    )
    expect(steps.get_by_role("heading", level=3)).to_have_text(
        [step["title"] for step in sorted(answer["path"], key=lambda s: s["order"])]
    )


def test_every_crisis_number_dials(mock_page):
    open_as(mock_page, "woman", "/help")
    expect(h1(mock_page)).to_have_text("Pomoc")

    expect(mock_page.get_by_role("link", name="116 123")).to_have_attribute("href", "tel:116123")
    expect(mock_page.get_by_role("link", name="800 70 2222")).to_have_attribute(
        "href", "tel:800702222"
    )
    hrefs = mock_page.locator("main a[href^='tel:']").evaluate_all("(a) => a.map((x) => x.href)")
    assert len(hrefs) == 3


def test_help_says_the_app_is_not_a_doctor(mock_page):
    open_as(mock_page, "partner", "/help")

    expect(mock_page.get_by_text("MaydayMama nie zastępuje lekarza")).to_be_visible()
    expect(mock_page.get_by_text("niczego nie diagnozuje")).to_be_visible()


def test_failed_help_still_shows_112_with_the_message_and_a_retry(mock_page):
    answers = {
        "GET /api/v1/me": (200, me_with(None)),
        "GET /api/v1/help": (
            500,
            {"error": {"code": "server_error", "message": "Serwer chwilowo odpoczywa."}},
        ),
    }
    live(mock_page, answers, "/help")

    expect(mock_page.get_by_role("link", name="112")).to_have_attribute("href", "tel:112")
    expect(mock_page.get_by_text("Serwer chwilowo odpoczywa.")).to_be_visible()
    answers["GET /api/v1/help"] = (200, example("get_help.200.json"))
    mock_page.get_by_role("button", name="Spróbuj ponownie").click()

    expect(mock_page.get_by_role("link", name="116 123")).to_be_visible()
    expect(mock_page.get_by_text("Mazowiecki Oddział Wojewódzki NFZ")).to_be_visible()


def test_help_is_asked_without_a_group_header(mock_page):
    seen = []

    def answer(route):
        request = route.request
        path = urlparse(request.url).path
        seen.append((path, request.headers.get("x-group-id")))
        if path == "/api/v1/me":
            route.fulfill(status=200, json=me_with("active", role="woman", name="Anna"))
        elif path == "/api/v1/me/memberships":
            route.fulfill(
                status=200,
                json={
                    "items": [
                        {
                            "group_id": 1,
                            "role": "woman",
                            "group_status": "active",
                            "woman_name": "Anna",
                        }
                    ]
                },
            )
        elif path == "/api/v1/help":
            route.fulfill(status=200, json=example("get_help.200.general.json"))
        else:
            route.fulfill(status=404, json={"error": {"code": "not_found", "message": "Brak."}})

    mock_page.route("**/api/v1/**", answer)
    mock_page.goto(f"{mock_page.base}?mock=0#/help")
    expect(mock_page.get_by_role("link", name="116 123")).to_be_visible()

    assert ("/api/v1/help", None) in seen
