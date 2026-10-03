from ninja import NinjaAPI, Schema
from ninja.security import SessionAuth

from .. import errors
from . import ai, auth, auth_security, groups, help, reminders, tasks, tracking

# CSRF is checked for every unsafe call by core.middleware.ApiMiddleware, public ones included.
session_auth = SessionAuth(csrf=False)

# The contract in contracts/openapi.yaml is the source of truth, so the generated
# docs and schema routes stay off: every route under /api/v1 must be declared there.
api = NinjaAPI(title="MaydayMama", version="v0", docs_url=None, openapi_url=None, auth=session_auth)
errors.install(api)


class HealthOut(Schema):
    status: str


@api.get("/health", response=HealthOut, operation_id="health", auth=None)
def health(request):
    return {"status": "ok"}


# One router per area. A path and all its methods live in one router, because django-ninja
# answers 405 for a method that its first router for that path does not hold.
for module in (auth, auth_security, groups, tracking, tasks, help, reminders, ai):
    api.add_router("", module.router)
