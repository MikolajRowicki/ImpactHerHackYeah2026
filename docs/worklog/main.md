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

## Change ai-assist-and-sources, group 2: curated knowledge source

- **Goal:** the conversation guide cites real Polish sources (light retrieval, no embeddings).
- **Built:**
  - `core/content/knowledge.json` has 13 short passages from 9 public pages: pacjent.gov.pl (two
    articles), mp.pl, Fundacja Rodzić po Ludzku, the sanitary station's page on gov.pl, the
    Ministry of Health, Fundacja Nie Widać Po Mnie, 116sos.pl and Centrum Wsparcia. Each page was
    read during this task, and every passage is a summary in our own words.
  - `CuratedKnowledge` folds the query. A topic tag scores 3 and a keyword prefix scores 1. It
    returns the best three passages from different pages, with ties in file order.
  - `KNOWLEDGE_SOURCE` defaults to `curated`, and a bad value or file stops startup.
  - `assist.generate` asks the knowledge source only when a feature passes a `query`, and only
    the guide does (`"<topic> <brief>"`). The guide prompt treats the passages as background
    without numbers or institution names.
  - New example `ai_conversation_guide.200.sources.json`. README and architecture describe the
    source.
- **Deviations:**
  - "At most one passage per page" was added to the spec, so the cited links are different pages.
  - The pacjent.gov.pl article on supporting a person with depression is linked as
    `https://pacjent.gov.pl/node/2609`. Its slug address is refused by the site's firewall even in
    headless Chromium, while the node address opens the article.
  - Tests changed on purpose: the default knowledge source is `curated`; the guide lists its
    curated sources by default; "say it for me" no longer lists passages.
- **Manual checks:**
  - Headless Chromium opened all 9 links with the expected titles.
  - With real Groq and the curated source, the guide answered in 0.3–0.4 s for three topics, with
    lines drawn from the passages ("zająć się dzieckiem", "w czym konkretnie mogę pomóc") and
    three sources each.
- **Not done:** the passages need a specialist's read before real use.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (1626 passed),
  `openspec validate --strict`.

## Change ai-assist-and-sources, group 3: "Powiedz to za mnie" screen

- **Goal:** the mother can turn something hard into a calm message she can edit and copy.
- **Built:**
  - `#/say-it` for the mother of an active or closed group. It has the text with a 500-character
    counter, the recipient and the tone. The suggestion comes in an editable field with "Kopiuj"
    and "Inna propozycja". A crisis answer shows the crisis lines and a link to help instead of a
    message. A failure keeps her text and offers "Spróbuj ponownie". The button says
    "Przygotowuję…" while waiting.
  - A quiet card on her start screen. The navigation is unchanged.
  - `ui/ai.js`: the origin label ("Przygotowane z pomocą AI", "Tekst przykładowy", none for fixed
    texts) and the sources list used by the guide.
  - `api.js` sends a `query` as a query string. Both AI operations are in `operations.js`.
  - Mock mode: `js/mock-ai.js` with sample messages, a short crisis list and sample guides.
    Mock-store handlers mirror the roles, the validation and the crisis answer. Her text is not
    kept.
  - `whileBusy` can show a label while it waits. `ctaCard` has a quiet variant.
- **Deviations:**
  - The guide's mock handler, strings and sources list landed here as shared plumbing. Group 4
    adds the screen.
  - The "not for you" text for loved ones' places now says "To miejsce jest dla bliskich osób
    mamy" instead of "Te pytania…", because the guide uses it too.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests`, `pytest tests_e2e`
  (212 passed, 16 of them new for this screen). Screenshots in mock mode at 390 px and 1280 px
  were checked by eye.

## Change ai-assist-and-sources, group 4: conversation guide with sources

- **Goal:** a partner or supporter prepares a caring conversation and sees the sources behind
  the text.
