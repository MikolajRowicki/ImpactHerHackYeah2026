# Operations

## Production layout

One Compute Engine VM runs two containers from `docker-compose.yml`:

- `app`: gunicorn with the Django app. `migrate` runs on every start. The SQLite file is
  `/data/db.sqlite3` on the `db` volume.
- `caddy`: terminates HTTPS for `maydaymama.pl` (certificate from Let's Encrypt, renewed by Caddy)
  and proxies to `app:8000`. `www.maydaymama.pl` redirects to the bare domain.

The code lives in a git clone on the VM. An update is `git pull` and a rebuild.

## Production `.env` (on the VM, never in git)

| Name | Value |
|---|---|
| `DJANGO_DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | long random string |
| `DJANGO_ALLOWED_HOSTS` | `maydaymama.pl,www.maydaymama.pl` |
| `APP_BASE_URL` | `https://maydaymama.pl/` (https here turns on secure cookies and proxy trust) |
| `AI_PROVIDER` | `groq`, with `GROQ_API_KEY` |
| `EMAIL_MODE` | `smtp`, with `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_FROM` |

`DATABASE_PATH` is set by the image; leave it out.

## Update

```sh
cd ~/ImpactHerHackYeah2026
git pull
docker compose up -d --build
```

## Reminders

`send_reminders` is a command, not a daemon. Run it once a day from the VM's cron:

```sh
docker compose exec -T app python src/backend/manage.py send_reminders
```

## Backup

```sh
docker compose exec -T app python -c "import sqlite3; s=sqlite3.connect('/data/db.sqlite3'); d=sqlite3.connect('/data/backup.sqlite3'); s.backup(d)"
docker compose cp app:/data/backup.sqlite3 ./backup-$(date +%F).sqlite3
```

Use SQLite's online backup, not `cp` of the live file.
