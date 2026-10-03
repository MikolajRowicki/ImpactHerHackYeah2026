# MaydayMama

Entry for HackYeah 2026, ImpactHer: Technology for Real Change.

MaydayMama helps new mothers and their close ones notice postpartum depression early and share the
load. It never diagnoses and never replaces a doctor or crisis help. The interface is in Polish.

Status: foundation only. The repository holds the backend skeleton, the API contract
(`contracts/`) and a frontend shell that runs on sample data. Features come in later changes.

## Requirements

- Python 3.12 or newer
- [Poetry](https://python-poetry.org/) 2

## Install

```bash
poetry install
cp .env.example .env
```

`.env` is local and ignored by git. For local work the defaults are enough (`DJANGO_DEBUG=1`).
With `DJANGO_DEBUG=0` the app refuses to start until `DJANGO_SECRET_KEY` is set.

## Run

```bash
poetry run python src/backend/manage.py migrate
poetry run python src/backend/manage.py runserver
```

Open <http://localhost:8000/>. Django serves the frontend from `src/frontend`, the contract
examples from `contracts/`, and the API under `/api/v1`. Check it:

```bash
curl http://localhost:8000/api/v1/health
```

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
