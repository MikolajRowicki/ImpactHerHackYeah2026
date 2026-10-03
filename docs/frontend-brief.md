# Frontend brief

Read this whole file first. It is written for the frontend session, which runs on another laptop
and another account than the backend session. The git repository and the user are the only
channels between the two sessions, so everything you need is here or in the repository.

Deadline of the whole project: 2026-10-04, 11:00 (morning).

## 1. What MaydayMama is

A Polish-language web app that helps new mothers and their close ones notice postpartum depression
early and share the load. It never diagnoses and never replaces a doctor or crisis help.

- The woman records how she feels (check-in), sees a gentle summary, gets small self-care
  suggestions, and sees the care tasks of her group.
- Her partner and other close ones (supporters) answer short, closed questions about her daily
  life (observations) and share care tasks.
- A plain, explainable trend engine turns the answers into a general summary. Nobody ever sees a
  single answer or who gave it.

Design and usability together are 40% of the judging score, so the interface has to look great
and feel calm on a phone and on a laptop.

## 2. Set up from a clean clone

You need git, Python 3.12 or newer, Poetry 2, Node.js with npm (for the OpenSpec CLI) and Chromium
for the browser tests.

```bash
git clone https://github.com/MikolajRowicki/ImpactHerHackYeah2026.git
cd ImpactHerHackYeah2026
git checkout change/foundation-and-api-contract
git checkout -b change/frontend-app          # or the branch name the user gives you
poetry install
cp .env.example .env
npm install -g @fission-ai/openspec@1.14.0   # the spec workflow, see CLAUDE.md
poetry run playwright install chromium
```

The `frontend-design` plugin is enabled in `.claude/settings.json`. If it is not available in your
session, install it with `/plugin install frontend-design@claude-plugins-official`. Use it for
every visual decision.

Check that everything works:

```bash
poetry run ruff check . && poetry run ruff format --check .
poetry run pytest
poetry run pytest tests_e2e
```

Then look at the shell in mock mode:

```bash
python3 -m http.server 8000
# open http://localhost:8000/src/frontend/index.html?mock=1
```

## 3. Branches

- Start from `change/foundation-and-api-contract`. It is not merged into `main` yet.
- While it is open, get its newer commits with `git fetch && git merge origin/change/foundation-and-api-contract`.
  Once it is merged into `main`, merge `main` instead, after every contract change announced by the user.
- Your own work lives on your branch (`change/frontend-app` unless told otherwise). Push it often:
  `git push -u origin change/frontend-app`.
- Never push to `main`, never force-push, never rewrite history.

## 3a. Messages from the backend

At the start of every session, read the files in `docs/from-be-to-fe/` (see its README), handle
them, and delete each one in the commit that handles it.

## 4. Who owns what

| Path | Owner | You |
|---|---|---|
| `src/frontend/` | you | edit freely |
| `tests_e2e/` | you from now on | edit; the shell tests there check the placeholder screen, so update them when you replace it |
| `openspec/changes/<your change>/` | you | edit |
| `docs/worklog/frontend.md` | you | create and edit |
| `docs/from-be-to-fe/` | backend session writes | read, then delete the messages you handled |
| `contracts/requests/` | you add new files | add; never edit or delete existing files |
| `src/backend/`, `tests/` | backend session | read only |
| `contracts/openapi.yaml`, `contracts/examples/`, `contracts/README.md` | main session | read only |
| `pyproject.toml`, `poetry.lock` | backend session | read only |
| `CLAUDE.md`, `README.md`, other files in `docs/`, `openspec/specs/`, `openspec/config.yaml` | main session | read only |

If you need a change in a read-only place, ask for it (section 7). If a read-only file is wrong,
say so in your worklog and in the final message to the user instead of editing it.

## 5. Rules from CLAUDE.md that apply to you

`CLAUDE.md` in the repository root is binding. Read it. The parts that matter most here:

- English in code, identifiers, comments, commit messages, branch names and documentation.
  Polish only for what the person sees, and that lives in `src/frontend/js/strings.pl.js`, never
  inside logic.
- Plain, short English. Comments say why, not what. No commented-out code.
- Never mention how the code was produced: no co-author trailers, no "generated with" lines, in
  any file or commit message.
- Spec-driven work: explore, propose, review, apply, archive. Create an OpenSpec change for your
  work only when the user orders it, and write down every assumption under "Assumptions to confirm
  at review". Specs describe behaviour with SHALL/MUST and WHEN/THEN scenarios.
- tasks.md groups tasks so that one group is one commit, each group with a verification step.
- Conventional Commits, small and self-contained, one per task group. Commit and push only after
  verification passes.
- Before every commit: `ruff check .`, `ruff format --check .`, `pytest`, and `pytest tests_e2e`
  because you change templates, CSS and scripts.
- Browser tests use user-facing locators (`get_by_role`, `get_by_label`, the real Polish texts),
  `expect(...)` auto-waiting and no fixed sleeps. A test must fail when what the person sees
  breaks. Artifacts go to `test-results/`, which git ignores.
