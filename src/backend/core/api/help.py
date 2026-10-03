from ninja import Router, Schema

from ..services import help as help_service

router = Router()


class CrisisLineOut(Schema):
    name: str
    number: str
    hours: str
    description: str
    source_url: str


class CareStepOut(Schema):
    order: int
    title: str
    description: str


class RegionalContactOut(Schema):
    name: str
    description: str
    url: str


class HelpOut(Schema):
    crisis_lines: list[CrisisLineOut]
    voivodeship: str | None
    path: list[CareStepOut]
    regional_contact: RegionalContactOut | None


@router.get("/help", response=HelpOut, operation_id="get_help")
def get_help(request, voivodeship: str | None = None):
    # A plain string, so a wrong value gets the contract's 422 with the field named.
    return help_service.help_for(request.user, voivodeship)
