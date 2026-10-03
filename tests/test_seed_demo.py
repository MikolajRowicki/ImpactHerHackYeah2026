from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.models import Group, Invitation, Observation, Task, User

from . import contract as c
from .factories import make_group, make_user

pytestmark = pytest.mark.django_db

PASSWORD = "demo-haslo-1"


@pytest.fixture
def seed(settings):
    settings.DEBUG = True

    def run(*args):
        out = StringIO()
        call_command("seed_demo", *args, stdout=out)
        return out.getvalue()

    return run


def example(name):
    return c.load_example(c.EXAMPLES_DIR / name)


def test_the_three_people_can_sign_in_and_annas_summary_needs_attention(seed, browser):
    seed()
    for email in ("anna@example.com", "piotr@example.com", "marta@example.com"):
        result = browser().call("login", body={"email": email, "password": PASSWORD})
        assert result.status == 200
    anna = browser()
    anna.call("login", body={"email": "anna@example.com", "password": PASSWORD})
    assert anna.call("get_summary")["trend"] == "needs_attention"
    assert anna.call("get_summary_extended")["help"] is not None


def test_the_people_match_the_contract_examples(seed, browser):
    seed()
    pairs = (
        ("anna@example.com", "get_me.200.json"),
        ("piotr@example.com", "get_me.200.partner.json"),
        ("marta@example.com", "get_me.200.supporter.json"),
    )
    for email, name in pairs:
        who = browser()
        me = who.call("login", body={"email": email, "password": PASSWORD}).body
        expected = example(name)
        assert (me["id"], me["email"], me["display_name"]) == (
            expected["id"],
            expected["email"],
            expected["display_name"],
        )
        assert me["membership"]["role"] == expected["membership"]["role"]


def test_the_data_covers_two_weeks_and_every_task_status(seed):
    seed()
    assert Group.objects.get().status == "active"
    assert Observation.objects.count() == 5
    assert set(Task.objects.values_list("status", flat=True)) == {"open", "claimed", "done"}
    assert Invitation.objects.filter(used_at__isnull=True, revoked_at__isnull=True).count() == 1


def test_running_twice_leaves_one_copy(seed):
    seed()
    first = (User.objects.count(), Group.objects.count(), Task.objects.count())
    seed()
    assert (User.objects.count(), Group.objects.count(), Task.objects.count()) == first == (3, 1, 4)


def test_other_data_is_not_touched(seed, browser):
    woman, partner, stranger = make_user("Ola"), make_user("Olek"), make_user("Ewa")
    other = make_group(woman=woman, partner=partner)
    seed()
    seed()
    assert User.objects.filter(pk__in=[woman.pk, partner.pk, stranger.pk]).count() == 3
    assert Group.objects.filter(pk=other.pk).exists()
    assert Group.objects.count() == 2
    assert User.objects.count() == 3 + 3


def test_it_prints_the_database_file(seed, settings):
    assert settings.DATABASES["default"]["NAME"] in seed()


def test_it_refuses_with_debug_off_and_changes_nothing(settings):
    settings.DEBUG = False
    out = StringIO()
    with pytest.raises(CommandError, match="DJANGO_DEBUG"):
        call_command("seed_demo", stdout=out)
    assert User.objects.count() == 0
    assert "Database:" in out.getvalue()


def test_the_flag_allows_it_with_debug_off(settings):
    settings.DEBUG = False
    call_command("seed_demo", "--allow-production", stdout=StringIO())
    assert User.objects.count() == 3


def test_the_clock_is_released_afterwards(seed):
    from core import clock

    seed()
    assert clock._frozen is None
