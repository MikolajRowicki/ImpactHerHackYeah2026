"""Groq chat completions over HTTPS, with the standard library only.

The HTTP call is a plain function, so tests replace it and never touch the network. Error
messages are built from fixed words and the status code: never from the request, so the key
cannot leak through an exception.
"""

import json
import re
import urllib.error
import urllib.request
from collections.abc import Callable

from django.conf import settings

from .base import Generation, ProviderError

URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SECONDS = 8
# Some reasoning models put their thinking into the answer; people must see only the answer.
_THINK = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL)

# (url, headers, body, timeout) -> (status, body text)
Http = Callable[[str, dict, bytes, float], tuple[int, str]]


def urllib_http(url: str, headers: dict, body: bytes, timeout: float) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, ""


class GroqProvider:
    def __init__(
        self, http: Http | None = None, api_key: str | None = None, model: str | None = None
    ):
        self._http = http or urllib_http
        self._api_key = settings.GROQ_API_KEY if api_key is None else api_key
        self._model = model or settings.GROQ_MODEL

    def generate(self, prompt: str) -> Generation:
        body = json.dumps(
            {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 600,
            }
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            # The default Python agent is refused by Groq's edge.
            "User-Agent": "maydaymama/1.0",
        }
        try:
            status, text = self._http(URL, headers, body, TIMEOUT_SECONDS)
        except Exception as error:
            # Only the type of the failure: its text could repeat the request.
            raise ProviderError(f"Groq did not answer ({type(error).__name__}).") from None
        if status != 200:
            raise ProviderError(f"Groq answered with status {status}.")
        return Generation(text=self._read(text), source="groq")

    @staticmethod
    def _read(text: str) -> str:
        try:
            content = json.loads(text)["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError("Groq answer is not in the expected shape.") from None
        if isinstance(content, str):
            content = _THINK.sub("", content)
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Groq answered with an empty text.")
        return content.strip()