- Independent review before calling something done: a fresh reviewer that did not write the code
  maps every spec scenario to a test and ends with PASS or FAIL. Look at the real running app and
  take screenshots at 375 px and 1280 px.
- Report outcomes honestly: failing tests with their output, skipped steps, known gaps.
- Write one entry per task group in `docs/worklog/frontend.md`: goal, what was built, deviations,
  verification, commit hashes.

## 6. How the frontend talks to the backend

The contract is `contracts/openapi.yaml`; `contracts/README.md` explains how to read it. Every
operation has an `operationId` such as `get_me`, the roles allowed to call it (`x-roles`), and the
responses it can give. Errors always look like `{"error": {"code", "message", "fields"?}}`.

The shell already has:

- `src/frontend/js/api.js`: `createApi({ mock, variant, base })` returns `{ mock, call }`.
  `await api.call("get_me")`, `await api.call("login", { body })`,
  `await api.call("claim_task", { params: { task_id: 5 } })`. A non-2xx answer throws `ApiError`
  with `status`, `code`, `message` and `fields`.
- `src/frontend/js/operations.js`: operationId, method, path and success status. A test in
  `tests/` compares it with the contract. When a merge brings new operations, add them here, or
  that test fails and tells you what is missing.
- `src/frontend/js/app.js`: a hash router (`#/path`) and the mock notice. Add screens under
  `js/screens/` and routes in `routes`.
- `src/frontend/css/tokens.css`: design tokens as custom properties. Change them and add more.
- `src/frontend/js/strings.pl.js`: all Polish strings.

### Mock mode

Mock mode answers every call from `contracts/examples/` and sends nothing to `/api/v1`. It is how
you work without a backend.

- `?mock=1` turns it on, `?mock=0` turns it off. The choice stays for the browser tab.
- `?variant=partner` (or `supporter`, `no_group`, `pending`) picks another example for the same
  call, for example `get_me.200.partner.json`. `?variant=` clears it.
- `api.call("create_task", { status: 409 })` returns the 409 example as an `ApiError`, so you can
  build error states.
- A notice that says the data is sample data is shown on every screen while mock mode is on.
  Keep it.
- Mutations only return their example. Keep any in-memory state you need inside the frontend, and
  mark it as mock data.

Standalone: `python3 -m http.server 8000` in the repository root, then open
`http://localhost:8000/src/frontend/index.html?mock=1`. With Django:
`poetry run python src/backend/manage.py runserver`, then open `http://localhost:8000/`.

### Live mode

Without `?mock=1` the same code calls `/api/v1` on its own origin. The session cookie travels
with every call and unsafe calls carry the `X-CSRFToken` header; `api.js` does both. The backend
session builds the operations one by one, so most of them answer 404 until they are done. Build
against mock mode first.

## 7. Asking for a contract change

You cannot reach the backend session, and you must not edit `contracts/openapi.yaml` or
`contracts/examples/`. If you need another field, operation or example:

1. Add `contracts/requests/<yyyymmdd>-<short-slug>.md`, for example
   `contracts/requests/20261003-task-due-date.md`. Say what you need, why, and the shape you
   propose.
2. Keep going with your own mock data and mark it as such in the request and in the code.
3. Push your branch and tell the user in your message that a request is waiting. The user relays
   anything urgent.
4. The main session applies the request on `main` and deletes the file in the same commit. When
   the user tells you, merge `main`.

## 8. Product rules

These come from the product decisions. They are not up for change on the frontend.

- **Nothing behind her back.** She knows observations exist. She sees only the general picture and
  the summary, in gentle, general wording, never an individual answer and never who said what.
  Loved ones have a separate coordination space; she knows it exists but does not have to read it.
- **The woman owns the group.** A partner may create it and invite her, but it stays empty (no
  data, nobody else added) until she accepts; show that waiting state. If she creates it, she
  invites her partner. Only she invites outsiders (family, friends), removes people and closes the
  group.
- **No "krąg" and no "wioska" anywhere in the UI.** They are internal working words.
- **No diagnoses, no judging.** No scores, no 1 to 5 ratings, no grading of her or of her helpers.
  Wording is care, not evaluation. Loved ones get a reminder to take special care of her.
- **Closed answers only.** Observations are short questions with ready-made answers and no free
  text about her.
- **Polish UI**, one strings file. The app is called MaydayMama.
- **Help path and crisis help** arrive in a later change, and the contract will get their fields
  then. Leave a visible, calm place for them in the layout, and do not invent phone numbers or
  medical advice.
- **Phone first, laptop great.** No PWA, no framework, no build step: plain HTML, CSS and ES
  modules. No horizontal scrolling at 375 px.
- Accessible by default: real headings and landmarks, visible focus, sufficient contrast, labels
  on every field.

## 9. Handing back

1. Everything committed on your branch, checks green, `docs/worklog/frontend.md` up to date.
2. `git push -u origin <your branch>`.
3. Tell the user: the branch name, what is done, what is not, which contract requests are waiting,
   and which screens were only checked in mock mode.

The main session merges your branch (it archives your OpenSpec change first, as `CLAUDE.md`
requires). Do not merge it into `main` yourself.
