from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.static import serve

from core.api import api


@ensure_csrf_cookie
def home(request):
    # The cookie lets the frontend send the CSRF header on its first unsafe call.
    return HttpResponseRedirect("/static/index.html")


urlpatterns = [
    path("api/v1/", api.urls),
    path("", home),
    # The page sets the CSRF cookie itself, so it works when opened directly, not only through "/".
    re_path(
        r"^static/(?P<path>index\.html)$",
        ensure_csrf_cookie(serve),
        {"document_root": settings.FRONTEND_DIR},
    ),
    # Mock mode in the browser reads the same example files the tests validate.
    re_path(
        r"^static/contracts/(?P<path>.*)$",
        serve,
        {"document_root": settings.CONTRACTS_DIR},
    ),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.FRONTEND_DIR}),
]
