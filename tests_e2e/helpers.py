"""Small helpers shared by the browser tests."""

from urllib.parse import urlparse


def open_as(page, perspective="woman", path="/"):
    """Opens the demo as one of the mock perspectives on the given route."""
    page.goto(f"{page.base}?mock=1&variant={perspective}#{path}")


def change_mock_state(page, script):
    """Changes the demo state behind the screen's back, as another person on another device would.

    `script` is a JS function body that receives the state object `s` and changes it in place.
    """
    page.evaluate(
        """(script) => {
            const s = JSON.parse(sessionStorage.getItem("mock-state"));
            new Function("s", script)(s);
            sessionStorage.setItem("mock-state", JSON.stringify(s));
        }""",
        script,
    )


def nav(page):
    return page.get_by_role("navigation", name="Nawigacja")


def h1(page):
    return page.get_by_role("heading", level=1)


def memberships_from(me_answer):
    """The group list that matches a routed `get_me` answer, unless the test routes its own."""
    status, me = me_answer or (401, {"error": {"code": "unauthorized", "message": "Zaloguj się."}})
    if status != 200:
        return status, me
    membership = me.get("membership")
    items = []
    if membership:
        woman = me["display_name"] if membership["role"] == "woman" else "Anna"
        items.append({**membership, "woman_name": woman})
    return 200, {"items": items}


def live(page, answers, path="/"):
    """Opens the page in live mode with routed API answers.

    `answers` maps "METHOD /api/v1/path" to (status, body); the test may change it later, as the
    backend's state would change. Returns the list of "METHOD /api/v1/path" that were called.
    """
    calls = []

    def answer(route):
        key = f"{route.request.method} {urlparse(route.request.url).path}"
        calls.append(key)
        if key == "GET /api/v1/me/memberships" and key not in answers:
            status, body = memberships_from(answers.get("GET /api/v1/me"))
        else:
            status, body = answers.get(
                key, (404, {"error": {"code": "not_found", "message": "Brak."}})
            )
        route.fulfill(status=status, json=body)

    page.route("**/api/v1/**", answer)
    page.goto(f"{page.base}?mock=0#{path}")
    return calls
