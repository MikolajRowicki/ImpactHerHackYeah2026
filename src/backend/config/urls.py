from django.conf import settings
from django.urls import path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.static import serve

from core.api import api

# The page sets the CSRF cookie itself, so it works at "/" and when opened as /static/index.html.
page = ensure_csrf_cookie(serve)

urlpatterns = [
    path("api/v1/", api.urls),
    path("", page, {"path": "index.html", "document_root": settings.FRONTEND_DIR}),
    re_path(
        r"^static/(?P<path>index\.html)$",
        page,
        {"document_root": settings.FRONTEND_DIR},
    ),
    # The page uses relative links, so at "/" its files are looked up in the root too. Only the
    # frontend's own folders and files are listed; nothing else of the repository is reachable.
    re_path(
        r"^(?P<path>(?:css|js|fonts)/.+|favicon\.svg|apple-touch-icon\.png)$",
        serve,
        {"document_root": settings.FRONTEND_DIR},
    ),
    # Mock mode in the browser reads the same example files the tests validate.
    re_path(
        r"^(?:static/)?contracts/(?P<path>.*)$",
        serve,
        {"document_root": settings.CONTRACTS_DIR},
    ),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.FRONTEND_DIR}),
]
