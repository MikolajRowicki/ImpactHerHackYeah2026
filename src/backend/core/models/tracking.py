from django.db import models

from .. import clock
from ..constants import ANSWER_VALUES, ANXIETIES, MOODS, SLEEPS
from .groups import Group, Membership, in_set


class CheckIn(models.Model):
    """How the woman feels. Private: only she reads it."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="check_ins")
    author = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="check_ins")
    mood = models.CharField(max_length=10)
    sleep = models.CharField(max_length=12)
    anxiety = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=clock.now)

    class Meta:
        indexes = [models.Index(fields=["group", "created_at"])]
        constraints = [
            in_set("mood", MOODS, "check_in_mood_known"),
            in_set("sleep", SLEEPS, "check_in_sleep_known"),
            in_set("anxiety", ANXIETIES, "check_in_anxiety_known"),
        ]


class Observation(models.Model):
    """One loved one's answers on one occasion. Read only by the trend engine."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="observations")
    author = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="observations")
    created_at = models.DateTimeField(default=clock.now)

    class Meta:
        indexes = [models.Index(fields=["group", "created_at"])]


class ObservationAnswer(models.Model):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE, related_name="answers")
    question_id = models.CharField(max_length=40)
    value = models.CharField(max_length=20)

    class Meta:
        constraints = [
            in_set("value", ANSWER_VALUES, "answer_value_known"),
            models.UniqueConstraint(
                fields=["observation", "question_id"], name="answer_one_per_question"
            ),
        ]
