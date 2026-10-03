from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware

from .errors import error_body, http_error_body

API_PREFIX = "/api/v1/"
SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")


def _noop(request):  # a stand-in view for the CSRF check; it is not csrf_exempt
    return None


class ApiMiddleware:
    """CSRF for every unsafe call under /api/v1, and the common error shape for what Django
    answers itself: unknown paths and wrong methods."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf = CsrfViewMiddleware(get_response)

    def __call__(self, request):
        if not request.path.startswith(API_PREFIX):
            return self.get_response(request)
        if request.method not in SAFE_METHODS and self.csrf.process_view(request, _noop, (), {}):
            return JsonResponse(
                error_body("csrf_failed", "Odśwież stronę i spróbuj ponownie."), status=403
            )
        response = self.get_response(request)
        if response.status_code in (404, 405) and "json" not in response.get("Content-Type", ""):
            status, body = http_error_body(response.status_code)
            return JsonResponse(body, status=status)
        return response
