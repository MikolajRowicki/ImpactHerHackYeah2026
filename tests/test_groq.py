"""The Groq adapter, always with a fake HTTP function. No test here uses the network."""

import json
import logging
import socket
import urllib.error
import urllib.request

import pytest

from core.ai import ProviderError, assist
from core.ai.groq import TIMEOUT_SECONDS, URL, GroqProvider, urllib_http

KEY = "gsk_SECRET_key_0123456789"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("no test may use the network")

    monkeypatch.setattr(socket, "socket", refuse)


def answer(content="Cześć, to tekst."):
    return json.dumps({"choices": [{"message": {"role": "assistant", "content": content}}]})


def provider(http):
    return GroqProvider(http=http, api_key=KEY, model="test-model")


def test_real_text_is_labelled_groq():
    generation = provider(lambda *a: (200, answer("Dziękuję, że jesteś."))).generate("prompt")
    assert generation.text == "Dziękuję, że jesteś."
    assert generation.source == "groq"


def test_request_goes_to_the_chat_endpoint_with_key_model_prompt_and_time_limit():
    seen = {}

    def http(url, headers, body, timeout):
        seen.update(url=url, headers=headers, body=json.loads(body), timeout=timeout)
        return 200, answer()

    provider(http).generate("moje pytanie")
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions" == URL
    assert seen["headers"]["Authorization"] == f"Bearer {KEY}"
    assert seen["body"]["model"] == "test-model"
    assert seen["body"]["messages"][-1] == {"role": "user", "content": "moje pytanie"}
    assert seen["timeout"] == TIMEOUT_SECONDS == 8


def test_model_and_key_come_from_settings_by_default(settings):
    settings.GROQ_API_KEY = KEY
    settings.GROQ_MODEL = "settings-model"
    seen = {}

    def http(url, headers, body, timeout):
        seen.update(headers=headers, body=json.loads(body))
        return 200, answer()

    GroqProvider(http=http).generate("x")
    assert seen["headers"]["Authorization"] == f"Bearer {KEY}"
    assert seen["body"]["model"] == "settings-model"


@pytest.mark.parametrize(
    ("env", "model"),
    [({}, "qwen/qwen3.8-27b"), ({"GROQ_MODEL": "openai/gpt-oss-120b"}, "openai/gpt-oss-120b")],
)
def test_the_request_names_the_model_of_the_environment(load_settings, settings, env, model):
    settings.GROQ_MODEL = load_settings(DJANGO_SECRET_KEY="x", **env).GROQ_MODEL
    seen = {}

    def http(url, headers, body, timeout):
        seen.update(body=json.loads(body))
        return 200, answer()

    GroqProvider(http=http, api_key=KEY).generate("x")
    assert seen["body"]["model"] == model


@pytest.mark.parametrize(
    ("content", "text"),
    [
        ("<think>plan</think>\nTekst.", "Tekst."),
        (
            "<think>\nkrok 1\nkrok 2\n</think>\n\nPierwsza linia.\nDruga linia.",
            "Pierwsza linia.\nDruga linia.",
        ),
        ("Tekst.<think>dopisek</think>", "Tekst."),
    ],
)
def test_a_think_block_is_dropped(content, text):
    assert provider(lambda *a: (200, answer(content))).generate("x").text == text


@pytest.mark.parametrize(
    "content", ["<think>tylko plan</think>", "<think>urwany plan", " <think></think> \n"]
)
def test_an_answer_of_only_thinking_is_empty(content):
    with pytest.raises(ProviderError, match="empty"):
        provider(lambda *a: (200, answer(content))).generate("x")


def test_only_thinking_gives_the_fallback_labelled_rules(monkeypatch):
    monkeypatch.setattr(
        "core.ai.assist.get_provider",
        lambda: provider(lambda *a: (200, answer("<think>plan</think>"))),
    )
    result = assist.generate("test", "prompt", "zapasowy tekst")
    assert (result.text, result.source) == ("zapasowy tekst", "rules")


