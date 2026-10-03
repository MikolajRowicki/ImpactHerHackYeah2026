import logging
from datetime import timedelta

import pytest
from django.db import transaction

from core import clock, mail
from core.models import MailLog

NOW = "2026-10-03T12:00:00+00:00"


def send(to="ola@example.com", kind="activation", **extra):
    return mail.send(kind, to=to, subject="Temat", body="Treść", **extra)


@pytest.fixture
def commit(db, django_capture_on_commit_callbacks):
    """Run `send` the way a request does: the callbacks run once the transaction commits."""

    def run(**kwargs):
        with django_capture_on_commit_callbacks(execute=True):
            return send(**kwargs)

    return run


def test_a_message_is_delivered_after_commit_to_the_given_address(commit, outbox):
    assert commit(user_id=7) is True
    assert [m.to for m in outbox] == [["ola@example.com"]]
    assert outbox[0].subject == "Temat"


def test_nothing_is_sent_until_the_transaction_commits(
    db, django_capture_on_commit_callbacks, outbox
):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        send()
    assert outbox == []
    assert len(callbacks) == 1


def test_a_rolled_back_transaction_sends_nothing_and_counts_nothing(db, outbox):
    with pytest.raises(RuntimeError), transaction.atomic():
        send()
        raise RuntimeError
    assert outbox == []
    assert MailLog.objects.count() == 0


def test_a_failing_backend_does_not_raise(commit, settings, outbox, caplog):
    settings.EMAIL_BACKEND = "tests.helpers.FailingEmailBackend"
    with caplog.at_level(logging.ERROR):
        assert commit(user_id=7) is True
    assert outbox == []
    assert "mail delivery failed" in caplog.text
    assert "user_id=7" in caplog.text


def test_the_log_never_holds_the_address_or_the_error_text(commit, settings, caplog):
    settings.EMAIL_BACKEND = "tests.helpers.FailingEmailBackend"
    with caplog.at_level(logging.DEBUG):
        commit(to="secret-address@example.com")
    assert "secret-address" not in caplog.text
    assert "ola@example.com" not in caplog.text
    assert "ConnectionRefusedError" in caplog.text


def test_a_second_message_within_a_minute_is_refused(commit, outbox, clock_at):
    clock_at(NOW)
    assert commit() is True
    clock_at(clock.now() + timedelta(seconds=30))
    assert commit() is False
    assert len(outbox) == 1
    clock_at(clock.now() + timedelta(seconds=31))
    assert commit() is True
    assert len(outbox) == 2


def test_three_messages_per_hour_per_address_and_kind(commit, outbox, clock_at):
    moment = clock_at(NOW)
    results = []
    for minute in (0, 2, 4, 6):
        clock_at(moment + timedelta(minutes=minute))
        results.append(commit())
    assert results == [True, True, True, False]
    # An hour after the first one, the address may be sent to again.
    clock_at(moment + timedelta(minutes=61))
    assert commit() is True
    assert len(outbox) == 4


def test_the_limits_are_per_address_and_kind(commit, outbox, clock_at):
    clock_at(NOW)
    assert commit(kind="activation") is True
    assert commit(kind="password_reset") is True
    assert commit(to="inna@example.com", kind="activation") is True
    assert len(outbox) == 3


def test_the_mailbox_has_a_daily_limit(commit, outbox, clock_at, caplog):
    moment = clock_at(NOW)
    for number in range(mail.PER_DAY):
        MailLog.objects.create(kind="x", key_hash=f"k{number}", created_at=moment)
    with caplog.at_level(logging.ERROR):
        assert commit(to="nowa@example.com") is False
    assert outbox == []
    assert "daily limit" in caplog.text
    # A day later the count has dropped again.
    clock_at(moment + timedelta(days=1, minutes=1))
    assert commit(to="nowa@example.com") is True


def test_limits_come_from_the_database_so_they_survive_a_restart(commit, outbox, clock_at):
    clock_at(NOW)
    assert commit() is True
    # A new process knows nothing but the database; here only the rows are left.
    assert MailLog.objects.filter(kind="activation").count() == 1
    assert commit() is False


def test_the_database_holds_a_hash_of_the_address(commit):
    commit(to="Ola@Example.com")
    log = MailLog.objects.get()
    assert log.key_hash == mail.address_key("ola@example.com")
    assert "ola" not in log.key_hash
    assert log.kind == "activation"
