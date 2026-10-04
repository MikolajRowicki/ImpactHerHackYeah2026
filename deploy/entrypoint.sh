#!/bin/sh
set -e

cd /app/src/backend
python manage.py migrate --noinput

# SQLite takes one writer at a time, so a few threads are enough.
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --access-logfile -
