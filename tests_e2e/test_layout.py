import pytest
from playwright.sync_api import expect

SIZES = [pytest.param(375, 800, id="phone"), pytest.param(1280, 800, id="laptop")]


@pytest.mark.parametrize(("width", "height"), SIZES)
def test_page_has_no_horizontal_scroll(mock_page, width, height):
    mock_page.set_viewport_size({"width": width, "height": height})
    mock_page.goto(f"{mock_page.base}?mock=1")
    expect(mock_page.get_by_text("Zalogowano jako Anna.")).to_be_visible()

    overflow = mock_page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0


def test_static_server_serves_the_page_with_sample_data(mock_page):
    mock_page.goto(f"{mock_page.base}?mock=1")

    expect(mock_page.get_by_role("link", name="MaydayMama")).to_be_visible()
    expect(mock_page.get_by_text("Zalogowano jako Anna.")).to_be_visible()
