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
  - The brief follows the `CLAUDE.md` rule about never showing how the code was produced, so it
    names only the repository's own files and plugins.
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
- **Commit:** `caba71d`

## Review round 1 (independent reviewer): FAIL, fixed

Findings and what changed:

- CSRF header missing when the page is opened as `/static/index.html` (the cookie was set only on
  `/`): the page itself now sets the cookie; a browser test and a unit test cover it.
- Planning files named the tool behind the sessions: wording in `design.md`, `proposal.md`,
  `tasks.md` and this worklog was changed. Repository file names stay. The body of the older
  commit `adce459` still names the tool; history is not rewritten.
- Spec said the woman may invite "any role", the contract says partner or supporter: the spec
  scenario now says "a partner or a supporter" (listed as an assumption in the proposal).
- Closed group had no declared answer: operations that need an active group now document 409
  `group_closed` next to `group_pending`; example `create_task.409.closed.json`; closing a closed
  group returns it unchanged.
- `get_invitation` description did not match its schema: description fixed.
- Mock notice scrolled away: the notice slot is now sticky; browser test added.
- Weak guards strengthened (each checked by a mutation in a throwaway copy): partner-created group
  is `pending`, every 422 example has `fields`, summary may only hold an allowlist of general
  fields, every `date-time` says UTC, URL patterns under `/api/v1` must be declared (not only
  django-ninja routes), settings code reads the environment only through the helper.
- Group 5 hash recorded (above).

## Review round 2 (independent reviewer): FAIL, fixed

- The 409 `group_closed` answer was documented only in the shared response; `claim_task`,
  `complete_task`, `architecture.md` and `contracts/README.md` still said only `group_pending`.
  All now name both codes, with `<operationId>.409.closed.json` examples; a test requires both
  codes for every operation marked `x-requires-active-group`.
- Invitations on a closed group had no declared answer: `create_invitation` and `accept_invitation`
  now declare 409 `group_closed`.
- `#constructor` in the URL showed `[object Object]` because routes were looked up on a plain
  object; the lookup uses `Object.hasOwn`, with a browser test (checked with a mutation).
- Left as is: the unreachable 409 `group_pending` on `create_check_in` (harmless over-declaration)
  and inline `#` comments in `.env` lines, which the small loader does not strip.

## Review round 3 (independent reviewer): PASS

All round-2 fixes verified by mutation in a throwaway copy; no new defects. One observation was
acted on: `/?mock=1` redirected without its query string and so switched mock mode off; the
redirect now keeps the query (unit test). Left as is: closed-group examples for `create_check_in`
and `create_observation` do not exist (not a spec scenario), `[::1]` is not in the default
`DJANGO_ALLOWED_HOSTS`.

## Archive

Change archived as `openspec/changes/archive/2026-10-03-foundation-and-api-contract`. The three
capabilities (`api-contract`, `frontend-mock-mode`, `ai-provider-config`) are now main specs
(16 requirements). `openspec validate --specs` passes.

## Change user-flow-and-groups: review

- A fresh reviewer mapped every scenario to a test and ended with PASS. Low findings fixed: the
  remembered group is forgotten at sign-out, a failed group switch shows the error state, the mock
  store refuses a second mother invitation like the backend, and a test checks the header text in
  the contract. Left as is: contrast probe covers text elements only; no test for suggestions in a
  pending group (that screen is closed to a pending group by the route guard).

## Change ai-assist-and-sources, group 1: Groq model and prompts

- **Goal:** Groq works again and its texts do not guess anyone's gender.
- **Built:**
  - The default `GROQ_MODEL` is `qwen/qwen3.8-27b`. `llama-3.3-70b-versatile` answered 404
    `model_not_found` on 2026-10-04. The key listed `openai/gpt-oss-120b`, `openai/gpt-oss-20b`
    and `qwen/qwen3.8-27b` as chat models; Qwen wrote the most natural Polish in 0.2–0.5 s. Free
    limits for this key: 1000 requests a day, 8000 tokens a minute per model.
  - A `<think>` block in a Groq answer is dropped. An answer of only thinking counts as empty.
  - The guide prompt names the gendered forms to avoid. Generated guide lines that still hold a
    first-person past or conditional form are dropped. When no line is left, the fixed lines are
    used with `source: rules` and no sources.
  - The "say it for me" prompt keeps her feminine voice and asks not to assume the partner's
    gender.
  - `load_settings` in the tests now also clears `GROQ_MODEL` and `KNOWLEDGE_SOURCE`.
- **Deviations:**
  - The line filter and the empty sources for the fixed lines were added to the spec
    (`ai-assist`). A prompt alone still gave "chciałbym" in 2 of 6 guides.
  - The "say it for me" result will be editable on screen, because the model still writes
    "byłbyś" now and then (frontend spec updated).
- **Manual check (real Groq):**
  - 10 guides (2 per topic) gave 30 lines, of which 29 were kept. The dropped one held
    "chciałbym".
  - Three "say it for me" messages read naturally. One used "byłbyś" for the partner.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1600 passed).

## Fix found on the way: 116 123 hours and link

- **Problem:** the help data said 116 123 works "codziennie, 14:00-22:00" and linked to
  `https://116123.pl/`, which is a parked domain for sale (checked 2026-10-04). The line moved to
  the state platform 116sos.pl and works around the clock with a chat (116sos.pl, the line's page
  at psychologia.edu.pl, and the Ministry of Health page "Gdzie uzyskać pomoc psychologiczną i
  psychiatryczną?").
- **Changed:** hours "całą dobę", link `https://116sos.pl/`, and the description now names the
  chat. The help data and the five contract examples that repeat it were updated; one test was
  added.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1601 passed), the
  browser tests for summary and help (23 passed).
