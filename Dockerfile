FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir poetry==2.5.1

WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

COPY src ./src
COPY contracts ./contracts
COPY deploy/entrypoint.sh /entrypoint.sh

# The database lives on a volume mounted at /data.
RUN useradd --system --create-home app \
    && mkdir /data \
    && chown app:app /data \
    && chmod +x /entrypoint.sh
USER app

ENV DATABASE_PATH=/data/db.sqlite3
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
