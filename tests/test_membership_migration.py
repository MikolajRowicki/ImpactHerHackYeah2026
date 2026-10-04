"""The migration that lets a person belong to many groups goes forward and back (spec:
group-membership, "Group integrity in the database")."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import IntegrityError

BEFORE = [("core", "0001_initial")]
AFTER = [("core", "0002_many_memberships")]


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(target)
    return executor.loader.project_state(target).apps


def add_person(apps, email):
    return apps.get_model("core", "User").objects.create(email=email, display_name=email)


def add_membership(apps, user, group, role):
    apps.get_model("core", "Membership").objects.create(user=user, group=group, role=role)


@pytest.fixture
def at_latest(transactional_db):
    """Leaves the database at the newest migration whatever a test did."""
    yield
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


def test_going_back_keeps_data_while_everyone_has_one_membership(at_latest):
    apps = migrate(AFTER)
    group = apps.get_model("core", "Group").objects.create(status="active")
    add_membership(apps, add_person(apps, "a@example.com"), group, "woman")

    apps = migrate(BEFORE)
    assert apps.get_model("core", "Membership").objects.count() == 1
    # The old rule is back: one membership per person.
    group_2 = apps.get_model("core", "Group").objects.create(status="active")
    user = apps.get_model("core", "User").objects.get()
    with pytest.raises(IntegrityError):
        add_membership(apps, user, group_2, "supporter")

    apps = migrate(AFTER)
    assert apps.get_model("core", "Membership").objects.count() == 1


def test_going_back_fails_loudly_when_a_person_has_two_groups(at_latest):
    apps = migrate(AFTER)
    user = add_person(apps, "a@example.com")
    Group = apps.get_model("core", "Group")
    add_membership(apps, user, Group.objects.create(status="active"), "woman")
    add_membership(apps, user, Group.objects.create(status="active"), "supporter")

    with pytest.raises(RuntimeError, match="more than one group"):
        migrate(BEFORE)

    # Nothing was changed by the failed attempt.
    apps = migrate(AFTER)
    assert apps.get_model("core", "Membership").objects.count() == 2


def test_going_forward_keeps_existing_memberships(at_latest):
    apps = migrate(BEFORE)
    group = apps.get_model("core", "Group").objects.create(status="active")
    add_membership(apps, add_person(apps, "a@example.com"), group, "woman")

    apps = migrate(AFTER)
    membership = apps.get_model("core", "Membership").objects.get()
    assert (membership.role, membership.group_id) == ("woman", group.pk)
