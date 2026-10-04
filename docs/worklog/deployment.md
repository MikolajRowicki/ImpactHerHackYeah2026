# Worklog: deployment

Branch `chore/deployment`. Outside OpenSpec: tooling and configuration only, no new behaviour.

## Group 1: gunicorn and https behind a proxy

- **Goal:** the app can run behind a reverse proxy that terminates https.
- **Built:** `gunicorn==23.0.0` (pyproject and lock); in `settings.py`, an https `APP_BASE_URL`
  sets `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS` and secure session and CSRF cookies.
  Two tests in `tests/test_settings.py`.
- **Deviations:** no new environment variable; the public scheme comes from `APP_BASE_URL`, so
  local http runs and the browser suite keep plain cookies. No whitenoise: the frontend is already
  served by `config.urls`.
- **Verification:** `ruff check .`, `ruff format --check .`, fast suite: 1523 passed, 4 failed.
  The same 4 fail on a clean `main`: contract examples are read with the Windows default encoding
  (cp1250), not UTF-8. Not related to this work.
- **Commit:** `f4b055b`

## Group 2: Docker image, compose, Caddy

- **Goal:** one command starts the app and https on a VM.
- **Built:** `Dockerfile`, `deploy/entrypoint.sh` (migrate, then gunicorn), `deploy/Caddyfile`,
  `docker-compose.yml`, `.dockerignore`, `.gitattributes` (LF for shell scripts),
  `docs/operations.md`.
- **Deviations:** first run failed with "unable to open database file": `.env` carried an empty
  `DATABASE_PATH=` that overrode the image. Compose now sets it under `environment`, which wins
  over `env_file`. Commit `1d4c462`.
- **Verification (on the VM, Compute Engine, Debian 13, static IP, DNS at home.pl):**
  `docker compose up -d --build`; migrations applied; `https://maydaymama.pl/` answers 200 with a
  valid certificate; `www` and plain http redirect to `https://maydaymama.pl/`; the `csrftoken`
  cookie is `Secure`; a POST without a CSRF token gets 403 `csrf_failed`.
- **Not done:** the browser suite (no template, CSS or view changed), an independent review, a
  real sign-up with the e-mail link over smtp, the daily `send_reminders` cron and the backup job.
- **Commits:** `fe8f345`, `1d4c462`

## Group 3: the page at `/` (branch `fix/root-page`)

- **Goal:** `https://maydaymama.pl/` shows the page at that address instead of redirecting to
  `/static/index.html`.
- **Built:** `config/urls.py` serves `index.html` at `/` (with the CSRF cookie) and the frontend's
  own `css/`, `js/`, `fonts/`, two icons and `contracts/` from the root, because the page links to
  them with relative paths. `/static/...` keeps working. Only those names are reachable from the
  root; tests check that `pyproject.toml`, `.env` and the source tree are not.
- **Deviations:** `<base href="/static/">` was rejected: it would break the `#/` links. The
  `sign_in` helper of `test_live_ai.py` now reloads after the API login, because `/` and
  `/#/say-it` are one document and a hash change no longer reloads it.
- **Verification:** ruff, fast suite (4 known failures, see Group 1), browser suite
  (235 passed after the test fix); the new tests fail against the old `urls.py` (9 failures);
  the real app run locally on a throwaway database, screenshot checked, no failed asset requests,
  mock mode and `/static/index.html` still work.
- **Not done:** an independent review; cache headers for static files (decided to wait).
