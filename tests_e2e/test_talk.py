"""The loved ones' conversation guide: topics, the three parts, sources, labels and entry points."""

import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .helpers import h1, live, nav, open_as
from .test_contrast_layout import CONTRAST

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"
GUIDE = "GET /api/v1/ai/conversation-guide"
PACJENT = {
    "title": "Młoda matka w depresji",
    "url": "https://pacjent.gov.pl/jak-zyc-z-choroba/mloda-matka-w-depresji",
}
MP = {
    "title": "Depresja i psychoza poporodowa",
    "url": "https://www.mp.pl/pacjent/psychiatria/choroby/91686,depresja-i-psychoza-poporodowa",
}


def example(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def guide(lines, source="groq", sources=(), topic="hard_day"):
    return {
        "topic": topic,
        "opening_lines": list(lines),
        "avoid": ["Oceniania, co zrobiła lub czego nie zdążyła."],
        "questions": ["Co najbardziej Cię dziś wyczerpało?"],
        "source": source,
        "sources": list(sources),
    }


def open_live(page, path, guide_answer=None):
    answers = {"GET /api/v1/me": (200, example("get_me.200.partner.json"))}
    if guide_answer is not None:
        answers[GUIDE] = guide_answer
    calls = live(page, answers, path)
    expect(h1(page)).to_have_text("Jak z nią rozmawiać")
    return answers, calls


def guide_urls(page):
    urls = []
    page.on("request", lambda r: urls.append(r.url) if "/ai/conversation-guide" in r.url else None)
    return urls


def part(page, title):
    return page.get_by_role("region", name=title)


# Entry points and access


def test_the_loved_ones_start_has_a_card_that_opens_the_topics(mock_page):
    open_as(mock_page, "supporter")
    mock_page.get_by_role("link", name="Jak z nią rozmawiać").click()
    expect(h1(mock_page)).to_have_text("Jak z nią rozmawiać")
    topics = mock_page.get_by_role("navigation", name="Tematy rozmowy").get_by_role("link")
    expect(topics).to_have_count(5)
    expect(mock_page.get_by_text("Wybierz temat z listy")).to_be_visible()


def test_the_loved_ones_navigation_gets_no_new_item(mock_page):
    open_as(mock_page, "partner")
    expect(nav(mock_page).get_by_role("link")).to_have_text(
        ["Start", "Pytania", "Zadania", "Grupa", "Wiedza", "Pomoc"]
    )


def test_a_summary_that_needs_attention_links_to_the_professional_help_topic(mock_page):
    open_as(mock_page, "partner")
    link = mock_page.get_by_role("link", name="Jak delikatnie porozmawiać o pomocy specjalisty")
    expect(link).to_have_attribute("href", "#/talk/suggest_professional_help")
    link.click()
    expect(mock_page.get_by_role("heading", name="Rozmowa o pomocy specjalisty")).to_be_visible()


def test_the_mothers_summary_has_no_guide_link(mock_page):
    open_as(mock_page, "woman")
    expect(mock_page.get_by_role("link", name="Zobacz, gdzie szukać wsparcia")).to_be_visible()
    expect(mock_page.get_by_role("link", name="Jak delikatnie porozmawiać")).to_have_count(0)


def test_the_mother_sees_that_the_guide_is_for_close_ones(mock_page):
    open_as(mock_page, "woman", "/talk/hard_day")
    expect(mock_page.get_by_text("To miejsce jest dla bliskich osób mamy.")).to_be_visible()


def test_a_person_without_a_group_sees_that_a_group_is_needed(mock_page):
    open_as(mock_page, "no_group", "/talk")
    expect(mock_page.get_by_text("To miejsce otworzy się, gdy dołączysz do grupy")).to_be_visible()


# Topics and the guide


def test_a_picked_topic_shows_its_three_parts_and_is_marked(mock_page):
    open_as(mock_page, "supporter", "/talk")
    mock_page.get_by_role("link", name="Wysłuchaj bez rad").click()

    expect(mock_page.get_by_role("heading", name="Wysłuchaj bez rad", level=2)).to_be_visible()
    expect(part(mock_page, "Od czego zacząć").get_by_role("listitem")).to_have_count(2)
    avoid = part(mock_page, "Czego unikać")
    expect(avoid.get_by_text("Przerywania i podsuwania gotowych rozwiązań.")).to_be_visible()
    expect(part(mock_page, "O co dopytać").get_by_role("listitem")).to_have_count(2)
    current = mock_page.get_by_role("link", name="Wysłuchaj bez rad")
    expect(current).to_have_attribute("aria-current", "page")
    expect(mock_page.get_by_role("link", name="Po trudnym dniu")).not_to_have_attribute(
        "aria-current", "page"
    )
    assert mock_page.api_requests == []


def test_a_topic_address_opens_that_topic_and_asks_for_it(mock_page):
    urls = guide_urls(mock_page)
    open_live(
        mock_page,
        "/talk/suggest_professional_help",
        (200, guide(["Martwię się o Ciebie."], topic="suggest_professional_help")),
    )
    heading = mock_page.get_by_role("heading", name="Rozmowa o pomocy specjalisty", level=2)
    expect(heading).to_be_visible()
    expect(part(mock_page, "Od czego zacząć")).to_contain_text("Martwię się o Ciebie.")
    assert urls[0].endswith("/api/v1/ai/conversation-guide?topic=suggest_professional_help")


@pytest.mark.parametrize(
    ("path", "hint"),
    [("/talk/pogoda", "Nie ma takiego tematu."), ("/talk", "Wybierz temat z listy")],
)
def test_without_a_known_topic_the_list_is_shown_and_nothing_is_asked(mock_page, path, hint):
    _, calls = open_live(mock_page, path, (200, guide(["Nie powinno przyjść."])))
    expect(mock_page.get_by_text(hint)).to_be_visible()
    topics = mock_page.get_by_role("navigation", name="Tematy rozmowy").get_by_role("link")
    expect(topics).to_have_count(5)
    expect(mock_page.get_by_role("heading", level=2)).to_have_count(0)
    assert GUIDE not in calls


def test_other_opening_lines_ask_again_for_the_same_topic(mock_page):
    urls = guide_urls(mock_page)
    answers, _ = open_live(mock_page, "/talk/hard_day", (200, guide(["Pierwsza linia."])))
    expect(part(mock_page, "Od czego zacząć")).to_contain_text("Pierwsza linia.")

    answers[GUIDE] = (200, guide(["Druga linia."]))
    mock_page.get_by_role("button", name="Inne propozycje zdań").click()
    expect(part(mock_page, "Od czego zacząć")).to_contain_text("Druga linia.")
    expect(part(mock_page, "Od czego zacząć")).not_to_contain_text("Pierwsza linia.")
    assert len(urls) == 2 and urls[0] == urls[1]


def test_a_failure_to_get_other_lines_keeps_the_guide_and_says_so(mock_page):
    answers, _ = open_live(mock_page, "/talk/hard_day", (200, guide(["Pierwsza linia."])))
    answers[GUIDE] = (500, {"error": {"code": "unknown", "message": "Błąd."}})
    mock_page.get_by_role("button", name="Inne propozycje zdań").click()
    expect(mock_page.get_by_text("Nie udało się przygotować nowych propozycji.")).to_be_visible()
    expect(part(mock_page, "Od czego zacząć")).to_contain_text("Pierwsza linia.")


# Sources and labels


def test_sources_are_links_with_the_site_name_that_open_in_a_new_tab(mock_page):
    open_live(mock_page, "/talk/hard_day", (200, guide(["Linia."], sources=[PACJENT, MP])))
    sources = part(mock_page, "Źródła")
    expect(sources.get_by_role("listitem")).to_have_count(2)
    for source, site in ((PACJENT, "pacjent.gov.pl"), (MP, "mp.pl")):
        link = sources.get_by_role("link", name=source["title"])
        expect(link).to_have_attribute("href", source["url"])
        expect(link).to_have_attribute("target", "_blank")
        expect(link).to_have_attribute("rel", "noopener noreferrer")
        expect(sources.get_by_text(site, exact=True)).to_be_visible()
    label = "Przygotowane z pomocą AI na podstawie źródeł poniżej"
    expect(mock_page.locator(".origin-label")).to_have_text(label)


def test_without_sources_there_is_no_sources_heading(mock_page):
    open_live(mock_page, "/talk/hard_day", (200, guide(["Linia."])))
    expect(part(mock_page, "Od czego zacząć")).to_be_visible()
    expect(mock_page.get_by_role("heading", name="Źródła")).to_have_count(0)
    expect(mock_page.locator(".origin-label")).to_have_text("Przygotowane z pomocą AI")


def test_a_link_that_is_not_https_is_never_shown(mock_page):
    unsafe = {"title": "Podejrzany", "url": "javascript:alert(1)"}
    open_live(mock_page, "/talk/hard_day", (200, guide(["Linia."], sources=[unsafe, PACJENT])))
    expect(part(mock_page, "Źródła").get_by_role("listitem")).to_have_count(1)
    expect(mock_page.get_by_role("link", name="Podejrzany")).to_have_count(0)


@pytest.mark.parametrize(("source", "label"), [("mock", "Tekst przykładowy"), ("rules", None)])
def test_mock_and_fixed_guides_are_labelled_by_their_origin(mock_page, source, label):
    open_live(mock_page, "/talk/hard_day", (200, guide(["Linia."], source=source)))
    expect(part(mock_page, "Od czego zacząć")).to_be_visible()
    labels = mock_page.locator(".origin-label")
    if label:
        expect(labels).to_have_text(label)
    else:
        expect(labels).to_have_count(0)


def test_mock_mode_gives_a_guide_with_sources(mock_page):
    open_as(mock_page, "partner", "/talk/suggest_professional_help")
    sources = part(mock_page, "Źródła")
    expect(sources.get_by_role("link")).to_have_count(3)
    expect(mock_page.get_by_text("Tekst przykładowy")).to_be_visible()
    assert mock_page.api_requests == []


def test_topics_and_sources_are_readable_in_both_themes(mock_page):
    for scheme in ("light", "dark"):
        mock_page.emulate_media(color_scheme=scheme)
        open_as(mock_page, "partner", "/talk/hard_day")
        expect(part(mock_page, "Źródła")).to_be_visible()
        for selector in (
            ".talk__topic:not([aria-current])",
            ".talk__topic[aria-current]",
            ".sources__list a",
            ".sources__site",
            ".talk__note",
            ".origin-label",
        ):
            ratio = mock_page.evaluate(CONTRAST, [selector, "color"])
            assert ratio >= 4.5, f"{scheme} {selector}: {ratio}"
