from datetime import datetime
from typing import Literal

from ninja import Router, Schema
from pydantic import Field

from ..constants import ANXIETIES, MOODS, ROLE_PARTNER, ROLE_SUPPORTER, ROLE_WOMAN, SLEEPS
from ..content.questions import question_list
from ..content.self_care import self_care_list
from ..permissions import member_context
from ..schemas import In
from ..services import checkins, observations, summary

router = Router()

WOMAN_ONLY = "Te wpisy widzi tylko właścicielka grupy."
LOVED_ONES_ONLY = "Tę operację mają tylko bliscy kobiety."
LOVED_ONES = (ROLE_PARTNER, ROLE_SUPPORTER)


class CheckInIn(In):
    mood: Literal[MOODS]
    sleep: Literal[SLEEPS]
    anxiety: Literal[ANXIETIES]


class CheckInOut(Schema):
    id: int
    created_at: datetime
    mood: str
    sleep: str
    anxiety: str


class CheckInListOut(Schema):
    items: list[CheckInOut]


class SelfCareItemOut(Schema):
    id: str
    kind: str
    title: str
    description: str
    duration_minutes: int


class SelfCareListOut(Schema):
    items: list[SelfCareItemOut]


class AnswerOptionOut(Schema):
    value: str
    label: str


class QuestionOut(Schema):
    id: str
    text: str
    answers: list[AnswerOptionOut]


class QuestionListOut(Schema):
    items: list[QuestionOut]


class AnswerIn(In):
    question_id: str = Field(max_length=100)
    value: Literal["yes", "no", "unsure", "more_than_usual", "as_usual", "less_than_usual"]


class ObservationIn(In):
    answers: list[AnswerIn] = Field(min_length=1, max_length=50)


class ObservationCreatedOut(Schema):
    id: int
    created_at: datetime


class NarrativeOut(Schema):
    text: str
    source: Literal["mock", "groq", "rules"]


class SummaryOut(Schema):
    audience: str
    trend: str
    statements: list[str]
    care_reminder: str | None
    narrative: NarrativeOut
    generated_at: datetime


class SummaryExtendedOut(SummaryOut):
    reasons: list[str]
    help: dict | None


@router.post("/check-ins", response={201: CheckInOut}, operation_id="create_check_in")
def create_check_in(request, payload: CheckInIn):
    ctx = member_context(
        request,
        [ROLE_WOMAN],
        active=True,
        message="Samopoczucie zapisuje tylko właścicielka grupy.",
    )
    return 201, checkins.create_check_in(ctx, payload.mood, payload.sleep, payload.anxiety)


@router.get("/check-ins", response=CheckInListOut, operation_id="list_check_ins")
def list_check_ins(request):
    ctx = member_context(request, [ROLE_WOMAN], message=WOMAN_ONLY)
    return {"items": checkins.list_check_ins(ctx)}


@router.get("/self-care", response=SelfCareListOut, operation_id="list_self_care")
def list_self_care(request):
    member_context(request, [ROLE_WOMAN], message="Te propozycje są dla właścicielki grupy.")
    return {"items": self_care_list()}


@router.get(
    "/observations/questions", response=QuestionListOut, operation_id="list_observation_questions"
)
def list_observation_questions(request):
    member_context(request, LOVED_ONES, message=LOVED_ONES_ONLY)
    return {"items": question_list()}


@router.post(
    "/observations", response={201: ObservationCreatedOut}, operation_id="create_observation"
)
def create_observation(request, payload: ObservationIn):
    ctx = member_context(request, LOVED_ONES, active=True, message=LOVED_ONES_ONLY)
    answers = [(a.question_id, a.value) for a in payload.answers]
    return 201, observations.create_observation(ctx, answers)


@router.get("/summary", response=SummaryOut, operation_id="get_summary")
def get_summary(request):
    ctx = member_context(request)
    return summary.build_summary(ctx)


@router.get("/summary/extended", response=SummaryExtendedOut, operation_id="get_summary_extended")
def get_summary_extended(request):
    ctx = member_context(request)
    return summary.build_extended(ctx)
