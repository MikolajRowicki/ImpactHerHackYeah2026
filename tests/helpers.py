"""`call()` for API tests: every response is checked against the contract.

A test that goes through `Api.call` is also a contract test. It fails when the status is not
declared for the operation, when the body does not match its schema, when a timestamp is not UTC,
or when the CSRF header is missing. The pairs (operation, status) it saw are recorded, so a final
test can check that every operation was exercised with its success status.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from django.core.mail.backends.base import BaseEmailBackend
from django.test import Client
from jsonschema import Draft202012Validator, FormatChecker

from . import contract as c

# (operationId, status) pairs seen by Api.call during this run.
EXERCISED: set[tuple[str, int]] = set()

TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


@dataclass
class Response:
    status: int
    body: Any
    raw: Any

    def __getitem__(self, key):
        return self.body[key]

    @property
    def error(self):
        return self.body["error"]

    @property
    def code(self):
        return self.body["error"]["code"]


def walk_timestamps(value, where="body"):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk_timestamps(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_timestamps(item, f"{where}[{index}]")
    elif isinstance(value, str) and TIMESTAMP.match(value):
        yield where, value


class Api:
    """One person's browser: a cookie jar plus calls by operationId."""

    def __init__(self, capture_commits=None):
        self.client = Client(enforce_csrf_checks=True)
        # Callbacks registered with transaction.on_commit (mail) run after each call.
        self._capture = capture_commits

    def sign_in(self, user):
        self.client.force_login(user)
        return self

    def csrf_token(self):
        if "csrftoken" not in self.client.cookies:
            self.client.get("/")  # the home page sets the cookie, as in the browser
        return self.client.cookies["csrftoken"].value

    def call(
        self, operation_id, *, body=None, path=None, query=None, csrf=True, check=True
    ) -> Response:
        method, template, op = c.operation_by_id()[operation_id]
        url = template.format(**(path or {}))
        extra = {"HTTP_X_CSRFTOKEN": self.csrf_token()} if csrf else {}
        send = {"content_type": "application/json", **extra}
        verb = getattr(self.client, method)
        if self._capture:
            with self._capture(execute=True):
                raw = self._send(verb, method, url, body, query, send)
        else:
            raw = self._send(verb, method, url, body, query, send)
        parsed = json.loads(raw.content) if raw.content else None
        result = Response(raw.status_code, parsed, raw)
        if check:
            self.check_contract(operation_id, op, result)
        EXERCISED.add((operation_id, result.status))
        return result

    @staticmethod
    def _send(verb, method, url, body, query, send):
        if method == "get":
            return verb(url, query or {}, **{k: v for k, v in send.items() if k != "content_type"})
        data = json.dumps(body) if body is not None else ""
        if query:
            url = f"{url}?" + "&".join(f"{k}={v}" for k, v in query.items())
        return verb(url, data=data, **send)

    @staticmethod
    def check_contract(operation_id, op, result):
        status = str(result.status)
        declared = sorted(op["responses"])
        assert status in op["responses"], (
            f"{operation_id} answered {status}, the contract declares {declared}: {result.body}"
        )
        schema = c.response_schema(op, status)
        validator = Draft202012Validator(c.with_components(schema), format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(result.body), key=str)
        assert not errors, f"{operation_id} {status} breaks the contract: " + "; ".join(
            f"{list(e.path)}: {e.message}" for e in errors
        )
        for where, value in walk_timestamps(result.body):
            assert value.endswith("Z"), f"{operation_id}: {where} is not UTC: {value}"


class FailingEmailBackend(BaseEmailBackend):
    """A mail server that is down."""

    def send_messages(self, email_messages):
        raise ConnectionRefusedError("mail server down: secret-address@example.com")