@pytest.mark.parametrize("status", [400, 401, 429, 500, 503])
def test_an_http_error_is_a_provider_error(status):
    with pytest.raises(ProviderError, match=str(status)):
        provider(lambda *a: (status, '{"error": "nope"}')).generate("x")


def test_a_timeout_is_a_provider_error():
    def http(*args):
        raise TimeoutError("timed out")

    with pytest.raises(ProviderError):
        provider(http).generate("x")


@pytest.mark.parametrize(
    "body",
    [
        "not json at all",
        "",
        "[]",
        "{}",
        '{"choices": []}',
        '{"choices": [{}]}',
        '{"choices": [{"message": {}}]}',
        '{"choices": [{"message": {"content": null}}]}',
        '{"choices": [{"message": {"content": 5}}]}',
    ],
)
def test_a_malformed_answer_is_a_provider_error(body):
    with pytest.raises(ProviderError):
        provider(lambda *a: (200, body)).generate("x")


@pytest.mark.parametrize("content", ["", "   ", "\n\t"])
def test_an_empty_text_is_a_provider_error(content):
    with pytest.raises(ProviderError, match="empty"):
        provider(lambda *a: (200, answer(content))).generate("x")


def test_the_key_never_appears_in_an_error_even_when_the_transport_repeats_it():
    def http(url, headers, body, timeout):
        raise RuntimeError(f"failed with headers {headers}")

    with pytest.raises(ProviderError) as caught:
        provider(http).generate("x")
    assert KEY not in str(caught.value)
    assert KEY not in repr(caught.value)
    assert caught.value.__cause__ is None


@pytest.mark.parametrize("status", [401, 500])
def test_the_key_never_appears_in_an_http_error(status):
    with pytest.raises(ProviderError) as caught:
        provider(lambda url, headers, body, timeout: (status, f"echo {headers}")).generate("x")
    assert KEY not in str(caught.value)


def test_the_key_never_appears_in_a_log_line_when_a_call_fails(monkeypatch, caplog):
    def http(url, headers, body, timeout):
        raise RuntimeError(f"failed with headers {headers}")

    monkeypatch.setattr("core.ai.assist.get_provider", lambda: provider(http))
    caplog.set_level(logging.DEBUG)
    result = assist.generate("test", "prompt", "zapasowy tekst")
    assert result.text == "zapasowy tekst"
    assert result.source == "rules"
    assert KEY not in caplog.text


def test_a_failing_call_gives_the_fallback_and_never_a_groq_label(monkeypatch):
    def http(*args):
        raise TimeoutError

    monkeypatch.setattr("core.ai.assist.get_provider", lambda: provider(http))
    result = assist.generate("test", "prompt", "zapasowy tekst")
    assert (result.text, result.source) == ("zapasowy tekst", "rules")


def test_the_default_http_function_returns_status_and_text(monkeypatch):
    seen = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return "treść".encode()

    def fake_urlopen(request, timeout):
        seen.update(request=request, timeout=timeout)
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    status, text = urllib_http("https://example.test/x", {"X-One": "1"}, b"{}", 8)
    assert (status, text) == (200, "treść")
    assert seen["timeout"] == 8
    assert seen["request"].get_method() == "POST"
    assert seen["request"].get_header("X-one") == "1"


def test_the_default_http_function_turns_an_http_error_into_a_status(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 429, "Too Many", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert urllib_http("https://example.test/x", {}, b"{}", 8) == (429, "")


def test_a_network_error_of_the_default_function_is_a_provider_error(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.URLError(f"unreachable {request.headers}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    groq = GroqProvider(api_key=KEY, model="m")
    with pytest.raises(ProviderError) as caught:
        groq.generate("x")
    assert KEY not in str(caught.value)


def test_the_socket_guard_is_active():
    with pytest.raises(AssertionError, match="network"):
        socket.socket()
