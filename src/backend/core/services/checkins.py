"""Check-ins: the woman's private record of how she feels. Only she reads them."""

from datetime import UTC

from ..models import CheckIn
from ..permissions import MemberContext


def as_dict(check_in: CheckIn) -> dict:
    return {
        "id": check_in.pk,
        "created_at": check_in.created_at.astimezone(UTC),
        "mood": check_in.mood,
        "sleep": check_in.sleep,
        "anxiety": check_in.anxiety,
    }


def create_check_in(ctx: MemberContext, mood: str, sleep: str, anxiety: str) -> dict:
    # A second check-in on the same day is another row; nothing is overwritten.
    check_in = CheckIn.objects.create(
        group=ctx.group, author=ctx.membership, mood=mood, sleep=sleep, anxiety=anxiety
    )
    return as_dict(check_in)


def list_check_ins(ctx: MemberContext) -> list[dict]:
    rows = CheckIn.objects.filter(author=ctx.membership).order_by("-created_at", "-id")
    return [as_dict(row) for row in rows]
