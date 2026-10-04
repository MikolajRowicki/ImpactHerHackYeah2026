import json
from pathlib import Path

from playwright.sync_api import expect

from .helpers import h1, nav, open_as

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"
WENT_OUT = "Czy w ostatnich dniach wyszła z domu na coś więcej niż zakupy?"
SAD = "Czy była ostatnio smutna albo płakała?"
ENJOYS = "Czy chętnie robi rzeczy, które zwykle lubi?"


def example(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def live_partner(page, sent):
    """Live mode with routed answers for a signed-in partner; records observation bodies."""
    answers = {
        "/api/v1/me": example("get_me.200.partner.json"),
        "/api/v1/me/memberships": {
            "items": [
                {"group_id": 1, "role": "partner", "group_status": "active", "woman_name": "Anna"}
            ]
        },
        "/api/v1/observations/questions": example("list_observation_questions.200.json"),
    }

    def answer(route):
        url = route.request.url
        if url.endswith("/api/v1/observations") and route.request.method == "POST":
            sent.append(route.request.post_data_json)
            route.fulfill(status=201, json=example("create_observation.201.json"))
            return
        for path, body in answers.items():
            if url.endswith(path):
                route.fulfill(status=200, json=body)
                return
        route.fulfill(status=404, json={"error": {"code": "not_found", "message": "Brak."}})

    page.route("**/api/v1/**", answer)
    page.goto(f"{page.base}?mock=0#/questions")
    expect(h1(page)).to_have_text("Jak ona się ma?")


def choose(page, question, label):
    page.get_by_role("group", name=question).get_by_label(label, exact=True).check()


def test_questions_are_shown_with_options_and_no_text_field(mock_page):
    open_as(mock_page, "supporter", "/questions")
    expect(h1(mock_page)).to_have_text("Jak ona się ma?")

    for question, labels in (
        (WENT_OUT, ["Tak", "Nie", "Nie wiem"]),
        (SAD, ["Tak", "Nie", "Nie wiem"]),
        (ENJOYS, ["Chętniej niż zwykle", "Tak jak zwykle", "Mniej chętnie niż zwykle"]),
    ):
        group = mock_page.get_by_role("group", name=question)
        expect(group.get_by_role("radio")).to_have_count(len(labels))
        for label in labels:
            expect(group.get_by_label(label, exact=True)).to_be_visible()
    expect(mock_page.locator("main textarea, main input[type=text]")).to_have_count(0)


def test_care_framing_note(mock_page):
    open_as(mock_page, "partner", "/questions")

    expect(
        mock_page.get_by_text("Twoich odpowiedzi nikt nie zobaczy pojedynczo ani z Twoim imieniem.")
    ).to_be_visible()


def test_partial_answers_send_only_the_answered_questions(mock_page):
    sent = []
    live_partner(mock_page, sent)

    choose(mock_page, WENT_OUT, "Nie")
    choose(mock_page, ENJOYS, "Mniej chętnie niż zwykle")
    mock_page.get_by_role("button", name="Wyślij odpowiedzi").click()

    expect(h1(mock_page)).to_have_text("Dziękujemy")
    assert sent == [
        {
            "answers": [
                {"question_id": "went_out", "value": "no"},
                {"question_id": "enjoys_things", "value": "less_than_usual"},
            ]
        }
    ]


def test_nothing_answered_asks_for_one_and_sends_nothing(mock_page):
    sent = []
    live_partner(mock_page, sent)

    mock_page.get_by_role("button", name="Wyślij odpowiedzi").click()

    expect(mock_page.get_by_role("alert")).to_have_text("Odpowiedz na co najmniej jedno pytanie.")
    expect(h1(mock_page)).to_have_text("Jak ona się ma?")
    assert sent == []


def test_answers_are_not_shown_back_after_the_thank_you(mock_page):
    open_as(mock_page, "partner", "/questions")
    choose(mock_page, SAD, "Tak")
    mock_page.get_by_role("button", name="Wyślij odpowiedzi").click()
    expect(h1(mock_page)).to_have_text("Dziękujemy")
    expect(h1(mock_page)).to_be_focused()
    expect(mock_page.get_by_text("Tak", exact=True)).to_have_count(0)

    nav(mock_page).get_by_role("link", name="Pytania").click()

    expect(h1(mock_page)).to_have_text("Jak ona się ma?")
    expect(mock_page.get_by_role("radio", checked=True)).to_have_count(0)


def test_loved_ones_summary_with_care_reminder_and_questions_call(mock_page):
    open_as(mock_page, "supporter")

    reminder = mock_page.get_by_role("complementary", name="Na dziś")
    expect(reminder).to_contain_text("Krótka wiadomość albo wspólny spacer")
    tasks = mock_page.get_by_role("region", name="Otwarte zadania")
    expect(tasks.get_by_text("Ugotować obiad")).to_be_visible()
    mock_page.get_by_role("link", name="Jak ona się ma?").click()
    expect(h1(mock_page)).to_have_text("Jak ona się ma?")
