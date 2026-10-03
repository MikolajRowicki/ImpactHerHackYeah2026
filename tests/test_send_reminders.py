import logging
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command

from core import clock, mail
from core.constants import TASK_CLAIMED
from core.models import CheckIn, MailLog, Observation, ReminderLog, Task

from .factories import make_circle, make_group, make_user

pytestmark = pytest.mark.django_db

NOON = "2026-10-03T12:00:00+02:00"
NAMES = ("Anna", "Piotr", "Marta")


@pytest.fixture
def run(django_capture_on_commit_callbacks):
    """Run the command. The test itself sits in a transaction, so mail is delivered on commit."""

    def go():
        out = StringIO()
        with django_capture_on_commit_callbacks(execute=True):
            call_command("send_reminders", stdout=out)
        return out.getvalue()

    return go


@pytest.fixture
def circle(clock_at):
    clock_at(NOON)
    return make_circle()


def recipients(outbox):
    return sorted(address for message in outbox for address in message.to)


def subjects_for(outbox, address):
    return [m.subject for m in outbox if address in m.to]


def test_everyone_with_something_due_gets_one_e_mail(run, circle, outbox):
    run()
    assert recipients(outbox) == ["anna@example.com", "marta@example.com", "piotr@example.com"]
    assert subjects_for(outbox, "anna@example.com") == ["MaydayMama: dzisiejszy wpis w dzienniku"]
    assert subjects_for(outbox, "piotr@example.com") == ["MaydayMama: dzisiejsza obserwacja"]
    assert ReminderLog.objects.filter(day=clock.today()).count() == 3


def test_the_second_run_on_the_same_day_sends_nothing(run, circle, outbox, clock_at):
    run()
    sent = len(outbox)
    # Even after the mail limits have forgotten the first run, the log still stops a second one.
    clock_at(clock.now() + timedelta(hours=3))
    run()
    assert len(outbox) == sent == 3
    assert ReminderLog.objects.count() == 3


def test_the_next_day_sends_again(run, circle, outbox, clock_at):
    run()
    clock_at(clock.now() + timedelta(days=1))
    run()
    assert len(outbox) == 6
    assert ReminderLog.objects.count() == 6


def test_a_reminder_that_is_no_longer_due_is_not_sent(run, circle, outbox):
    CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood="good",
        sleep="enough",
        anxiety="none",
    )
    run()
    assert "anna@example.com" not in recipients(outbox)


def test_a_person_who_gave_an_observation_gets_no_observation_reminder(run, circle, outbox):
    Observation.objects.create(group=circle.group, author=circle.membership(circle.piotr))
    run()
    assert "piotr@example.com" not in recipients(outbox)
    assert "marta@example.com" in recipients(outbox)


def test_a_task_in_progress_gets_one_e_mail_however_many_tasks(run, circle, outbox):
    Observation.objects.create(group=circle.group, author=circle.membership(circle.marta))
    for title in ("a", "b"):
        Task.objects.create(
            group=circle.group,
            title=title,
            created_by=circle.piotr,
            status=TASK_CLAIMED,
            claimed_by=circle.marta,
            claimed_at=clock.now(),
        )
    run()
    assert subjects_for(outbox, "marta@example.com") == ["MaydayMama: zadanie w toku"]
    assert ReminderLog.objects.get(user=circle.marta).kind == "task_in_progress"


def test_a_person_with_two_kinds_gets_two_e_mails(run, circle, outbox):
    Task.objects.create(
        group=circle.group,
        title="a",
        created_by=circle.anna,
        status=TASK_CLAIMED,
        claimed_by=circle.marta,
        claimed_at=clock.now(),
    )
    run()
    assert subjects_for(outbox, "marta@example.com") == [
        "MaydayMama: dzisiejsza obserwacja",
        "MaydayMama: zadanie w toku",
    ]


def test_a_person_who_turned_reminders_off_gets_nothing(run, circle, outbox):
    circle.piotr.email_reminders = False
    circle.piotr.save()
    run()
    assert "piotr@example.com" not in recipients(outbox)
    assert not ReminderLog.objects.filter(user=circle.piotr).exists()
    assert len(outbox) == 2


def test_turning_reminders_off_through_the_preferences_stops_the_e_mail(
    run, circle, outbox, browser
):
    saved = browser(circle.marta).call("update_preferences", body={"email_reminders": False})
    assert saved.status == 200
    run()
    assert "marta@example.com" not in recipients(outbox)


def test_an_inactive_account_is_skipped(run, circle, outbox):
    circle.marta.is_active = False
    circle.marta.save()
    run()
    assert "marta@example.com" not in recipients(outbox)


@pytest.mark.parametrize("status", ["pending", "closed"])
def test_a_group_that_is_not_active_is_skipped(run, clock_at, outbox, status):
    clock_at(NOON)
    make_circle(status=status)
    run()
    assert outbox == []
    assert ReminderLog.objects.count() == 0


def test_a_person_without_a_group_is_skipped(run, clock_at, outbox):
    clock_at(NOON)
    make_user("Sama")
    run()
    assert outbox == []


