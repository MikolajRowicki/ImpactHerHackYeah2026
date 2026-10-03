from playwright.sync_api import expect

from .helpers import change_mock_state, h1, open_as

MOOD = "Jak się dziś czujesz?"
SLEEP = "Jak Ci się spało?"
ANXIETY = "Czy coś Cię dziś niepokoi?"


def choose(page, legend, label):
    page.get_by_role("group", name=legend).get_by_label(label, exact=True).check()


def entries(page):
    return page.get_by_role("region", name="Moje wpisy").get_by_role("listitem")


def open_check_in(page):
    open_as(page, "woman", "/check-in")
    expect(h1(page)).to_have_text("Mój dzień")
    expect(entries(page)).to_have_count(3)


def test_suggestions_on_her_start_show_their_durations(mock_page):
    open_as(mock_page, "woman")
    care = mock_page.get_by_role("region", name="Chwila dla siebie")

    expect(care.get_by_role("listitem")).to_have_count(4)
    for title, minutes in (
        ("Spokojny oddech", "3 min"),
        ("Rozluźnij ramiona", "5 min"),
        ("Krótka medytacja", "10 min"),
        ("Spacer wokół bloku", "15 min"),
    ):
        item = care.get_by_role("listitem").filter(has_text=title)
        expect(item).to_contain_text(minutes)
    expect(care.get_by_text("Wdech przez nos na cztery")).to_be_visible()


def test_mothers_start_has_summary_check_in_call_and_open_tasks(mock_page):
    open_as(mock_page, "woman")

    expect(mock_page.get_by_role("region", name="Ogólny obraz")).to_be_visible()
    tasks = mock_page.get_by_role("region", name="Otwarte zadania bliskich")
    expect(tasks.get_by_text("Ugotować obiad")).to_be_visible()
    expect(tasks.get_by_text("Zrobić zakupy")).to_have_count(0)
    mock_page.get_by_role("link", name="Jak się dziś czujesz?").click()
    expect(h1(mock_page)).to_have_text("Mój dzień")


def test_check_in_choices_are_words_with_labels(mock_page):
    open_check_in(mock_page)

    for legend, labels in (
        (MOOD, ["Dobrze", "W porządku", "Raczej słabo", "Bardzo ciężko"]),
        (SLEEP, ["Wystarczająco", "Mało", "Prawie wcale"]),
        (ANXIETY, ["Raczej nie", "Trochę", "Bardzo"]),
    ):
        group = mock_page.get_by_role("group", name=legend)
        expect(group.get_by_role("radio")).to_have_count(len(labels))
        for label in labels:
            expect(group.get_by_label(label, exact=True)).to_be_visible()
    form_text = mock_page.locator("form").inner_text()
    assert not any(ch.isdigit() for ch in form_text), form_text


def test_privacy_note_says_only_she_sees_her_entries(mock_page):
    open_check_in(mock_page)

    expect(mock_page.get_by_text("Te wpisy widzisz tylko Ty.")).to_be_visible()


def test_saving_a_check_in_confirms_warmly_and_tops_the_history(mock_page):
    open_check_in(mock_page)

    choose(mock_page, MOOD, "Bardzo ciężko")
    choose(mock_page, SLEEP, "Prawie wcale")
    choose(mock_page, ANXIETY, "Bardzo")
    mock_page.get_by_role("button", name="Zapisz wpis").click()

    expect(mock_page.get_by_text("Dziękujemy, że się zatrzymałaś.")).to_be_visible()
    expect(entries(mock_page)).to_have_count(4)
    newest = entries(mock_page).first
    expect(newest).to_contain_text("Bardzo ciężko")
    expect(newest).to_contain_text("Prawie wcale")
    expect(newest).to_contain_text("Bardzo")

    mock_page.reload()
    expect(entries(mock_page)).to_have_count(4)


def test_missing_choice_is_asked_for_and_nothing_is_sent(mock_page):
    open_check_in(mock_page)

    choose(mock_page, MOOD, "Dobrze")
    choose(mock_page, SLEEP, "Mało")
    mock_page.get_by_role("button", name="Zapisz wpis").click()

    anxiety = mock_page.get_by_role("group", name=ANXIETY)
    expect(anxiety.get_by_text("Wybierz jedną z odpowiedzi.")).to_be_visible()
    expect(mock_page.get_by_role("group", name=MOOD).get_by_text("Wybierz jedną")).to_have_count(0)
    mock_page.reload()
    expect(entries(mock_page)).to_have_count(3)


def test_pending_group_answer_keeps_her_choices(mock_page):
    open_check_in(mock_page)
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'pending';")

    choose(mock_page, MOOD, "W porządku")
    choose(mock_page, SLEEP, "Wystarczająco")
    choose(mock_page, ANXIETY, "Trochę")
    mock_page.get_by_role("button", name="Zapisz wpis").click()

    expect(mock_page.get_by_role("alert")).to_have_text(
        "Grupa zacznie działać, gdy właścicielka przyjmie zaproszenie."
    )
    expect(mock_page.get_by_role("group", name=MOOD).get_by_label("W porządku")).to_be_checked()
    expect(mock_page.get_by_role("group", name=ANXIETY).get_by_label("Trochę")).to_be_checked()


def test_history_is_in_words_newest_first_without_charts(mock_page):
    open_check_in(mock_page)

    first, second, third = (entries(mock_page).nth(i) for i in range(3))
    expect(first).to_contain_text("3 października")
    expect(first).to_contain_text("Raczej słabo")
    expect(first).to_contain_text("Mało")
    expect(first).to_contain_text("Trochę")
    expect(second).to_contain_text("2 października")
    expect(third).to_contain_text("1 października")
    expect(third).to_contain_text("Wystarczająco")
    history = mock_page.get_by_role("region", name="Moje wpisy")
    expect(history.locator("canvas, svg, progress, meter")).to_have_count(0)


def test_no_entries_yet_invites_the_first_one(mock_page):
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    change_mock_state(mock_page, "s.checkIns = [];")

    mock_page.goto(f"{mock_page.base}#/check-in")

    expect(mock_page.get_by_text("Nie masz jeszcze wpisów.")).to_be_visible()


def test_closed_group_keeps_history_but_offers_no_form(mock_page):
    open_as(mock_page, "woman")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    change_mock_state(mock_page, "s.groups.find((g) => g.id === 1).status = 'closed';")
    notice = mock_page.get_by_role("region", name="Tryb demonstracyjny")
    notice.get_by_label("Pokaż jako").select_option(label="Mama (Anna)")

    mock_page.goto(f"{mock_page.base}#/check-in")

    expect(mock_page.get_by_text("Grupa jest zamknięta, więc nie dodasz")).to_be_visible()
    expect(mock_page.get_by_role("button", name="Zapisz wpis")).to_have_count(0)
    expect(entries(mock_page)).to_have_count(3)
