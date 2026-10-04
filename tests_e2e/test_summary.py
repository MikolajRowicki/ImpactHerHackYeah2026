import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .helpers import h1, open_as

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"


def summary(page):
    return page.get_by_role("region", name="Ogólny obraz")


def serve_summary(page, name, **changes):
    """Answers the summary example with some fields changed, to show other trends."""
    body = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    body.update(changes)
    page.route(f"**/contracts/examples/{name}", lambda route: route.fulfill(json=body))


def test_mothers_summary_shows_statements_and_narrative(mock_page):
    open_as(mock_page, "woman")

    card = summary(mock_page)
    expect(card.get_by_text("W ostatnich dniach było trudniej niż zwykle.")).to_be_visible()
    expect(card.get_by_text("Dobrze, że zaglądasz tu regularnie. To ważny krok.")).to_be_visible()
    expect(card.get_by_text("To przykładowy tekst.")).to_have_count(0)
    expect(card.get_by_role("complementary", name="Na dziś")).to_have_count(0)


def test_loved_ones_summary_sets_the_care_reminder_apart(mock_page):
    open_as(mock_page, "partner")

    reminder = summary(mock_page).get_by_role("complementary", name="Na dziś")
    expect(reminder).to_contain_text("Zadbaj dziś o nią szczególnie")
    statements = summary(mock_page).locator(".summary__statements")
    expect(statements).not_to_contain_text("Zadbaj dziś o nią szczególnie")


def test_needs_attention_points_to_help_without_red(mock_page):
    open_as(mock_page, "partner")
    card = summary(mock_page)

    expect(card.get_by_text("Wygląda na to, że ostatnio jest jej trudniej.")).to_be_visible()
    card.get_by_role("link", name="Zobacz, gdzie szukać wsparcia").click()
    expect(h1(mock_page)).to_have_text("Pomoc")

    open_as(mock_page, "partner")
    expect(summary(mock_page)).to_be_visible()
    reds = summary(mock_page).evaluate(
        """(root) => {
            const red = (value) => {
                const m = value.match(/rgba?\\((\\d+), (\\d+), (\\d+)/);
                if (!m) return false;
                const [r, g, b] = m.slice(1).map(Number);
                return r > 150 && g < 110 && b < 110;
            };
            return [root, ...root.querySelectorAll("*")].filter((el) => {
                const style = getComputedStyle(el);
                return red(style.color) || red(style.backgroundColor) || red(style.borderColor);
            }).length;
        }"""
    )
    assert reds == 0


def test_stable_trend_is_calm_and_adds_no_help_prompt(mock_page):
    serve_summary(mock_page, "get_summary_extended.200.json", trend="stable")
    open_as(mock_page, "woman")

    card = summary(mock_page)
    expect(card.get_by_text("Ostatnie dni wyglądają spokojnie.")).to_be_visible()
    expect(card.get_by_role("link", name="Zobacz, gdzie szukać wsparcia")).to_have_count(0)


def test_needs_attention_shows_the_reasons_and_the_crisis_lines(mock_page):
    open_as(mock_page, "woman")

    card = summary(mock_page)
    expect(card.get_by_role("heading", name="Skąd ten obraz")).to_be_visible()
    expect(card.get_by_text("To obraz ogólny, nie ocena.")).to_be_visible()
    lines = card.get_by_role("region", name="Gdzie szukać wsparcia")
    expect(lines.get_by_role("link", name="116 123")).to_have_attribute("href", "tel:116123")
    expect(lines.get_by_role("link", name="112")).to_have_attribute("href", "tel:112")


def test_stable_summary_shows_no_crisis_lines_and_no_reasons(mock_page):
    serve_summary(
        mock_page,
        "get_summary_extended.200.json",
        trend="stable",
        reasons=[],
        help=None,
    )
    open_as(mock_page, "woman")

    expect(summary(mock_page)).to_be_visible()
    expect(summary(mock_page).get_by_role("region", name="Gdzie szukać wsparcia")).to_have_count(0)
    expect(summary(mock_page).get_by_role("heading", name="Skąd ten obraz")).to_have_count(0)


def test_trend_is_never_a_number(mock_page):
    open_as(mock_page, "partner")
    text = summary(mock_page).locator(".summary__trend").inner_text()

    assert not any(ch.isdigit() for ch in text), text


def test_mock_narrative_is_hidden(mock_page):
    open_as(mock_page, "supporter")

    card = summary(mock_page)
    expect(card).to_be_visible()
    expect(card.locator(".summary__narrative")).to_have_count(0)
    expect(card.get_by_text("Przykładowy tekst", exact=True)).to_have_count(0)


@pytest.mark.parametrize(
    "name", ["get_summary_extended.200.json", "get_summary_extended.200.partner.json"]
)
def test_uncertain_trend_does_not_claim_the_last_days_were_different(mock_page, name):
    serve_summary(mock_page, name, trend="uncertain")
    open_as(mock_page, "woman" if name == "get_summary_extended.200.json" else "partner")

    text = summary(mock_page).locator(".summary__trend").inner_text()
    assert "Na razie nie da się powiedzieć nic pewnego." in text
    assert "były różne" not in text


def test_narrative_from_rules_is_shown(mock_page):
    serve_summary(
        mock_page,
        "get_summary_extended.200.json",
        narrative={"text": "Spokojny tydzień.", "source": "rules"},
    )
    open_as(mock_page, "woman")

    expect(summary(mock_page).get_by_text("Spokojny tydzień.")).to_be_visible()
    expect(summary(mock_page).get_by_text("Przykładowy tekst", exact=True)).to_have_count(0)
    expect(summary(mock_page).locator(".origin-label")).to_have_count(0)


def test_narrative_from_a_model_says_it_was_prepared_with_ai(mock_page):
    serve_summary(
        mock_page,
        "get_summary_extended.200.json",
        narrative={"text": "Tekst od modelu.", "source": "groq"},
    )
    open_as(mock_page, "woman")

    narrative = summary(mock_page).locator(".summary__narrative")
    expect(narrative).to_contain_text("Tekst od modelu.")
    expect(narrative.locator(".origin-label")).to_have_text("Przygotowane z pomocą AI")


@pytest.mark.parametrize(
    ("timezone", "shown"),
    [("Europe/Warsaw", "22:05"), ("America/New_York", "16:05")],
)
def test_summary_time_is_shown_in_local_time(browser, static_url, timezone, shown):
    context = browser.new_context(timezone_id=timezone)
    page = context.new_page()
    page.base = f"{static_url}/src/frontend/index.html"
    open_as(page, "woman")

    expect(summary(page).get_by_text("Przygotowano 3 października 2026")).to_contain_text(shown)
    context.close()
