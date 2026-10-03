"""Small helpers shared by the browser tests."""


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