- **Built:**
  - `#/talk` (topic list and a hint) and `#/talk/<topic>` for partners and supporters of an
    active or closed group. The current topic is marked with `aria-current`. The guide has three
    parts ("Od czego zacząć", "Czego unikać", "O co dopytać"), "Inne propozycje zdań", the origin
    label, a "Źródła" list (title, site name, new tab, https only) and a short note.
  - A quiet card on the loved ones' start screen. When the trend needs attention, their summary
    also links to the professional-help topic. The mother's summary has no such link.
  - Help and guide links in the summary now sit on their own lines.
- **Deviations:** none from the spec. An unknown topic shows the list with a hint and sends no
  request.
- **Verification:**
  - `ruff check .`, `ruff format --check .`, `pytest tests` (1626 passed), `pytest tests_e2e`
    (233 passed, 21 new). Two of the new tests run against the seeded backend: Marta sees three
    curated sources for "Po trudnym dniu", and Anna gets a message and the crisis answer with
    116 123 "całą dobę".
  - Screenshots in mock mode at 390 px and 1280 px were checked by eye.

## Change ai-assist-and-sources: live check (task 5.1)

- **Setup:**
  - The real app with `AI_PROVIDER=groq`, `KNOWLEDGE_SOURCE=curated` and e-mail to the console.
  - A fresh demo database in the scratch folder. `db.sqlite3` was not touched.
- **Anna:**
  - "Powiedz to za mnie" answered in 0.4 s, labelled "Przygotowane z pomocą AI".
  - The Groq narrative showed on her summary.
- **Marta:** the professional-help guide showed three Groq lines and three sources (mp.pl,
  gov.pl, pacjent.gov.pl). Screenshots were taken at 390 px and 1280 px.
- **Found and fixed during the check:**
  - A line with "żebym pomógł" passed the gender filter (`9c14a97`).
  - The origin label shared a line with the field label (`a2b83f7`).
  - The counter overlapped the text box, and the message box was too short on a phone
    (`a2b83f7`).
- **Own mutation checks:** 8 behaviours were broken on purpose in a throwaway worktree, and each
  was caught by its test.

## Change ai-assist-and-sources: review round 1 (independent reviewer): FAIL, fixed

- **M1:** a slow, older answer (a pending "Inna propozycja") could replace a newer crisis answer.
  - Only the latest request's answer is shown now. A counter grows when a request really leaves.
  - A test holds the older request and releases it after the crisis answer.
  - The first attempt counted a blocked second press too; the double-press test caught that.
- **M2:** the main spec's "Guide for a topic" still said `sources` is empty.
  - The delta now MODIFIES "Conversation guide".
  - The ai-assist Purpose in the main spec was updated.
- **L1:** ranking by a sum (+3 per topic, +1 per keyword) did not guarantee topic first.
  - Passages are now ranked by topic hits, then keyword hits.
  - A new test has a keyword-heavy passage without a tag.
- **L2:** the gender filter missed some forms.
  - It now also catches the split conditional up to four words apart, the compound future
    ("będę pomagał"), adjectives after "jestem" and "sam nie wiem".
  - Nouns that only look like past forms ("z pomysłem", "nie łam się") are ignored.
  - Spec scenarios were added.
- **L3:** "zrobiłaś" and "byłaś" are now in the test of lines that stay.
- **L4:** a Groq narrative on the summary is now labelled "Przygotowane z pomocą AI" (spec
  scenario added).
- **L5:** after a failure, focus goes to "Spróbuj ponownie" or "Inne propozycje zdań".
- **L6:** the privacy note says the text is not stored and goes only to the AI service.
- **L7:** without a key, the mock provider gives the helpers sample texts that fit their screens.
- **L8:** these worklog entries.
- **Verification:**
  - The new tests fail on the code before the fixes (checked in a throwaway worktree).
  - `ruff check .`, `ruff format --check .`, `pytest tests` (1646 passed).
  - At the user's request, only the browser tests of the touched screens ran: say it for me,
    guide, summary, live AI, contrast and layout (59 passed). The full browser suite last ran
    before these fixes (233 passed).
