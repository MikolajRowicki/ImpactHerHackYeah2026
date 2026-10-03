import re

from playwright.sync_api import expect

from .helpers import change_mock_state, h1, open_as


def column(page, name):
    return page.get_by_role("region", name=name, exact=True)


def task(page, state, title):
    return column(page, state).get_by_role("listitem").filter(has_text=title)


def open_tasks(page, perspective="partner"):
    open_as(page, perspective, "/tasks")
    expect(h1(page)).to_have_text("Zadania")
    expect(column(page, "Do wzięcia")).to_be_visible()


def test_grouped_list_shows_who_added_and_who_took(mock_page):
    open_tasks(mock_page, "woman")

    expect(task(mock_page, "Do wzięcia", "Ugotować obiad")).to_contain_text("Dodane przez: Piotr")
    taken = task(mock_page, "W toku", "Zrobić zakupy")
    expect(taken).to_contain_text("Zajmuje się: Marta")
    done = task(mock_page, "Zrobione", "Wyprowadzić psa")
    expect(done).to_contain_text("Zrobione przez: Piotr")


def test_empty_list_invites_the_first_task(mock_page):
    open_tasks(mock_page)
    change_mock_state(mock_page, "s.tasks = [];")

    mock_page.reload()

    expect(mock_page.get_by_text("Nie ma jeszcze zadań. Dodaj pierwsze")).to_be_visible()


def test_adding_a_task_puts_it_under_open(mock_page):
    open_tasks(mock_page)

    mock_page.get_by_label("Co trzeba zrobić?").fill("Odebrać leki z apteki")
    mock_page.get_by_label("Szczegóły (nieobowiązkowo)").fill("Recepta jest w szufladzie.")
    mock_page.get_by_role("button", name="Dodaj zadanie").click()

    added = task(mock_page, "Do wzięcia", "Odebrać leki z apteki")
    expect(added).to_contain_text("Recepta jest w szufladzie.")
    expect(added).to_contain_text("Dodane przez: Ty")
    expect(mock_page.get_by_label("Co trzeba zrobić?")).to_have_value("")


def test_missing_title_is_asked_for_and_nothing_is_sent(mock_page):
    open_tasks(mock_page)

    mock_page.get_by_role("button", name="Dodaj zadanie").click()

    title = mock_page.get_by_label("Co trzeba zrobić?")
    expect(title).to_have_attribute("aria-invalid", "true")
    expect(mock_page.get_by_text("Wpisz krótki tytuł zadania.")).to_be_visible()
    expect(column(mock_page, "Do wzięcia").get_by_role("listitem")).to_have_count(1)


def test_title_and_details_have_length_limits(mock_page):
    open_tasks(mock_page)

    expect(mock_page.get_by_label("Co trzeba zrobić?")).to_have_attribute("maxlength", "120")
    expect(mock_page.get_by_label("Szczegóły (nieobowiązkowo)")).to_have_attribute(
        "maxlength", "500"
    )


def test_taking_moves_the_task_under_taken_with_the_name(mock_page):
    open_tasks(mock_page, "partner")

    task(mock_page, "Do wzięcia", "Ugotować obiad").get_by_role("button", name="Biorę to").click()

    taken = task(mock_page, "W toku", "Ugotować obiad")
    expect(taken).to_contain_text("Zajmuje się: Ty")
    open_as(mock_page, "supporter", "/tasks")
    expect(task(mock_page, "W toku", "Ugotować obiad")).to_contain_text("Zajmuje się: Piotr")


def test_finishing_moves_the_task_under_done(mock_page):
    open_tasks(mock_page, "supporter")

    task(mock_page, "W toku", "Zrobić zakupy").get_by_role(
        "button", name="Oznacz jako zrobione"
    ).click()

    expect(task(mock_page, "Zrobione", "Zrobić zakupy")).to_contain_text("Zrobione przez: Ty")
    expect(column(mock_page, "W toku").get_by_role("listitem")).to_have_count(0)


def test_no_done_control_on_someone_elses_task(mock_page):
    open_tasks(mock_page, "partner")

    taken = task(mock_page, "W toku", "Zrobić zakupy")
    expect(taken).to_be_visible()
    expect(taken.get_by_role("button")).to_have_count(0)


