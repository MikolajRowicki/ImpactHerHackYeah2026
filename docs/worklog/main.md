# Worklog: main session

One entry per task group. Change: `foundation-and-api-contract`, branch
`change/foundation-and-api-contract`.

## Group 1: Backend skeleton and tooling

- **Goal:** a Django project that runs from a clean clone, with settings from the environment.
- **Built:** `pyproject.toml` (pinned django, django-ninja; dev group), `poetry.lock`, ruff and
  pytest config, `src/backend/config` and `src/backend/core`, `GET /api/v1/health`,
  `.env.example`, tests for settings, health and `.env.example`.
- **Deviations:**
  - pytest-django loads the settings before any `conftest.py`, so the tests use
    `tests/settings.py`, which sets a test secret key and imports the real settings.
  - `.env` is loaded by `manage.py`, `wsgi.py` and `asgi.py`, not by the settings module, so tests
    never read a developer's local `.env`.
  - `config/env.py` records every variable it reads, so a test can compare them with `.env.example`.
  - `poetry.toml` (in-project virtualenv) is committed.
- **Verification:** `poetry install`, `ruff check .`, `ruff format --check .`, `pytest` (8 passed);
  `manage.py check` fails with a message naming `DJANGO_SECRET_KEY` when debug is off.
- **Commit:** `fedd56a`

## Group 2: API contract v0

- **Goal:** one written contract for backend and frontend.
- **Built:** `contracts/openapi.yaml` (23 operations, 9 resources, roles in `x-roles`, common
  error shape), 92 example files in `contracts/examples/`, `contracts/README.md`,
  `contracts/requests/`, guard tests (validity, examples against schemas, privacy, roles, routes).
- **Deviations:**
  - Paths carry the full `/api/v1` prefix.
  - `get_group` is open to any signed-in person (404 `no_group` without a group), so the rule
    "group operation without a membership gives 403 `not_a_member`" has no exception.
  - "The woman invites any role" is read as partner or supporter (see the proposal assumptions).
  - `yes` and `no` are quoted in the YAML: PyYAML reads bare `yes` and `no` as booleans.
  - Examples have variants (`get_me.200.partner.json`) so the frontend can show other roles.
  - Every declared response has an example, which is stricter than the spec asks.
- **Verification:** `pytest` (329 passed at the end of group 3). The route guard was checked by
  hand: a route added to `core/api.py` without a contract entry made
  `test_every_implemented_route_is_declared` fail; the route was removed again.
- **Commit:** `df34a1e`

## Group 3: Frontend shell with mock mode

- **Goal:** a frontend page that runs without a backend and shows that it does.
- **Built:** `src/frontend` (index, tokens, base CSS, hash router, strings file, placeholder
  screen), API client with live and mock adapters, mock notice, `tests_e2e` (mock mode, layout at
  375 and 1280 px, live adapter against Django), operation table guard test.
- **Deviations:**
  - Django serves the frontend and `contracts/` with `django.views.static.serve` in `urls.py`
    instead of the staticfiles app, so the demo also works with debug off.
  - `/` redirects to `/static/index.html` and sets the CSRF cookie.
  - The mock adapter also takes `?variant=` and `{ status }` so the frontend session can show
    other roles and error states.
  - Browser tests start their own WSGI server for Django instead of `live_server`, which breaks
    with Playwright's event loop (`SynchronousOnlyOperation`).
  - `/api/v1/me` is not built yet, so the live-mode test expects the "could not load" message.
- **Verification:** `pytest tests_e2e` (12 passed, headless). Two throwaway-copy mutations were
  caught: hiding the notice failed 3 tests, making mock mode call the live API failed 7. Screenshots
  at 375 and 1280 px were looked at; a stray margin on the notice was fixed.
- **Commit:** `847cf88`

## Group 4: Documentation and frontend brief

- **Goal:** a clean clone is enough to start, and the frontend session has a self-contained brief.
- **Built:** `README.md`, `docs/architecture.md` (component, sequence and ER diagrams, role
  table), `docs/frontend-brief.md`, this worklog, the per-session worklog rule in `CLAUDE.md`.
- **Deviations:**
  - The brief does not use the words "AI" or "assistant", because `CLAUDE.md` forbids mentioning
    them in files.
  - The frontend session also owns `tests_e2e/`, because the shell tests check the placeholder
    screen it will replace.
  - The hash of this group is added in a follow-up commit, because a commit cannot contain its own hash.
- **Verification:** all three Mermaid blocks render with Mermaid 11 in headless Chromium; the
  README and the brief were followed step by step in a fresh clone.
- **Commit:** `3d9581a`

## Group 5: AI provider switch

- **Goal:** the AI provider comes from `.env`, mock by default, so the demo needs no key.
- **Built:** `core/ai/` (provider protocol, deterministic mock provider, `get_provider`),
  `AI_PROVIDER` in the settings, a startup check in `CoreConfig.ready`, `.env.example` entry,
  a section in `docs/architecture.md`, tests.
- **Deviations:**
  - The check runs in `CoreConfig.ready`, not in the settings module, so the settings stay free of
    app imports. `manage.py check` fails with the list of available values.
  - `GROQ_API_KEY` is only a comment in `.env.example`: nothing reads it until the Groq adapter
    exists, and the `.env.example` test compares only variables that are read.
  - The mock picks one of three fixed Polish sentences by the hash of the prompt.
- **Verification:** `pytest` (339 passed), `ruff check .`, `ruff format --check .`;
  `AI_PROVIDER=nope manage.py check` stops with "Available values: mock", the default passes.
- **Commit:** see the git log (`feat(ai): add provider switch`).
