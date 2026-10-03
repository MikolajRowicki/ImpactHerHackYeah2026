# Tasks

Branch: `change/foundation-and-api-contract`. One group is one commit. Run `ruff check .`, `ruff format --check .` and the fast tests before each commit.

## 1. Backend skeleton and tooling

- [ ] 1.1 Create `pyproject.toml` (Python 3.12+, package-mode off) with pinned django and django-ninja, dev group with ruff, pytest, pytest-django, jsonschema, openapi-spec-validator; commit `poetry.lock`. Verify `poetry install` succeeds on a clean environment.
- [ ] 1.2 Configure ruff and pytest in `pyproject.toml`. Verify `ruff check .` and `ruff format --check .` pass.
- [ ] 1.3 Create the Django project `src/backend/config` and app `src/backend/core`, with settings read from the environment (secret key, debug, allowed hosts, database path), static files served from `src/frontend`, and a startup failure when the secret key is missing and debug is off. Verify a test starts the settings in both modes (spec: Missing secret key in production mode).
- [ ] 1.4 Add `GET /api/v1/health` with django-ninja. Verify a test gets 200 and the documented body (spec: Service is up).
- [ ] 1.5 Add `.env.example` listing every variable and extend `.gitignore` if needed. Verify a test compares settings variables with `.env.example` (spec: Example file is complete).

## 2. AI provider switch

- [ ] 2.1 Add the provider interface and the deterministic mock provider that labels its output as mock. Verify tests for repeated calls and for the label (specs: Repeated call, Mock is labelled).
- [ ] 2.2 Choose the provider from `AI_PROVIDER` (default `mock`) and fail startup on an unknown value with the list of available ones. Verify tests for default, explicit mock and unknown value (specs: Default provider, Explicit mock, Unknown value).

## 3. API contract v0

- [ ] 3.1 Write `contracts/openapi.yaml` with conventions, the common error shape, security, roles per operation and all v0 resources from design.md. Verify the document passes `openapi-spec-validator`.
- [ ] 3.2 Write `contracts/examples/` with a success example and the relevant error examples (401, 403, 404, 422) for every operation. Verify a test validates every example against its schema and that every operation has examples (specs: Examples match their schemas, Every operation has an example).
- [ ] 3.3 Add the guard tests: all resources present, error shape, privacy rules (no free text, no author in summary, check-ins only for the woman), permission rules (invitation, close, remove), and implemented routes are declared. Verify the tests pass and fail when a route is added without a contract entry (check once by hand).
- [ ] 3.4 Write `contracts/README.md` (how to read it, how to request a change, naming of example files). Verify its example file names match the files in the folder.

## 4. Frontend shell with mock mode

- [ ] 4.1 Create `src/frontend/index.html`, base CSS with design tokens, `js/app.js` with a hash router, `js/strings.pl.js` and one placeholder screen that shows the current user. Verify the page opens from a static server.
- [ ] 4.2 Add the API client with live and mock adapters, the `?mock=1` and `?mock=0` switch kept in `sessionStorage`, the CSRF header on unsafe live calls, and the sample-data banner. Verify with Playwright: banner visible in mock mode, absent otherwise, no request to `/api/v1` in mock mode (specs: Mock call, Mock mode is remembered, Notice on every screen, No notice in live mode).
- [ ] 4.3 Add Playwright setup (fixtures, artifacts in a git-ignored directory) and a smoke test for the page at 375 px and 1280 px width without horizontal scroll (specs: Static serving, Phone width). Verify `pytest tests_e2e` passes headless.
- [ ] 4.4 Verify the live adapter against the running Django app: the health call succeeds and the page served by Django loads its static files. Check by hand and with a Playwright test.

## 5. Documentation and frontend brief

- [ ] 5.1 Rewrite `README.md` for a clean clone: install, `.env`, run, tests, mock mode. Verify each command by running it from a fresh clone.
- [ ] 5.2 Write `docs/architecture.md`: component diagram, request flow, planned data model as a Mermaid ER diagram, role and permission table. Keep it short. Verify the Mermaid blocks render (checked in a Mermaid viewer or `mmdc`).
- [ ] 5.3 Write `docs/frontend-brief.md` for the separate frontend session: worktree commands, branch name, owned paths, rules from `CLAUDE.md` that apply, mock mode, how to ask for a contract change, product rules (nothing behind her back, no words "krąg" or "wioska" in the UI, Polish UI strings). Verify a fresh reader can start from it: run its commands in a new worktree.
- [ ] 5.4 Add the first entries to `docs/worklog.md` for groups 1 to 5 with commit hashes. Verify every group has goal, result, deviations and verification.

## 6. Integration check

- [ ] 6.1 Run the full check on a fresh clone of the branch: poetry install, ruff, fast tests, browser tests, `openspec validate foundation-and-api-contract`. Verify all pass.
- [ ] 6.2 Independent review by a fresh reviewer against the specs: every scenario mapped to a test, defects hunted with concrete failing cases, ending in PASS or FAIL. Fix findings and review again until PASS.
