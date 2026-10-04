"""The landing page of a signed-out visitor (spec: frontend-landing)."""

import re

from playwright.sync_api import expect

from .helpers import h1, live, nav, open_as
from .test_live_flows import example

TITLE = "zauważyć wcześnie, wspierać razem"


def signed_out(page):
    open_as(page, "woman")
    page.get_by_role("button", name="Wyloguj").click()
    expect(h1(page)).to_have_text("Zaloguj się")
    page.goto(f"{page.base}?mock=1#/")
    expect(h1(page)).to_have_text(TITLE)


def test_a_visitor_sees_the_landing_page_with_both_actions(mock_page):
    signed_out(mock_page)

    main = mock_page.locator("main")
    expect(main.get_by_role("link", name="Załóż konto").first).to_have_attribute(
        "href", "#/register"
    )
    expect(main.get_by_role("link", name="Zaloguj się").first).to_have_attribute("href", "#/login")


def test_the_three_roles_are_explained_in_separate_blocks(mock_page):
    signed_out(mock_page)

    roles = mock_page.get_by_role("region", name="Dla kogo jest MaydayMama").get_by_role("article")
    expect(roles).to_have_count(3)
    for name in ("Mama", "Partner", "Bliska osoba"):
        expect(
            roles.filter(has=mock_page.get_by_role("heading", name=name, exact=True))
        ).to_have_count(1)


def test_it_states_the_privacy_promise_the_doubt_note_and_links_to_help(mock_page):
    signed_out(mock_page)

    privacy = mock_page.get_by_role("region", name="Kto co widzi?")
    expect(privacy).to_contain_text("Pojedyncze wpisy widzi tylko mama.")
    expect(privacy).to_contain_text("Bliscy widzą wyłącznie ogólny obraz")
    safety = mock_page.get_by_role("region", name="Siatka bezpieczeństwa")
    expect(safety).to_contain_text("niczego nie diagnozuje")
    safety.get_by_role("link", name="Zobacz, gdzie szukać pomocy").click()
    expect(h1(mock_page)).to_have_text("Pomoc")


def test_the_table_says_in_words_who_sees_what(mock_page):
    signed_out(mock_page)

    row = mock_page.get_by_role("row").filter(has_text="Jej codzienne wpisy")
    cells = row.get_by_role("cell")
    expect(cells.nth(0)).to_contain_text("widzi")
    expect(cells.nth(1)).to_contain_text("nie widzi")


def test_a_signed_in_person_sees_their_start_at_the_root(mock_page):
    open_as(mock_page, "woman", "/")

    expect(h1(mock_page)).to_have_text("Cześć, Anna")


def test_an_invitation_link_is_not_replaced_by_the_landing_page(mock_page):
    signed_out(mock_page)

    mock_page.goto(f"{mock_page.base}?mock=1#/invite/k3p9x2vb7qd4")

    expect(h1(mock_page)).to_contain_text("Anna zaprasza Cię do grupy")


def test_the_header_offers_help_to_a_visitor(mock_page):
    signed_out(mock_page)

    expect(nav(mock_page).get_by_role("link", name="Pomoc")).to_be_visible()


def test_a_failed_read_of_the_session_is_not_shown_as_a_visitor(mock_page):
    live(mock_page, {"GET /api/v1/me": (500, example("get_me.401.json"))})

    expect(mock_page.get_by_role("button", name="Spróbuj ponownie")).to_be_visible()


# Motion and layout


def test_reduced_motion_runs_no_animation_and_shows_everything(browser, static_url):
    context = browser.new_context(reduced_motion="reduce")
    page = context.new_page()
    page.base = f"{static_url}/src/frontend/index.html"
    signed_out(page)

    names = page.evaluate(
        """() => [...document.querySelectorAll(".landing *")]
            .map((el) => getComputedStyle(el).animationName)
            .filter((name) => name !== "none")"""
    )
    assert names == []
    expect(page.get_by_role("heading", name="Kto co widzi?")).to_be_visible()
    context.close()


def test_motion_is_one_settling_animation_when_allowed(browser, static_url):
    context = browser.new_context(reduced_motion="no-preference")
    page = context.new_page()
    page.base = f"{static_url}/src/frontend/index.html"
    signed_out(page)

    names = set(
        page.evaluate(
            """() => [...document.querySelectorAll(".landing *")]
            .map((el) => getComputedStyle(el).animationName)
            .filter((name) => name !== "none")"""
        )
    )
    assert names == {"settle"}
    context.close()


def test_no_horizontal_scroll_on_a_phone(browser, static_url):
    context = browser.new_context(viewport={"width": 375, "height": 800})
    page = context.new_page()
    page.base = f"{static_url}/src/frontend/index.html"
    signed_out(page)

    widths = page.evaluate(
        "() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]"
    )
    assert widths[0] <= widths[1], widths
    context.close()


def test_body_text_has_enough_contrast_in_both_themes(browser, static_url):
    probe = """() => {
        const parse = (c) => c.match(/[\\d.]+/g).slice(0, 4).map(Number);
        const channel = (v) => {
            v /= 255;
            return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
        };
        const lum = ([r, g, b]) => 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
        const backdrop = (el) => {
            for (let n = el; n; n = n.parentElement) {
                const c = parse(getComputedStyle(n).backgroundColor);
                if (c.length < 4 || c[3] > 0.5) return c;
            }
            return parse(getComputedStyle(document.body).backgroundColor);
        };
        const selector = [
            "p", "h1 span", "h2", "h3", "li", "th", "td", "a",
        ].map((tag) => ".landing " + tag).join(", ");
        const bad = [];
        for (const el of document.querySelectorAll(selector)) {
            if (!el.textContent.trim() || el.closest("[aria-hidden=true], .notes")) continue;
            const style = getComputedStyle(el);
            const [a, b] = [lum(parse(style.color)), lum(backdrop(el))].sort((x, y) => y - x);
            const ratio = (a + 0.05) / (b + 0.05);
            const size = parseFloat(style.fontSize);
            const large = size >= 24 || (size >= 18.66 && Number(style.fontWeight) >= 700);
            if (ratio < (large ? 3 : 4.5)) {
                bad.push([el.tagName, el.textContent.trim().slice(0, 30), ratio.toFixed(2)]);
            }
        }
        return bad;
    }"""
    for scheme in ("light", "dark"):
        context = browser.new_context(color_scheme=scheme)
        page = context.new_page()
        page.base = f"{static_url}/src/frontend/index.html"
        signed_out(page)
        assert page.evaluate(probe) == [], scheme
        context.close()


def test_one_letter_words_are_glued_to_the_next_word(mock_page):
    signed_out(mock_page)

    text = mock_page.locator(".landing").inner_text()
    # A single-letter word followed by a plain space could end a line.
    assert not re.search(r"(?<![^\s(„])[aiouwzAIOUWZ] (?=\S)", text), text


def test_the_page_declares_a_favicon_that_follows_the_color_scheme(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")

    href = mock_page.locator('link[rel="icon"]').get_attribute("href")
    assert href == "favicon.svg"
    svg = mock_page.request.get(mock_page.url.split("index.html")[0] + href)
    assert svg.ok
    assert "prefers-color-scheme: dark" in svg.text()
