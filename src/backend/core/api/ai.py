from typing import Annotated, Literal

from ninja import Router, Schema
from pydantic import StringConstraints

from ..constants import ROLE_PARTNER, ROLE_SUPPORTER, ROLE_WOMAN
from ..content.guide_topics import TOPICS
from ..permissions import member_context
from ..schemas import In
from ..services import assist_guide, assist_say_it

router = Router()

WOMAN_ONLY = "Ta funkcja jest tylko dla właścicielki grupy."
CLOSE_ONES_ONLY = "Ta funkcja jest dla bliskich właścicielki grupy."


class SayItIn(In):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    recipient: Literal["partner", "supporters"]
    tone: Literal["gentle", "direct"]


class SourceOut(Schema):
    title: str
    url: str


class SayItOut(Schema):
    crisis: bool
    message: str | None
    help: dict | None
    source: Literal["mock", "groq", "rules"]
    sources: list[SourceOut]


class GuideOut(Schema):
    topic: Literal[TOPICS]
    opening_lines: list[str]
    avoid: list[str]
    questions: list[str]
    source: Literal["mock", "groq", "rules"]
    sources: list[SourceOut]


@router.post("/ai/say-it-for-me", response=SayItOut, operation_id="ai_say_it_for_me")
def say_it_for_me(request, payload: SayItIn):
    context = member_context(request, (ROLE_WOMAN,), message=WOMAN_ONLY)
    return assist_say_it.suggest(context.user, payload.text, payload.recipient, payload.tone)


@router.get("/ai/conversation-guide", response=GuideOut, operation_id="ai_conversation_guide")
def conversation_guide(request, topic: Literal[TOPICS]):
    member_context(request, (ROLE_PARTNER, ROLE_SUPPORTER), message=CLOSE_ONES_ONLY)
    return assist_guide.guide(topic)
