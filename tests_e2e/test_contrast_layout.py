import pytest
from playwright.sync_api import expect

from .helpers import h1, open_as

# WCAG contrast of the computed colours, measured in the page. Background is the first
# non-transparent background found walking up from the element.
CONTRAST = """([selector, part]) => {
    const el = document.querySelector(selector);
    if (!el) return null;
    const parse = (value) => {
        const m = value.match(/rgba?\\(([\\d.]+),? ([\\d.]+),? ([\\d.]+)(?:,? \\/? ?([\\d.]+))?/);
        if (!m) return null;
        return { rgb: [m[1], m[2], m[3]].map(Number), a: m[4] === undefined ? 1 : Number(m[4]) };
    };
    const background = (node) => {
        for (let n = node; n; n = n.parentElement) {
            const c = parse(getComputedStyle(n).backgroundColor);
            if (c && c.a > 0.5) return c.rgb;
        }
        return parse(getComputedStyle(document.body).backgroundColor).rgb;
    };
    const lum = ([r, g, b]) => {
        const f = (v) => {
            v /= 255;
            return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
        };
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    };
    const style = getComputedStyle(el);
    const fg = parse(part === "border" ? style.borderTopColor : style.color).rgb;
    const bg = part === "border" ? background(el.parentElement) : background(el);
    const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x);
    return (a + 0.05) / (b + 0.05);
}"""

# (perspective, route, selector, what is measured, minimum ratio)
CHECKS = [
    ("supporter", "/tasks", "main h1", "color", 4.5),
    ("supporter", "/tasks", ".page-head__lead", "color", 4.5),
    ("supporter", "/tasks", ".task-row__meta", "color", 4.5),
    ("supporter", "/tasks", ".task-row .button", "color", 4.5),
    ("supporter", "/tasks", ".button--accent", "color", 4.5),
    ("supporter", "/tasks", ".field__hint", "color", 4.5),
    ("supporter", "/tasks", ".field__input", "border", 3),
    ("supporter", "/tasks", ".site-nav a[aria-current]", "color", 4.5),
    ("supporter", "/tasks", ".site-nav a:not([aria-current])", "color", 4.5),
    ("supporter", "/tasks", ".mock-notice__text", "color", 4.5),
    ("partner", "/", ".summary__trend-text", "color", 4.5),
    ("partner", "/", ".summary__help", "color", 4.5),
    ("partner", "/", ".summary__reminder-text", "color", 4.5),
    ("partner", "/", ".summary__time", "color", 4.5),
    ("partner", "/", ".chip", "color", 4.5),
    ("partner", "/", ".cta-card__title", "color", 4.5),
    ("woman", "/check-in", ".choice__label", "color", 4.5),
    ("woman", "/check-in", ".choice", "border", 3),
    ("woman", "/group", ".button--danger", "color", 4.5),
]


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_text_and_controls_have_enough_contrast(mock_page, scheme):
    mock_page.emulate_media(color_scheme=scheme)
    failures = []
    current = None
    for perspective, route, selector, part, minimum in CHECKS:
        if current != (perspective, route):
            open_as(mock_page, perspective, route)
            expect(h1(mock_page)).to_be_visible()
            expect(mock_page.locator(selector).first).to_be_attached()
            current = (perspective, route)
        ratio = mock_page.evaluate(CONTRAST, [selector, part])
        if ratio is None or ratio < minimum:
            failures.append(f"{scheme} {route} {selector} {part}: {ratio}")
    assert failures == []


def test_error_text_has_enough_contrast_in_both_themes(mock_page):
    for scheme in ("light", "dark"):
        mock_page.emulate_media(color_scheme=scheme)
        open_as(mock_page, "partner", "/tasks")
        mock_page.get_by_role("button", name="Dodaj zadanie").click()
        expect(mock_page.get_by_text("Wpisz krótki tytuł zadania.")).to_be_visible()

        assert mock_page.evaluate(CONTRAST, [".field__error", "color"]) >= 4.5


ROUTES = [
    ("woman", "/"),
    ("woman", "/check-in"),
    ("woman", "/tasks"),
    ("woman", "/group"),
    ("woman", "/help"),
    ("woman", "/questions"),
    ("woman", "/nie-ma-takiej"),
    ("woman", "/invite/k3p9x2vb7qd4"),
    ("woman", "/invite/nieznany-token"),
    ("partner", "/"),
    ("partner", "/questions"),
    ("partner", "/group"),
    ("supporter", "/tasks"),
    ("no_group", "/"),
    ("no_group", "/invite/k3p9x2vb7qd4"),
    ("pending", "/"),
    ("pending", "/group"),
]


def overflow(page):
    return page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_every_screen_fits_a_phone_without_horizontal_scroll(mock_page, scheme):
    mock_page.emulate_media(color_scheme=scheme)
    mock_page.set_viewport_size({"width": 375, "height": 800})
    wide = []
    for perspective, route in ROUTES:
        open_as(mock_page, perspective, route)
        expect(h1(mock_page)).to_be_visible()
        if overflow(mock_page) > 0:
            wide.append(f"{perspective} {route}")

    # Signed-out screens.
    mock_page.get_by_role("button", name="Wyloguj").click()
    for route in ("/login", "/register", "/invite/k3p9x2vb7qd4", "/help"):
        mock_page.goto(f"{mock_page.base}#{route}")
        expect(h1(mock_page)).to_be_visible()
        if overflow(mock_page) > 0:
            wide.append(f"signed out {route}")
    assert wide == []


def test_invitation_link_fits_a_phone(mock_page):
    mock_page.set_viewport_size({"width": 375, "height": 800})
    open_as(mock_page, "woman", "/group")
    mock_page.get_by_role("button", name="Utwórz link zaproszenia").click()
    expect(mock_page.get_by_label("Link zaproszenia")).to_be_visible()

    assert overflow(mock_page) <= 0


def test_text_lines_stay_readable_on_a_laptop(mock_page):
    mock_page.set_viewport_size({"width": 1280, "height": 800})
    open_as(mock_page, "woman", "/check-in")
    expect(h1(mock_page)).to_be_visible()

    width = mock_page.locator("main").evaluate("(el) => el.getBoundingClientRect().width")
    assert width <= 720
