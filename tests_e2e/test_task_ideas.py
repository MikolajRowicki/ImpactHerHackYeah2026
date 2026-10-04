from playwright.sync_api import expect

from .helpers import change_mock_state, h1, open_as


def ideas(page):
    return page.get_by_role("region", name="Pomysły na zadania")


def test_ideas_are_listed_with_title_and_details(mock_page):
    open_as(mock_page, "partner", "/tasks")
    expect(h1(mock_page)).to_have_text("Zadania")

    expect(ideas(mock_page).get_by_role("listitem")).to_have_count(4)
    first = ideas(mock_page).get_by_role("listitem").filter(has_text="Wyjść z dzieckiem na spacer")
    expect(first).to_contain_text("Godzina dla niej na sen, prysznic albo ciszę.")


def test_adding_an_idea_creates_that_task_and_confirms(mock_page):
    open_as(mock_page, "partner", "/tasks")
    open_column = mock_page.get_by_role("region", name="Do wzięcia", exact=True)
    expect(open_column.get_by_role("heading", name="Przejąć nocną zmianę")).to_have_count(0)

    ideas(mock_page).get_by_role("button", name="Dodaj: Przejąć nocną zmianę").click()

    expect(open_column.get_by_role("heading", name="Przejąć nocną zmianę")).to_be_visible()
    expect(open_column).to_contain_text("Jedna przespana noc robi dużą różnicę.")
    expect(mock_page.get_by_text("Dodano zadanie: Przejąć nocną zmianę.")).to_be_visible()


def test_a_closed_group_offers_no_ideas(mock_page):
    open_as(mock_page, "partner", "/tasks")
    expect(h1(mock_page)).to_have_text("Zadania")
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'closed';")

    mock_page.reload()

    expect(h1(mock_page)).to_have_text("Zadania")
    expect(ideas(mock_page)).to_have_count(0)
