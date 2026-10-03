"""Observations: a loved one's closed answers. Stored for the trend engine, never shown."""

from datetime import UTC

from django.db import transaction

from ..content.questions import OFFERED
from ..errors import invalid
from ..models import Observation, ObservationAnswer
from ..permissions import MemberContext


def validate_answers(answers: list[tuple[str, str]]) -> None:
    """Every question must exist once and every value must be one the question offers."""
    seen = set()
    for question_id, value in answers:
        if question_id not in OFFERED:
            raise invalid(answers="Jedno z pytań nie istnieje.")
        if question_id in seen:
            raise invalid(answers="Na każde pytanie można odpowiedzieć tylko raz.")
        seen.add(question_id)
        if value not in OFFERED[question_id]:
            raise invalid(answers="Jedna z odpowiedzi nie pasuje do pytania.")


def create_observation(ctx: MemberContext, answers: list[tuple[str, str]]) -> dict:
    validate_answers(answers)
    with transaction.atomic():
        observation = Observation.objects.create(group=ctx.group, author=ctx.membership)
        ObservationAnswer.objects.bulk_create(
            ObservationAnswer(observation=observation, question_id=question_id, value=value)
            for question_id, value in answers
        )
    return {"id": observation.pk, "created_at": observation.created_at.astimezone(UTC)}
