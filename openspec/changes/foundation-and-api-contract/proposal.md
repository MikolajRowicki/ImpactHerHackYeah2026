# Proposal

## Why

MaydayMama has about 14 hours until the 2026-10-04 11:00 deadline and two builders working in parallel: a backend session and a separate frontend session. Without a shared, written contract and a clean repo layout they will block each other or overwrite each other's work. This change lays the ground so both can start at once on their own branches.

## What Changes

- Repo skeleton: all code under `src/` (`src/backend` Django + django-ninja, `src/frontend` plain HTML/CSS/JS), Poetry, ruff, pytest, `.env.example`, short README.
- General API contract v0 in `contracts/openapi.yaml` (outside `src/`), with example payloads in `contracts/examples/`. It fixes conventions, roles, permissions and the list of resources. It carries no business logic.
- Backend serves one live endpoint, `GET /api/v1/health`, and tests that guard the contract (valid document, valid examples, no undeclared routes).
- AI provider switch driven by `.env` (`AI_PROVIDER=mock|groq`), with the mock provider only. All keys live in `.env`.
- Frontend shell with a mock mode that serves the contract examples, so the frontend session works without any backend. Mock mode is clearly marked on screen.
- Docs: architecture with Mermaid (components, planned data model), worklog kept per session, and a self-contained brief for the frontend session. That session runs on another laptop and another account, so the git repository is the only channel: the brief covers setup from a clean clone, ownership, rules, and how to request a contract change by adding a file.
- `CLAUDE.md`: the worklog rule changes from one `docs/worklog.md` to one file per session in `docs/worklog/`, so parallel sessions never edit the same file.

**Non-goals** (each is its own later change): groups and roles logic, check-ins and observations, trend engine and summaries, tasks and self-care, the real Groq adapter, help path and crisis handling, the visual design of real screens, the pitch slides.

## Capabilities

### New Capabilities
- `api-contract`: the published API contract, its conventions, role permissions and the guarantees that keep code and contract in sync.
- `frontend-mock-mode`: the frontend runs against the contract examples without a backend and says so on screen.
- `ai-provider-config`: AI provider and secrets come from the environment; mock by default; bad configuration fails at startup.

### Modified Capabilities

None.

## Impact

- New directories `src/`, `contracts/`, `docs/` content, `pyproject.toml`, `poetry.lock`, `.env.example`.
- New dependencies, pinned: django, django-ninja. Dev group: ruff, pytest, pytest-django, playwright, pytest-playwright, openapi-spec-validator, jsonschema.
- `openspec/config.yaml` context corrected: deadline is 2026-10-04 11:00 AM, project name added.

## Assumptions to confirm at review

- `contracts/` sits at the repo root, outside `src/` (confirmed by the user).
- The contract is hand-written and is the source of truth; the code follows it. django-ninja is the implementation, not the author of the contract.
- One origin: Django serves `src/frontend` as static files, so session cookies work and CORS is not needed.
- The frontend session cannot talk to the backend session. Contract changes travel as files in `contracts/requests/` (unique file names, so no merge conflicts), pushed on the frontend branch and applied by the main session when it merges. The user relays anything urgent.
- The frontend session starts from the foundation branch as soon as its contract, shell and brief are pushed (before this change is archived), then merges `main` once the foundation is merged. Its files do not overlap with the foundation's remaining work.
- Roles are per group membership (`woman`, `partner`, `supporter`), not per account.
- Reminders reach people by e-mail (console backend in the demo) and in-app only. No push.
- The Groq adapter and its client library arrive in the AI change; until then `AI_PROVIDER=groq` is rejected at startup.
- Polish UI strings live in one frontend strings file, never inside logic.
- "The woman invites any role" is read as: she invites a partner or a supporter. A group has exactly one woman, so `x-invite-rules` does not let her invite another woman. The spec scenario "Only the woman invites outsiders" says so too.
- Examples with a variant (`get_me.200.partner.json`) let the frontend show other roles in mock mode; the plain `<operationId>.<status>.json` is the default.
- A person without a group who calls a group operation gets 403 `not_a_member`; only `get_group` answers 404 `no_group`.
