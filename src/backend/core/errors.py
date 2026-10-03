"""The common error shape, `{"error": {"code", "message", "fields"?}}`, for every refusal.

Services and routers raise `ApiError`; the handlers installed on the API turn it, validation
errors, unknown paths and unexpected failures into the same body. Messages are Polish.
"""

import json
import logging

from django.http import Http404
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, HttpError, ValidationError

logger = logging.getLogger(__name__)

VALIDATION_MESSAGE = "Popraw zaznaczone pola."


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, fields: dict[str, str] | None = None):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields


def error_body(code: str, message: str, fields: dict[str, str] | None = None) -> dict:
    body = {"code": code, "message": message}
    if fields:
        body["fields"] = fields
    return {"error": body}


def invalid(**fields: str) -> ApiError:
    """422 with a message per field, for rules a schema cannot express."""
    return ApiError(422, "validation_error", VALIDATION_MESSAGE, fields)


# Polish messages for the checks that schemas make, by field and then by pydantic error type.
TYPE_MESSAGES = {
    "missing": "To pole jest wymagane.",
    "string_too_short": "Ta wartość jest za krótka.",
    "string_too_long": "Ta wartość jest za długa.",
    "enum": "Wybierz jedną z dostępnych wartości.",
    "literal_error": "Wybierz jedną z dostępnych wartości.",
    "extra_forbidden": "Tego pola nie można podać.",
    "too_short": "Podaj co najmniej jedną wartość.",
    "value_error": "Podaj poprawną wartość.",
}
FIELD_MESSAGES = {
    ("email", "value_error"): "Podaj poprawny adres e-mail.",
    ("email", "missing"): "Podaj adres e-mail.",
    ("password", "string_too_short"): "Hasło musi mieć co najmniej 8 znaków.",
    ("password", "string_too_long"): "Hasło może mieć najwyżej 128 znaków.",
    ("new_password", "string_too_short"): "Hasło musi mieć co najmniej 8 znaków.",
    ("new_password", "string_too_long"): "Hasło może mieć najwyżej 128 znaków.",
    ("current_password", "missing"): "Podaj obecne hasło.",
    ("current_password", "string_too_short"): "Podaj obecne hasło.",
    ("display_name", "string_too_short"): "Wpisz imię lub nazwę.",
    ("display_name", "string_too_long"): "Imię lub nazwa może mieć najwyżej 60 znaków.",
    ("title", "string_too_short"): "Wpisz krótki tytuł zadania.",
    ("title", "string_too_long"): "Tytuł może mieć najwyżej 120 znaków.",
    ("details", "string_too_long"): "Opis może mieć najwyżej 500 znaków.",
    ("text", "string_too_short"): "Wpisz od 1 do 500 znaków.",
    ("text", "string_too_long"): "Wpisz od 1 do 500 znaków.",
    ("text", "missing"): "Wpisz od 1 do 500 znaków.",
    ("answers", "too_short"): "Odpowiedz na co najmniej jedno pytanie.",
    ("answers", "missing"): "Odpowiedz na co najmniej jedno pytanie.",
    ("token", "missing"): "Brakuje kodu z linku.",
    ("token", "string_too_short"): "Brakuje kodu z linku.",
    ("token", "string_too_long"): "Ten kod jest nieprawidłowy.",
    ("voivodeship", "enum"): "Wybierz województwo z listy.",
    ("voivodeship", "literal_error"): "Wybierz województwo z listy.",
    ("topic", "enum"): "Wybierz temat z listy.",
    ("topic", "literal_error"): "Wybierz temat z listy.",
    ("topic", "missing"): "Wybierz temat z listy.",
    ("role", "enum"): "Wybierz rolę z listy.",
    ("role", "literal_error"): "Wybierz rolę z listy.",
    ("recipient", "literal_error"): "Wybierz, do kogo jest wiadomość.",
    ("tone", "literal_error"): "Wybierz ton wiadomości.",
    ("mood", "literal_error"): "Wybierz jedną z dostępnych odpowiedzi.",
    ("sleep", "literal_error"): "Wybierz jedną z dostępnych odpowiedzi.",
    ("anxiety", "literal_error"): "Wybierz jedną z dostępnych odpowiedzi.",
}
FALLBACK_MESSAGE = "Popraw tę wartość."


def _field_name(loc) -> str:
    """The request field an error is about. Locations look like ("body", "payload", "email")."""
    parts = [str(p) for p in loc]
    if parts and parts[0] == "body":
        parts = parts[2:] or parts[1:]
    elif parts:
        parts = parts[1:]
    return parts[0] if parts else "body"


def validation_fields(errors) -> dict[str, str]:
    fields: dict[str, str] = {}
    for error in errors:
        name = _field_name(error.get("loc", ()))
        kind = error.get("type", "")
        message = FIELD_MESSAGES.get((name, kind)) or TYPE_MESSAGES.get(kind) or FALLBACK_MESSAGE
        fields.setdefault(name, message)
    return fields


HTTP_ERRORS = {
    400: ("validation_error", "Nie udało się odczytać danych żądania."),
    401: ("unauthorized", "Zaloguj się, aby kontynuować."),
    403: ("forbidden", "Ta operacja nie jest dostępna."),
    404: ("not_found", "Nie znaleziono."),
    405: ("method_not_allowed", "Ta metoda nie jest dostępna dla tego adresu."),
}


def http_error_body(status: int) -> tuple[int, dict]:
    code, message = HTTP_ERRORS.get(
        status, ("server_error", "Coś poszło nie tak. Spróbuj ponownie.")
    )
    # An unreadable body is a validation problem for the client, so it answers 422.
    return (422 if status == 400 else status), error_body(code, message)


def install(api: NinjaAPI) -> None:
    @api.exception_handler(ApiError)
    def api_error(request, exc):
        return api.create_response(
            request, error_body(exc.code, exc.message, exc.fields), status=exc.status
        )

    @api.exception_handler(ValidationError)
    def validation_error(request, exc):
        fields = validation_fields(exc.errors)
        return api.create_response(
            request, error_body("validation_error", VALIDATION_MESSAGE, fields), status=422
        )

    @api.exception_handler(AuthenticationError)
    def unauthorized(request, exc):
        status, body = http_error_body(401)
        return api.create_response(request, body, status=status)

    @api.exception_handler(HttpError)
    def http_error(request, exc):
        status, body = http_error_body(exc.status_code)
        return api.create_response(request, body, status=status)

    @api.exception_handler(Http404)
    def not_found(request, exc):
        status, body = http_error_body(404)
        return api.create_response(request, body, status=status)

    @api.exception_handler(json.JSONDecodeError)
    def malformed_json(request, exc):
        status, body = http_error_body(400)
        return api.create_response(request, body, status=status)

    @api.exception_handler(Exception)
    def unexpected(request, exc):
        # No detail leaves the server; the log has the traceback.
        logger.exception("Unexpected error in %s %s", request.method, request.path)
        return api.create_response(
            request,
            error_body("server_error", "Coś poszło nie tak. Spróbuj ponownie za chwilę."),
            status=500,
        )
