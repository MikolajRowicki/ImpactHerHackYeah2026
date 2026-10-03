# MaydayMama

Entry for HackYeah 2026, ImpactHer: Technology for Real Change.

MaydayMama helps new mothers and their close ones notice postpartum depression early and share the
load. It never diagnoses and never replaces a doctor or crisis help. The interface is in Polish.

Status: the backend answers every operation of the API contract (`contracts/`): accounts and
e-mail activation, groups and invitations, check-ins, observations, an explainable trend and
summary, tasks, help paths, reminders and two optional AI helpers. The frontend shell still runs on
sample data; the real screens are built separately.

## Requirements

- Python 3.12 or newer
- [Poetry](https://python-poetry.org/) 2

## Install

```bash
poetry install
cp .env.example .env
```

`.env` is local and ignored by git. For local work the defaults are enough (`DJANGO_DEBUG=1`).
With `DJANGO_DEBUG=0` the app refuses to start until `DJANGO_SECRET_KEY` is set. Every variable
is explained in `.env.example`.

## Run

```bash
poetry run python src/backend/manage.py migrate
poetry run python src/backend/manage.py runserver
```

`migrate` creates the SQLite database file (`db.sqlite3`, or the path in `DATABASE_PATH`).
Open <http://localhost:8000/>. Django serves the frontend from `src/frontend`, the contract
examples from `contracts/`, and the API under `/api/v1`. Check it:

```bash
curl http://localhost:8000/api/v1/health
```

## Demo data

```bash
poetry run python src/backend/manage.py seed_demo
```

Creates Anna (the woman), Piotr (partner) and Marta (supporter) with the password `demo-haslo-1`,
one active group, two weeks of check-ins and observations, tasks in every status and one open
invitation (`#/invite/demo-invite-1`). Anna's summary shows `needs_attention`. The command prints
the database file it works on, replaces only these three accounts when run again, and refuses to
run with `DJANGO_DEBUG=0` unless you add `--allow-production`. Then sign in at
<http://localhost:8000/> or call the API:

```bash
curl -s -c jar http://localhost:8000/ -o /dev/null            # sets the csrftoken cookie
TOKEN=$(awk '/csrftoken/ {print $7}' jar)
curl -s -b jar -c jar -H "X-CSRFToken: $TOKEN" -H 'Content-Type: application/json' \
  -d '{"email":"anna@example.com","password":"demo-haslo-1"}' http://localhost:8000/api/v1/auth/login
curl -s -b jar http://localhost:8000/api/v1/summary
```

## Reminders

```bash
poetry run python src/backend/manage.py send_reminders
```

Sends at most one e-mail per person and kind each day (a check-in, an observation, a task in
progress), to people with e-mail reminders on and an active group. Run it again the same day and
nothing new is sent. Start it by hand or from cron, for example `0 18 * * *`. There is no
background worker.

## E-mail

By default mail is printed to the terminal (`EMAIL_MODE=console`). To send real mail, for example
through Gmail, create an app password for your Google account (it needs 2-step verification) and
set in `.env`:

```
EMAIL_MODE=smtp
EMAIL_USER=your.address@gmail.com
EMAIL_PASS=the-16-character-app-password
APP_BASE_URL=http://localhost:8000/
```

`EMAIL_MODE=smtp` without `EMAIL_USER` or `EMAIL_PASS` stops startup. Links in messages start with
`APP_BASE_URL`. Limits: 1 message per 60 seconds and 3 per hour per address and kind, 200 per day
for the whole mailbox. A mail failure never breaks a request. Sign-up by e-mail
(`/api/v1/auth/signup`) needs this; the older `register` creates an active account at once and
works only while `DJANGO_DEBUG=1` unless `ALLOW_LEGACY_REGISTER=1`.

## AI provider (mock or Groq)

`AI_PROVIDER=mock` (default) is offline and every text it produces is labelled `mock`. To use
Groq, set `AI_PROVIDER=groq` and `GROQ_API_KEY` (a free key from the Groq console; `GROQ_MODEL`
is optional). A missing key stops startup. A slow or failing provider (limit 8 seconds) never
breaks a request: the answer falls back to a fixed text labelled `rules`. Text that "say it for
me" sends to the provider is never stored or logged here.

## Frontend without a backend (mock mode)

Mock mode answers every API call from the files in `contracts/examples/` and sends nothing to the
backend. A banner on every screen says the data is sample data.

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/src/frontend/index.html?mock=1>. Django serves the same page at
<http://localhost:8000/static/index.html?mock=1>.

- `?mock=1` turns mock mode on and `?mock=0` turns it off. The choice stays for the browser tab.
- `?variant=partner` shows another example (`get_me.200.partner.json`). Available variants are
  listed in [contracts/README.md](contracts/README.md). `?variant=` clears it.

## Tests and checks

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest                       # fast tests
poetry run playwright install chromium  # once
poetry run pytest tests_e2e             # browser tests, headless
```

Watch a browser run: `poetry run pytest tests_e2e --headed --slowmo 300`. After a failure, replay
the trace with `poetry run playwright show-trace test-results/<test>/trace.zip`. Artifacts go to
`test-results/`, which git ignores.

## Layout

| Path | Content |
|---|---|
| `src/backend/` | Django project (`config/`) and app (`core/`), API built with django-ninja |
| `src/frontend/` | plain HTML, CSS and JavaScript, no build step |
| `contracts/` | the API contract and its examples; see [contracts/README.md](contracts/README.md) |
| `tests/`, `tests_e2e/` | fast tests, browser tests |
| `docs/` | [architecture](docs/architecture.md), [frontend brief](docs/frontend-brief.md), worklog |
| `openspec/` | specs and changes (spec-driven workflow) |
| `CLAUDE.md` | working agreements for this repository |
