from playwright.sync_api import expect

from .helpers import h1, open_as

LIGHT_BG = "rgb(250, 247, 242)"
DARK_BG = "rgb(28, 36, 32)"


def background(page):
    return page.evaluate("getComputedStyle(document.body).backgroundColor")


def test_system_dark_shows_the_dark_theme(mock_page):
    mock_page.emulate_media(color_scheme="dark")
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    assert background(mock_page) == DARK_BG
    expect(mock_page.get_by_role("button", name="Ciemny motyw")).to_have_attribute(
        "aria-pressed", "true"
    )


def test_system_light_shows_the_light_theme(mock_page):
    mock_page.emulate_media(color_scheme="light")
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")

    assert background(mock_page) == LIGHT_BG


def test_manual_choice_is_remembered_regardless_of_the_system(mock_page):
    mock_page.emulate_media(color_scheme="dark")
    open_as(mock_page, "woman")
    switch = mock_page.get_by_role("button", name="Ciemny motyw")
    expect(switch).to_have_attribute("aria-pressed", "true")

    switch.click()
    expect(switch).to_have_attribute("aria-pressed", "false")
    assert background(mock_page) == LIGHT_BG

    mock_page.reload()
    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    assert background(mock_page) == LIGHT_BG
    expect(mock_page.get_by_role("button", name="Ciemny motyw")).to_have_attribute(
        "aria-pressed", "false"
    )


def test_font_files_are_served(mock_page):
    responses = {}
    mock_page.on(
        "response", lambda r: responses.update({r.url: r.status}) if ".woff2" in r.url else None
    )
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    mock_page.wait_for_function("document.fonts.check('16px Nunito', 'ąę')")

    assert responses, "no font was requested"
    assert all(status == 200 for status in responses.values()), responses
    licence = mock_page.request.get(mock_page.base.replace("index.html", "fonts/OFL.txt"))
    assert licence.status == 200
