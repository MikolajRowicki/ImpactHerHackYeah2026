from ninja import NinjaAPI, Schema

# The contract in contracts/openapi.yaml is the source of truth, so the generated
# docs and schema routes stay off: every route under /api/v1 must be declared there.
api = NinjaAPI(title="MaydayMama", version="v0", docs_url=None, openapi_url=None)


class HealthOut(Schema):
    status: str


@api.get("/health", response=HealthOut, operation_id="health", auth=None)
def health(request):
    return {"status": "ok"}
