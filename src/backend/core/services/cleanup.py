"""What happens to a person's data when they leave, are removed or delete the account.

One path serves all three, so the rules cannot drift apart: claimed tasks reopen, observation
answers go, then the membership goes. Everything runs in one transaction.
"""

from django.db import transaction

from ..constants import ROLE_WOMAN, TASK_CLAIMED, TASK_DONE, TASK_OPEN
from ..models import CheckIn, Group, Membership, Observation, Task


def _reopen_claimed_tasks(user_id: int, group_id: int) -> None:
    Task.objects.filter(group_id=group_id, claimed_by_id=user_id, status=TASK_CLAIMED).update(
        status=TASK_OPEN, claimed_by=None, claimed_at=None
    )


def remove_membership(membership: Membership) -> None:
    """Take a person out of their group and drop what only their membership held.

    Tasks they finished keep their claimer, tasks they created stay. A group that is left
    without anyone (a pending group whose partner goes) is deleted with its invitations.
    """
    with transaction.atomic():
        _reopen_claimed_tasks(membership.user_id, membership.group_id)
        # The answers go with the observations (cascade); nothing keeps who gave them.
        Observation.objects.filter(author=membership).delete()
        group_id = membership.group_id
        membership.delete()
        if not Membership.objects.filter(group_id=group_id).exists():
            Group.objects.filter(pk=group_id).delete()


def delete_group(group_id: int) -> None:
    """Remove the whole group; this cascades to memberships, check-ins, observations, tasks and
    invitations."""
    Group.objects.filter(pk=group_id).delete()


def delete_group_if_empty(group_id: int, user_id: int) -> bool:
    """Delete the group when its only member is that person and it holds no data.

    Call it inside a transaction. The group row is locked first, so data added at the same moment
    waits: it is either seen by the check or refused after the delete, never lost with the group.
    (SQLite ignores the row lock; its write lock, taken at the start of the transaction, does it.)
    """
    group = Group.objects.select_for_update().filter(pk=group_id).first()
    if group is None:
        return False
    if list(Membership.objects.filter(group_id=group_id).values_list("user_id", flat=True)) != [
        user_id
    ]:
        return False
    holds_data = any(
        model.objects.filter(group_id=group_id).exists() for model in (CheckIn, Task, Observation)
    )
    if holds_data:
        return False
    group.delete()
    return True


def delete_account(user) -> None:
    """Delete the person and what they wrote. The woman takes her whole group with her."""
    with transaction.atomic():
        for membership in list(Membership.objects.filter(user=user)):
            if membership.role == ROLE_WOMAN:
                delete_group(membership.group_id)
            else:
                remove_membership(membership)
        # Task.claimed_by is SET_NULL, which a finished task cannot take (the database wants a
        # claimer on it). Claimed tasks were reopened above; finished ones go with their person.
        Task.objects.filter(claimed_by_id=user.pk, status=TASK_DONE).delete()
        user.delete()