def test_conflict_shows_the_message_and_reloads_the_list(mock_page):
    open_tasks(mock_page, "partner")
    # Marta takes the task on her phone while Piotr still sees it as open.
    change_mock_state(
        mock_page,
        """const t = s.tasks.find((x) => x.id === 5);
        t.status = "claimed";
        t.claimed_by = { id: 3, display_name: "Marta" };""",
    )

    task(mock_page, "Do wzięcia", "Ugotować obiad").get_by_role("button", name="Biorę to").click()

    expect(mock_page.get_by_role("alert")).to_have_text("Ktoś już zajął się tym zadaniem.")
    expect(task(mock_page, "W toku", "Ugotować obiad")).to_contain_text("Zajmuje się: Marta")


def test_closed_group_answer_is_shown_next_to_the_action(mock_page):
    open_tasks(mock_page, "partner")
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'closed';")

    mock_page.get_by_label("Co trzeba zrobić?").fill("Posprzątać kuchnię")
    mock_page.get_by_role("button", name="Dodaj zadanie").click()

    form = mock_page.get_by_role("region", name="Dodaj zadanie")
    expect(form.get_by_role("alert")).to_contain_text("Ta grupa została zamknięta")
    expect(mock_page.get_by_label("Co trzeba zrobić?")).to_have_value("Posprzątać kuchnię")
    expect(task(mock_page, "Do wzięcia", "Ugotować obiad")).to_be_visible()


def test_closed_group_offers_no_task_actions(mock_page):
    open_tasks(mock_page, "woman")
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'closed';")
    mock_page.get_by_role("region", name="Tryb demonstracyjny").get_by_label(
        "Pokaż jako"
    ).select_option(label="Partner (Piotr)")

    mock_page.goto(f"{mock_page.base}#/tasks")

    expect(mock_page.get_by_text("Grupa jest zamknięta, więc nie można")).to_be_visible()
    expect(mock_page.get_by_role("main").get_by_role("button")).to_have_count(0)


def test_no_counts_or_ranking_per_person(mock_page):
    open_tasks(mock_page, "woman")

    expect(column(mock_page, "Zrobione")).to_be_visible()
    text = " ".join(
        column(mock_page, name).inner_text() for name in ("Do wzięcia", "W toku", "Zrobione")
    )
    assert not re.search(r"\d", text), text
    for word in ("ranking", "punkt", "najwięcej", "wynik"):
        assert word not in text.lower()


def test_task_taken_in_the_demo_survives_a_reload_without_api_calls(mock_page):
    open_tasks(mock_page, "supporter")

    task(mock_page, "Do wzięcia", "Ugotować obiad").get_by_role("button", name="Biorę to").click()
    expect(task(mock_page, "W toku", "Ugotować obiad")).to_contain_text("Zajmuje się: Ty")
    mock_page.reload()

    expect(task(mock_page, "W toku", "Ugotować obiad")).to_contain_text("Zajmuje się: Ty")
    assert mock_page.api_requests == []


def test_reset_brings_back_the_example_tasks(mock_page):
    open_tasks(mock_page, "supporter")
    task(mock_page, "Do wzięcia", "Ugotować obiad").get_by_role("button", name="Biorę to").click()
    expect(task(mock_page, "W toku", "Ugotować obiad")).to_be_visible()

    mock_page.get_by_role("button", name="Zacznij demo od nowa").click()
    expect(h1(mock_page)).to_have_text("Cześć, Marta")
    mock_page.goto(f"{mock_page.base}#/tasks")

    expect(task(mock_page, "Do wzięcia", "Ugotować obiad")).to_be_visible()


def test_focus_stays_on_the_task_after_taking_it(mock_page):
    open_tasks(mock_page, "partner")

    task(mock_page, "Do wzięcia", "Ugotować obiad").get_by_role("button", name="Biorę to").click()

    expect(task(mock_page, "W toku", "Ugotować obiad")).to_be_focused()


def test_the_person_who_took_a_task_can_hand_it_back(mock_page):
    open_tasks(mock_page, "supporter")

    task(mock_page, "W toku", "Zrobić zakupy").get_by_role("button", name="Oddaj zadanie").click()

    expect(task(mock_page, "Do wzięcia", "Zrobić zakupy")).to_be_visible()
    expect(column(mock_page, "W toku").get_by_role("listitem")).to_have_count(0)