def test_a_group_without_a_woman_still_reminds_the_loved_ones(run, clock_at, outbox):
    clock_at(NOON)
    make_group(partner=make_user("Piotr"))
    run()
    assert recipients(outbox) == ["piotr@example.com"]


def test_the_e_mail_is_general_polish_text_with_the_link(run, circle, outbox, settings):
    settings.APP_BASE_URL = "https://maydaymama.example/"
    CheckIn.objects.create(
        group=circle.group,
        author=circle.membership(circle.anna),
        mood="very_low",
        sleep="almost_none",
        anxiety="strong",
        created_at=clock.now() - timedelta(days=1),
    )
    Task.objects.create(
        group=circle.group,
        title="Tajny tytuł zadania",
        details="Tajne szczegóły",
        created_by=circle.piotr,
        status=TASK_CLAIMED,
        claimed_by=circle.piotr,
        claimed_at=clock.now(),
    )
    run()
    assert outbox
    for message in outbox:
        text = f"{message.subject}\n{message.body}"
        assert "https://maydaymama.example/" in message.body
        for name in NAMES:
            assert name not in text
        for secret in ("Tajny", "Tajne", "very_low", "almost_none", "strong", "trend"):
            assert secret not in text
        assert "Cześć" in message.body
        assert message.from_email


def test_the_e_mail_goes_to_the_owner_only(run, circle, outbox):
    run()
    assert all(len(message.to) == 1 and not message.cc and not message.bcc for message in outbox)


def test_the_command_prints_counts_and_never_an_address(run, circle, outbox):
    printed = run()
    assert printed.strip() == "send_reminders: sent=3 already_sent=0 refused=0"
    assert "@" not in printed
    again = run()
    assert again.strip() == "send_reminders: sent=0 already_sent=3 refused=0"


def test_console_mode_writes_the_message_and_succeeds(
    circle, settings, capsys, django_capture_on_commit_callbacks
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    with django_capture_on_commit_callbacks(execute=True):
        call_command("send_reminders", stdout=StringIO())
    printed = capsys.readouterr().out
    assert "Subject: MaydayMama: dzisiejszy wpis w dzienniku" in printed
    assert ReminderLog.objects.count() == 3


def test_a_failing_mail_server_does_not_fail_the_command(run, circle, settings, caplog):
    settings.EMAIL_BACKEND = "tests.helpers.FailingEmailBackend"
    with caplog.at_level(logging.DEBUG):
        printed = run()
    assert "sent=3" in printed
    assert "mail delivery failed" in caplog.text
    # Neither the logs nor the output hold an address.
    assert "@example.com" not in caplog.text
    assert "@" not in printed


def test_every_reminder_goes_through_the_shared_mail_service(run, circle, outbox):
    run()
    kinds = sorted(MailLog.objects.values_list("kind", flat=True))
    assert kinds == [
        "reminder_check_in_due",
        "reminder_observation_due",
        "reminder_observation_due",
    ]
    assert MailLog.objects.filter(
        kind="reminder_check_in_due", key_hash=mail.address_key("anna@example.com")
    ).exists()


def test_the_daily_limit_of_the_mailbox_applies(run, circle, outbox, caplog):
    for number in range(mail.PER_DAY):
        MailLog.objects.create(kind="other", key_hash=f"k{number}", created_at=clock.now())
    with caplog.at_level(logging.WARNING):
        printed = run()
    assert outbox == []
    assert printed.strip() == "send_reminders: sent=0 already_sent=0 refused=3"
    assert "daily limit" in caplog.text


def test_a_refused_reminder_is_not_marked_as_sent_so_a_later_run_can_retry(
    run, circle, outbox, clock_at
):
    moment = clock.now()
    for number in range(mail.PER_DAY):
        MailLog.objects.create(kind="other", key_hash=f"k{number}", created_at=moment)
    run()
    assert ReminderLog.objects.count() == 0
    # The mailbox has room again later the same day, and the reminders go out.
    MailLog.objects.filter(kind="other").delete()
    clock_at(moment + timedelta(hours=1))
    run()
    assert len(outbox) == 3
    assert ReminderLog.objects.count() == 3


def test_an_existing_log_row_blocks_a_second_send_even_with_free_mail_limits(run, circle, outbox):
    ReminderLog.objects.create(user=circle.anna, kind="check_in_due", day=clock.today())
    run()
    assert "anna@example.com" not in recipients(outbox)


def test_the_log_is_per_kind_and_day(run, circle, outbox):
    other_day = clock.today() - timedelta(days=1)
    ReminderLog.objects.create(user=circle.anna, kind="check_in_due", day=other_day)
    run()
    assert "anna@example.com" in recipients(outbox)


def test_the_day_follows_warsaw_time(run, circle, outbox, clock_at):
    # 23:30 UTC on the 3rd is already the 4th in Warsaw, so the log day is the 4th.
    clock_at("2026-10-03T23:30:00+00:00")
    run()
    assert set(ReminderLog.objects.values_list("day", flat=True)) == {clock.today()}
    assert clock.today().isoformat() == "2026-10-04"
