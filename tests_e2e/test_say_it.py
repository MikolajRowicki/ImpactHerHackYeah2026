"""The mother's "say it for me": form, suggestion, copy, crisis answer, labels and access."""

import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .helpers import h1, live, nav, open_as
from .test_contrast_layout import CONTRAST

EXAMPLES = Path(__file__).resolve().parents[1] / "contracts" / "examples"
SAY_IT = "POST /api/v1/ai/say-it-for-me"
TEXT = "Nie daję rady z nocnym karmieniem i chcę, żeby ktoś przejął jedną noc."


def example(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def answer(message, source="groq"):
    return {"crisis": False, "message": message, "help": None, "source": source, "sources": []}


def open_live(page, say_it_answer=None):
    answers = {"GET /api/v1/me": (200, example("get_me.200.json"))}
    if say_it_answer is not None:
        answers[SAY_IT] = say_it_answer
    calls = live(page, answers, "/say-it")
    expect(h1(page)).to_have_text("Powiedz to za mnie")
    return answers, calls


def requests_to_say_it(page):
    sent = []
    page.on(
        "request",
        lambda r: sent.append(r.post_data_json) if r.url.endswith("/ai/say-it-for-me") else None,
    )
    return sent


def text_field(page):
    return page.get_by_label("Co chcesz powiedzieć?")


def send(page):
    page.get_by_role("button", name="Przygotuj wiadomość").click()


def message_field(page):
    return page.get_by_label("Twoja wiadomość (możesz ją poprawić)")


# Entry and access


def test_the_mothers_start_has_a_card_that_opens_say_it(mock_page):
    open_as(mock_page, "woman")
    mock_page.get_by_role("link", name="Powiedz to za mnie").click()
    expect(h1(mock_page)).to_have_text("Powiedz to za mnie")
    expect(mock_page.get_by_text("Twój tekst nie jest nigdzie zapisywany.")).to_be_visible()


def test_the_navigation_gets_no_new_item(mock_page):
    open_as(mock_page, "woman")
    expect(nav(mock_page).get_by_role("link")).to_have_text(
        ["Start", "Mój dzień", "Zadania", "Grupa", "Wiedza", "Pomoc"]
    )


def test_a_partner_sees_that_say_it_belongs_to_the_mother(mock_page):
    open_as(mock_page, "partner", "/say-it")
    expect(mock_page.get_by_text("To miejsce należy do mamy.")).to_be_visible()
    expect(mock_page.get_by_label("Co chcesz powiedzieć?")).to_have_count(0)


def test_a_person_without_a_group_sees_that_a_group_is_needed(mock_page):
    open_as(mock_page, "no_group", "/say-it")
    expect(mock_page.get_by_text("To miejsce otworzy się, gdy dołączysz do grupy")).to_be_visible()


# The suggestion


def test_a_sample_suggestion_can_be_copied_and_edited_without_any_request(mock_page):
    mock_page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    open_as(mock_page, "woman", "/say-it")
    text_field(mock_page).fill(TEXT)
    mock_page.get_by_role("group", name="Do kogo?").get_by_label("Do bliskich osób").check()
    mock_page.get_by_role("group", name="Jakim tonem?").get_by_label("Wprost").check()
    send(mock_page)

    expect(mock_page.get_by_role("heading", name="Propozycja wiadomości")).to_be_focused()
    expect(message_field(mock_page)).to_have_value(
        "Potrzebuję wsparcia i wolę powiedzieć to jasno. Pomóżcie mi, proszę, w konkretnych "
        "sprawach: zakupy, posiłek albo godzina odpoczynku."
    )
    expect(mock_page.get_by_text("Tekst przykładowy")).to_be_visible()

    mock_page.get_by_role("button", name="Kopiuj").click()
    expect(mock_page.get_by_text("Skopiowano.")).to_be_visible()
    copied = mock_page.evaluate("navigator.clipboard.readText()")
    assert copied == message_field(mock_page).input_value()

    message_field(mock_page).fill("Moja poprawiona wiadomość.")
    mock_page.get_by_role("button", name="Kopiuj").click()
    assert mock_page.evaluate("navigator.clipboard.readText()") == "Moja poprawiona wiadomość."
    assert mock_page.api_requests == []


def test_an_empty_text_shows_a_message_and_sends_nothing(mock_page):
    _, calls = open_live(mock_page, (200, answer("Nie powinno przyjść.")))
    text_field(mock_page).fill("   ")
    send(mock_page)
    expect(mock_page.get_by_text("Napisz, co chcesz przekazać.")).to_be_visible()
    expect(text_field(mock_page)).to_be_focused()
    assert SAY_IT not in calls


def test_the_counter_follows_the_text_and_the_field_takes_at_most_500(mock_page):
    open_as(mock_page, "woman", "/say-it")
    expect(mock_page.get_by_text("0 / 500 znaków")).to_be_visible()
    text_field(mock_page).fill("Cześć")
    expect(mock_page.get_by_text("5 / 500 znaków")).to_be_visible()

    text_field(mock_page).fill("a" * 498)
    text_field(mock_page).press_sequentially("bcdef")
    assert len(text_field(mock_page).input_value()) == 500
    expect(mock_page.get_by_text("500 / 500 znaków")).to_be_visible()


def test_another_suggestion_sends_the_same_text_recipient_and_tone_again(mock_page):
    answers, _ = open_live(mock_page, (200, answer("Pierwsza propozycja.")))
    sent = requests_to_say_it(mock_page)
    text_field(mock_page).fill(TEXT)
    mock_page.get_by_role("group", name="Jakim tonem?").get_by_label("Wprost").check()
    send(mock_page)
    expect(message_field(mock_page)).to_have_value("Pierwsza propozycja.")

    answers[SAY_IT] = (200, answer("Druga propozycja."))
    mock_page.get_by_role("button", name="Inna propozycja").click()
    expect(message_field(mock_page)).to_have_value("Druga propozycja.")
    assert len(sent) == 2
    assert sent[0] == sent[1] == {"text": TEXT, "recipient": "partner", "tone": "direct"}


def test_her_text_is_gone_after_leaving_and_is_in_no_browser_storage(mock_page):
    secret = "Sekretne zdanie ZQX-5521 o tym, jak mi ciężko."
    open_as(mock_page, "woman", "/say-it")
    text_field(mock_page).fill(secret)
    send(mock_page)
    expect(message_field(mock_page)).to_be_visible()

    mock_page.goto(f"{mock_page.base}#/")
    expect(h1(mock_page)).to_have_text("Cześć, Anna")
    mock_page.goto(f"{mock_page.base}#/say-it")
    expect(text_field(mock_page)).to_have_value("")
    stored = mock_page.evaluate(
        "JSON.stringify([Object.entries(sessionStorage), Object.entries(localStorage)])"
    )
    assert "ZQX-5521" not in stored


def test_a_failure_keeps_her_text_and_offers_to_try_again(mock_page):
    failure = (500, {"error": {"code": "unknown", "message": "Błąd."}})
    answers, _ = open_live(mock_page, failure)
    text_field(mock_page).fill(TEXT)
    send(mock_page)
    expect(mock_page.get_by_text("Nie udało się przygotować wiadomości.")).to_be_visible()
    expect(text_field(mock_page)).to_have_value(TEXT)

    answers[SAY_IT] = (200, answer("Teraz się udało."))
    mock_page.get_by_role("button", name="Spróbuj ponownie").click()
    expect(message_field(mock_page)).to_have_value("Teraz się udało.")


def test_a_second_press_sends_nothing_while_the_answer_is_on_its_way(mock_page):
    open_live(mock_page)
    sent = requests_to_say_it(mock_page)
    waiting = []
    mock_page.route("**/api/v1/ai/say-it-for-me", lambda route: waiting.append(route))
    text_field(mock_page).fill(TEXT)
    button = mock_page.get_by_role("button", name="Przygotuj wiadomość")
    button.click()

    busy = mock_page.locator(".say-it-form button[type=submit]")
    expect(busy).to_be_disabled()
    expect(busy).to_have_text("Przygotowuję…")
    busy.dispatch_event("click")
    mock_page.locator(".say-it-form").evaluate("form => form.requestSubmit()")

    waiting[0].fulfill(status=200, json=answer("Gotowe."))
    expect(message_field(mock_page)).to_have_value("Gotowe.")
    expect(busy).to_have_text("Przygotuj wiadomość")
    assert len(sent) == 1


# Labels and the crisis answer


@pytest.mark.parametrize(
    ("source", "label"),
    [("groq", "Przygotowane z pomocą AI"), ("mock", "Tekst przykładowy"), ("rules", None)],
)
def test_the_label_says_where_the_text_came_from(mock_page, source, label):
    open_live(mock_page, (200, answer("Wiadomość.", source)))
    text_field(mock_page).fill(TEXT)
    send(mock_page)
    expect(message_field(mock_page)).to_have_value("Wiadomość.")
    labels = mock_page.locator(".origin-label")
    if label:
        expect(labels).to_have_text(label)
    else:
        expect(labels).to_have_count(0)


def test_a_crisis_answer_shows_the_lines_and_no_message(mock_page):
    open_as(mock_page, "woman", "/say-it")
    text_field(mock_page).fill("Dziś znowu płakałam. Nie chcę żyć.")
    send(mock_page)

    expect(mock_page.get_by_role("heading", name="Nie musisz być z tym sama")).to_be_focused()
    lines = mock_page.locator(".crisis-lines")
    expect(lines.get_by_role("link", name="116 123")).to_have_attribute("href", "tel:116123")
    expect(lines.get_by_role("link", name="800 70 2222")).to_be_visible()
    help_link = mock_page.get_by_role("link", name="Zobacz wszystkie miejsca pomocy")
    expect(help_link).to_have_attribute("href", "#/help")
    expect(mock_page.get_by_role("button", name="Kopiuj")).to_have_count(0)
    expect(message_field(mock_page)).to_have_count(0)


def test_the_label_and_the_counter_are_readable_in_both_themes(mock_page):
    for scheme in ("light", "dark"):
        mock_page.emulate_media(color_scheme=scheme)
        open_as(mock_page, "woman", "/say-it")
        text_field(mock_page).fill(TEXT)
        send(mock_page)
        expect(mock_page.locator(".origin-label")).to_be_visible()
        assert mock_page.evaluate(CONTRAST, [".origin-label", "color"]) >= 4.5
        assert mock_page.evaluate(CONTRAST, [".say-it__counter", "color"]) >= 4.5
