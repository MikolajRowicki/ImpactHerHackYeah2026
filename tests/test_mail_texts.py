import re

import pytest

from core.content import mail_texts

from .factories import make_circle, make_user

LINK = "https://mayday.example.org/#/activate/abc123"

BUILDERS = {
    "activation": mail_texts.activation,
    "password_reset": mail_texts.password_reset,
    "account_exists": mail_texts.account_exists,
}
VALIDITY = {"activation": "3 dni", "password_reset": "1 godzina", "account_exists": "1 godzina"}

# Words that would mean a group, another person or health information in an account message.
FORBIDDEN = (
    "grup",
    "krąg",
    "partner",
    "opiekun",
    "depresj",
    "nastrój",
    "nastroj",
    "trend",
    "objaw",
    "sen ",
    "lęk",
    "samopoczuci",
    "Anna",
    "Piotr",
    "Marta",
)


@pytest.mark.parametrize("kind", BUILDERS)
def test_a_message_holds_the_link_how_long_it_works_and_a_note_to_ignore_it(kind):
    subject, body = BUILDERS[kind](LINK)
    assert subject
    assert LINK in body
    assert VALIDITY[kind] in body
    assert "zignoruj" in body


@pytest.mark.parametrize("kind", BUILDERS)
def test_a_message_is_in_polish(kind):
    subject, body = BUILDERS[kind](LINK)
    assert re.search(r"[ąćęłńóśźż]", subject + body)
    assert "Link działa" in body
    assert "Click" not in body


@pytest.mark.parametrize("kind", BUILDERS)
def test_a_message_holds_no_group_no_member_and_no_health_words(kind):
    subject, body = BUILDERS[kind](LINK)
    text = (subject + " " + body).lower()
    for word in FORBIDDEN:
        assert word.lower() not in text, word


def test_a_sent_message_names_no_group_even_when_the_person_belongs_to_one(api, outbox):
    circle = make_circle()
    make_user("Ola", email="ola@example.com", active=False)
    api.call("resend_activation", body={"email": "ola@example.com"})
    api.call("request_password_reset", body={"email": circle.anna.email})
    assert len(outbox) == 2
    for message in outbox:
        text = (message.subject + " " + message.body).lower()
        for word in FORBIDDEN:
            assert word.lower() not in text, (message.subject, word)


def test_the_mail_does_not_repeat_the_name_or_the_address(api, outbox):
    make_user("Ola", email="ola@example.com", active=False)
    api.call("resend_activation", body={"email": "ola@example.com"})
    assert "Ola" not in outbox[0].body
    assert "ola@example.com" not in outbox[0].body
    assert outbox[0].subject == "Potwierdź swoje konto w MaydayMama"
